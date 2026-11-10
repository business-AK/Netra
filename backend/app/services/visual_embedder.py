import torch
import open_clip
from PIL import Image
import numpy as np
from typing import List
from app.config import settings

class VisualEmbedder:
    _instance = None

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading CLIP visual model '{settings.VISUAL_MODEL}' ({settings.PRETRAINED_VISUAL}) on {self.device}...")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            settings.VISUAL_MODEL,
            pretrained=settings.PRETRAINED_VISUAL
        )
        self.model = self.model.to(self.device)
        self.model.eval()
        self.tokenizer = open_clip.get_tokenizer(settings.VISUAL_MODEL)
        self.dimension = 512

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VisualEmbedder()
        return cls._instance

    def embed_images(self, image_paths: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embeds a list of image paths into L2-normalized 512-dim vectors.
        """
        if not image_paths:
            return np.empty((0, self.dimension), dtype=np.float32)

        all_embeddings = []
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            tensors = []
            for path in batch_paths:
                try:
                    img = Image.open(path).convert("RGB")
                    tensors.append(self.preprocess(img))
                except Exception as e:
                    print(f"Warning: could not process image {path}: {e}")
                    # blank dummy image tensor
                    tensors.append(torch.zeros(3, 224, 224))

            batch_tensor = torch.stack(tensors).to(self.device)
            with torch.no_grad():
                features = self.model.encode_image(batch_tensor)
                features = features / features.norm(dim=-1, keepdim=True)
                all_embeddings.append(features.cpu().numpy().astype(np.float32))

        return np.vstack(all_embeddings)

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embeds a text query into L2-normalized 512-dim vector for visual semantic matching.
        """
        tokens = self.tokenizer([text]).to(self.device)
        with torch.no_grad():
            features = self.model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
            return features.cpu().numpy().astype(np.float32)

