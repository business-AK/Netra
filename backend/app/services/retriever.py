import os
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models.frame import Frame
from app.services.visual_embedder import VisualEmbedder
from app.services.text_embedder import TextEmbedder
from app.services.vector_store import VideoVectorStore

class MultimodalRetriever:
    def __init__(self, video_id: str):
        self.video_id = video_id
        self.vector_store = VideoVectorStore(video_id)
        self.visual_embedder = VisualEmbedder.get_instance()
        self.text_embedder = TextEmbedder.get_instance()

    def retrieve(
        self,
        query: str,
        top_k_visual: int = None,
        top_k_text: int = None,
        temporal_window: float = None
    ) -> Dict[str, Any]:
        """
        Performs dual visual and textual vector retrieval, expands temporal neighbors,
        and packages multimodal evidence for the VLM.
        """
        top_k_visual = top_k_visual or settings.TOP_K_VISUAL
        top_k_text = top_k_text or settings.TOP_K_TEXT
        temporal_window = temporal_window if temporal_window is not None else settings.TEMPORAL_WINDOW_SECONDS

        # 1. Visual Query Encoding and Retrieval (sorted by similarity desc)
        visual_query_vec = self.visual_embedder.embed_text(query)
        visual_results = self.vector_store.search_visual(visual_query_vec, top_k=top_k_visual)

        # 2. Text Query Encoding and Retrieval
        text_query_vec = self.text_embedder.embed_query(query)
        text_results = self.vector_store.search_text(text_query_vec, top_k=top_k_text)

        # 3. Temporal Context Expansion prioritized by highest similarity primary matches
        max_images = settings.MAX_VLM_IMAGES
        selected_frames = self._expand_temporal_context(visual_results, temporal_window, max_frames=max_images)

        return {
            "query": query,
            "visual_evidence": selected_frames,
            "audio_evidence": text_results,
            "raw_visual_matches": visual_results
        }

    def _expand_temporal_context(
        self,
        primary_frames: List[Dict[str, Any]],
        window_seconds: float,
        max_frames: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Retrieves neighboring frames for the top primary hits from SQLite to capture scene context.
        Prioritizes the highest-confidence primary matches and their adjacent temporal windows,
        then sorts the resulting evidence subset chronologically for the VLM.
        """
        if not primary_frames:
            return []

        db: Session = SessionLocal()
        selected_dict = {}

        try:
            # Process primary frames in order of similarity
            for p in primary_frames:
                if len(selected_dict) >= max_frames:
                    break

                fid = p["frame_id"]
                if fid not in selected_dict:
                    p_copy = dict(p)
                    p_copy["is_primary_match"] = True
                    selected_dict[fid] = p_copy

                # Retrieve immediate temporal neighbors [ts - window, ts + window]
                ts = p["timestamp"]
                neighbors = db.query(Frame).filter(
                    Frame.video_id == self.video_id,
                    Frame.timestamp >= ts - window_seconds,
                    Frame.timestamp <= ts + window_seconds,
                    Frame.id != fid
                ).all()

                for n in neighbors:
                    if len(selected_dict) >= max_frames:
                        break
                    if n.id not in selected_dict:
                        selected_dict[n.id] = {
                            "frame_id": n.id,
                            "video_id": self.video_id,
                            "timestamp": n.timestamp,
                            "frame_index": n.frame_index,
                            "image_path": n.image_path,
                            "image_url": f"/api/frames/{n.id}",
                            "similarity": round(float(p.get("similarity", 0.0) * 0.95), 4),
                            "is_primary_match": False
                        }

        finally:
            db.close()

        # Sort the prioritized evidence chronologically for the VLM
        chronological_frames = list(selected_dict.values())
        chronological_frames.sort(key=lambda x: x["timestamp"])

        return chronological_frames
