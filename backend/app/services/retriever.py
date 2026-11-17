import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models.video import Video
from app.models.frame import Frame
from app.models.transcript import TranscriptSegment
from app.services.visual_embedder import VisualEmbedder
from app.services.text_embedder import TextEmbedder
from app.services.vector_store import VideoVectorStore
from app.services.query_router import QueryRouter

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
        temporal_window: float = None,
        duration: float = 0.0
    ) -> Dict[str, Any]:
        """
        Main entry point for multimodal retrieval.
        Applies intent routing and query preprocessing:
          - SUMMARIZATION -> Uniform timeline sampling + full transcript
          - TEMPORAL_TARGET -> Direct timestamp / position range query
          - SEMANTIC_SEARCH -> Refined query CLIP search + text FAISS search
        """
        top_k_visual = top_k_visual or settings.TOP_K_VISUAL
        top_k_text = top_k_text or settings.TOP_K_TEXT
        temporal_window = temporal_window if temporal_window is not None else settings.TEMPORAL_WINDOW_SECONDS

        # 1. Look up video duration if not provided
        if duration <= 0.0:
            db: Session = SessionLocal()
            try:
                vid = db.query(Video).filter(Video.id == self.video_id).first()
                if vid and vid.duration:
                    duration = vid.duration
            finally:
                db.close()

        # 2. Route and classify intent
        routing = QueryRouter.route(query, video_duration=duration)
        strategy = routing["strategy"]

        # 3. Dispatch to specialized retrieval pipeline
        if strategy == "SUMMARIZATION":
            return self._retrieve_summary(query, routing, max_frames=settings.MAX_VLM_IMAGES)
        elif strategy == "TEMPORAL_TARGET":
            return self._retrieve_temporal(query, routing, window_seconds=temporal_window)
        elif strategy == "GENERIC_QA":
            # Safety check: if the video transcript explicitly mentions query keywords,
            # prioritize video semantic search so educational/topic videos are not bypassed
            if self._transcript_matches_query(query):
                return self._retrieve_semantic(query, routing, top_k_visual, top_k_text, temporal_window)
            return self._retrieve_generic(query, routing)
        else:
            return self._retrieve_semantic(query, routing, top_k_visual, top_k_text, temporal_window)

    def _retrieve_summary(
        self,
        query: str,
        routing: Dict[str, Any],
        max_frames: int = 5
    ) -> Dict[str, Any]:
        """
        Strategy 1: Global Stride Pipeline for Summaries.
        Picks N uniformly spaced frames (0% to 100% of duration) across the video,
        and retrieves a chronologically budgeted dialogue transcript to fit within local VRAM/context limits.
        """
        db: Session = SessionLocal()
        visual_evidence = []
        audio_evidence = []

        try:
            # 1. Fetch all frames sorted by timestamp
            all_frames = db.query(Frame).filter(
                Frame.video_id == self.video_id
            ).order_by(Frame.timestamp.asc()).all()

            if all_frames:
                total_f = len(all_frames)
                if total_f <= max_frames:
                    chosen = all_frames
                else:
                    # Pick max_frames evenly spaced from index 0 to total_f - 1
                    indices = [int(round(i * (total_f - 1) / (max_frames - 1))) for i in range(max_frames)]
                    # Deduplicate while preserving order
                    chosen = [all_frames[i] for i in sorted(list(dict.fromkeys(indices)))]

                for f in chosen:
                    visual_evidence.append({
                        "frame_id": f.id,
                        "video_id": self.video_id,
                        "timestamp": f.timestamp,
                        "frame_index": f.frame_index,
                        "image_path": f.image_path,
                        "image_url": f"/api/frames/{f.id}",
                        "similarity": 1.0,
                        "is_primary_match": True,
                        "badge": "Timeline Stride"
                    })

            # 2. Fetch transcript segments with token budget awareness
            segments = db.query(TranscriptSegment).filter(
                TranscriptSegment.video_id == self.video_id
            ).order_by(TranscriptSegment.start_time.asc()).all()

            # Budget: keep transcript under ~1200 words (~1500 tokens)
            total_words = sum(len(s.text.split()) for s in segments)
            if total_words > 1200 and len(segments) > 15:
                # Chronologically stride sample segments across the timeline
                target_count = 20
                stride_step = max(1, len(segments) // target_count)
                sampled_segments = segments[::stride_step]
                if segments[-1] not in sampled_segments:
                    sampled_segments.append(segments[-1])
            else:
                sampled_segments = segments

            for s in sampled_segments:
                audio_evidence.append({
                    "type": "audio",
                    "start": s.start_time,
                    "end": s.end_time,
                    "text": s.text,
                    "similarity": 1.0
                })

        finally:
            db.close()

        return {
            "query": query,
            "strategy": "SUMMARIZATION",
            "routing": routing,
            "visual_evidence": visual_evidence,
            "audio_evidence": audio_evidence,
            "raw_visual_matches": visual_evidence
        }

    def _retrieve_temporal(
        self,
        query: str,
        routing: Dict[str, Any],
        window_seconds: float = 2.5
    ) -> Dict[str, Any]:
        """
        Strategy 2: Time-Window Pipeline for specific timestamps or positions.
        Retrieves frames within [T - window, T + window] and matching transcript segments.
        """
        target_t = routing.get("target_timestamp", 0.0) or 0.0
        db: Session = SessionLocal()
        visual_evidence = []
        audio_evidence = []

        try:
            # 1. Fetch frames in [target_t - window, target_t + window]
            frames = db.query(Frame).filter(
                Frame.video_id == self.video_id,
                Frame.timestamp >= target_t - window_seconds,
                Frame.timestamp <= target_t + window_seconds
            ).order_by(Frame.timestamp.asc()).all()

            # If range yielded too few (e.g. edge of video or low fps), widen window
            if len(frames) < 3:
                frames = db.query(Frame).filter(
                    Frame.video_id == self.video_id,
                    Frame.timestamp >= target_t - (window_seconds * 2.0),
                    Frame.timestamp <= target_t + (window_seconds * 2.0)
                ).order_by(Frame.timestamp.asc()).limit(settings.MAX_VLM_IMAGES).all()

            for f in frames:
                # Calculate distance score to target
                dist = abs(f.timestamp - target_t)
                sim = round(max(0.1, 1.0 - (dist / 10.0)), 3)
                visual_evidence.append({
                    "frame_id": f.id,
                    "video_id": self.video_id,
                    "timestamp": f.timestamp,
                    "frame_index": f.frame_index,
                    "image_path": f.image_path,
                    "image_url": f"/api/frames/{f.id}",
                    "similarity": sim,
                    "is_primary_match": (dist <= 1.0),
                    "badge": f"Time Window (~{int(target_t)}s)"
                })

            # 2. Fetch transcript segments overlapping [target_t - 4, target_t + 4]
            segments = db.query(TranscriptSegment).filter(
                TranscriptSegment.video_id == self.video_id,
                TranscriptSegment.end_time >= target_t - 4.0,
                TranscriptSegment.start_time <= target_t + 4.0
            ).order_by(TranscriptSegment.start_time.asc()).all()

            for s in segments:
                audio_evidence.append({
                    "type": "audio",
                    "start": s.start_time,
                    "end": s.end_time,
                    "text": s.text,
                    "similarity": 1.0
                })

        finally:
            db.close()

        return {
            "query": query,
            "strategy": "TEMPORAL_TARGET",
            "routing": routing,
            "visual_evidence": visual_evidence,
            "audio_evidence": audio_evidence,
            "raw_visual_matches": visual_evidence
        }

    def _retrieve_semantic(
        self,
        query: str,
        routing: Dict[str, Any],
        top_k_visual: int,
        top_k_text: int,
        temporal_window: float
    ) -> Dict[str, Any]:
        """
        Strategy 3: Existing Vector Pipeline with Preprocessed Visual Query.
        Uses refined query for CLIP embedding and original query for text FAISS embedding.
        """
        visual_search_query = routing.get("visual_search_query", query)

        # 1. Visual query projection using REFINED descriptive text (e.g. "cat sitting on car")
        visual_query_vec = self.visual_embedder.embed_text(visual_search_query)
        visual_results = self.vector_store.search_visual(visual_query_vec, top_k=top_k_visual)

        # 2. Text query projection using full original query (e.g. "is there a cat sitting on car?")
        text_query_vec = self.text_embedder.embed_query(query)
        text_results = self.vector_store.search_text(text_query_vec, top_k=top_k_text)

        # 3. Temporal Context Expansion
        max_images = settings.MAX_VLM_IMAGES
        selected_frames = self._expand_temporal_context(visual_results, temporal_window, max_frames=max_images)

        return {
            "query": query,
            "strategy": "SEMANTIC_SEARCH",
            "routing": routing,
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

    def _retrieve_generic(
        self,
        query: str,
        routing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Strategy 4: Generic QA / Direct LLM.
        For general knowledge, coding, health, or off-topic conversational questions
        that do not relate to the video. Skips visual and audio retrieval to avoid
        false-positive evidence cards and reduce token/compute overhead.
        """
        return {
            "visual_evidence": [],
            "audio_evidence": [],
            "strategy": "GENERIC_QA",
            "routing": routing
        }

    def _transcript_matches_query(self, query: str) -> bool:
        """
        Disambiguation helper: Checks if any transcript segment in this video
        contains key topic words from the query before assuming it is off-topic.
        """
        import re
        db: Session = SessionLocal()
        try:
            words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', query)]
            stopwords = {"what", "when", "where", "which", "about", "there", "their", "could", "would", "should"}
            meaningful_words = [w for w in words if w not in stopwords]
            if not meaningful_words:
                return False

            segments = db.query(TranscriptSegment).filter(
                TranscriptSegment.video_id == self.video_id
            ).all()
            for seg in segments:
                text_lower = seg.text.lower()
                matched = sum(1 for w in meaningful_words if w in text_lower)
                if matched >= max(1, len(meaningful_words) // 2):
                    return True
            return False
        except Exception:
            return False
        finally:
            db.close()
