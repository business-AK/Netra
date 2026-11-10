import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Tuple
from app.config import settings

class VideoVectorStore:
    def __init__(self, video_id: str):
        self.video_id = video_id
        self.index_dir = os.path.join(settings.STORAGE_DIR, "indexes")
        os.makedirs(self.index_dir, exist_ok=True)

        self.visual_index_path = os.path.join(self.index_dir, f"{video_id}_visual.index")
        self.visual_meta_path = os.path.join(self.index_dir, f"{video_id}_visual_meta.json")

        self.text_index_path = os.path.join(self.index_dir, f"{video_id}_text.index")
        self.text_meta_path = os.path.join(self.index_dir, f"{video_id}_text_meta.json")

    def build_visual_index(self, embeddings: np.ndarray, metadata_list: List[Dict[str, Any]]) -> None:
        """
        Creates and saves a FAISS IndexFlatIP index for visual frame embeddings.
        """
        if embeddings.shape[0] == 0:
            return

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        faiss.write_index(index, self.visual_index_path)
        with open(self.visual_meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, indent=2)

    def build_text_index(self, embeddings: np.ndarray, metadata_list: List[Dict[str, Any]]) -> None:
        """
        Creates and saves a FAISS IndexFlatIP index for transcript chunk embeddings.
        """
        if embeddings.shape[0] == 0:
            return

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        faiss.write_index(index, self.text_index_path)
        with open(self.text_meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, indent=2)

    def search_visual(self, query_vector: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Searches the visual index for top_k frames matching the query vector.
        """
        if not os.path.exists(self.visual_index_path) or not os.path.exists(self.visual_meta_path):
            return []

        index = faiss.read_index(self.visual_index_path)
        with open(self.visual_meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        actual_k = min(top_k, index.ntotal)
        if actual_k <= 0:
            return []

        scores, indices = index.search(query_vector, actual_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(metadata):
                item = dict(metadata[idx])
                item["similarity"] = round(float(score), 4)
                results.append(item)

        return results

    def search_text(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches the text index for top_k transcript segments matching the query vector.
        """
        if not os.path.exists(self.text_index_path) or not os.path.exists(self.text_meta_path):
            return []

        index = faiss.read_index(self.text_index_path)
        with open(self.text_meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        actual_k = min(top_k, index.ntotal)
        if actual_k <= 0:
            return []

        scores, indices = index.search(query_vector, actual_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(metadata):
                item = dict(metadata[idx])
                item["similarity"] = round(float(score), 4)
                results.append(item)

        return results

    def delete_indexes(self) -> None:
        """
        Cleans up index and metadata files when video is deleted.
        """
        for p in [self.visual_index_path, self.visual_meta_path, self.text_index_path, self.text_meta_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e:
                    print(f"Warning: could not delete {p}: {e}")

