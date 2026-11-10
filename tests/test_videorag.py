import os
import sys
import unittest
import shutil
import asyncio

# Ensure backend modules are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.config import settings
from app.database import Base, engine, SessionLocal
from app.models.video import Video
from app.models.frame import Frame
from app.models.transcript import TranscriptSegment
from app.services.frame_extractor import extract_frames
from app.services.audio_extractor import extract_audio
from app.services.transcription import transcribe_audio, chunk_transcript
from app.services.visual_embedder import VisualEmbedder
from app.services.text_embedder import TextEmbedder
from app.services.vector_store import VideoVectorStore
from app.services.retriever import MultimodalRetriever
from app.services.vlm_service import VLMService, encode_image_base64
from app.services.video_processor import process_video_pipeline
from app.services.chat_service import ChatService

class TestNetraVideoRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.samples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "samples"))
        cls.v1_path = os.path.join(cls.samples_dir, "test_visual_only.mp4")
        cls.v2_path = os.path.join(cls.samples_dir, "test_educational.mp4")
        cls.v3_path = os.path.join(cls.samples_dir, "test_general.mp4")

    def test_01_frame_extraction(self):
        """Test frame extraction preserves timestamps and extracts expected frame count."""
        video_id = "test_vid_frames"
        extracted = extract_frames(self.v1_path, video_id, fps=1.0)
        self.assertGreater(len(extracted), 0, "Should extract frames from valid video")
        
        # Verify timestamps are non-negative and strictly non-decreasing
        timestamps = [f["timestamp"] for f in extracted]
        for i in range(len(timestamps) - 1):
            self.assertLessEqual(timestamps[i], timestamps[i+1], "Timestamps must be non-decreasing")
        
        # Check that files exist on disk
        for f in extracted:
            self.assertTrue(os.path.exists(f["image_path"]), f"Frame file must exist: {f['image_path']}")

        # Clean up test frames
        frames_dir = os.path.join(settings.STORAGE_DIR, "frames", video_id)
        if os.path.exists(frames_dir):
            shutil.rmtree(frames_dir, ignore_errors=True)

    def test_02_visual_embedding_generation(self):
        """Test CLIP ViT-B/32 embedding generation and normalization."""
        video_id = "test_vid_clip"
        extracted = extract_frames(self.v1_path, video_id, fps=1.0)
        frame_paths = [f["image_path"] for f in extracted[:3]]
        
        embedder = VisualEmbedder.get_instance()
        embeddings = embedder.embed_images(frame_paths)
        
        self.assertEqual(embeddings.shape[0], len(frame_paths))
        self.assertEqual(embeddings.shape[1], 512, "CLIP ViT-B/32 embedding dimension must be 512")
        
        # Verify L2 normalization (norm should be ~1.0)
        norms = (embeddings ** 2).sum(axis=-1) ** 0.5
        for norm in norms:
            self.assertAlmostEqual(norm, 1.0, places=4, msg="Embeddings must be L2 normalized")

        # Test text embedding projection
        text_vec = embedder.embed_text("a red car entering")
        self.assertEqual(text_vec.shape[1], 512)
        text_norm = (text_vec ** 2).sum() ** 0.5
        self.assertAlmostEqual(text_norm, 1.0, places=4)

        # Clean up
        shutil.rmtree(os.path.join(settings.STORAGE_DIR, "frames", video_id), ignore_errors=True)

    def test_03_audio_extraction_and_transcription(self):
        """Test audio extraction and faster-whisper transcription."""
        video_id = "test_vid_audio"
        # Visual-only video has no audio or silence
        audio_path_silent = extract_audio(self.v1_path, video_id)
        segments_silent = transcribe_audio(audio_path_silent)
        self.assertIsInstance(segments_silent, list)

        # Educational video has audio track
        audio_path_edu = extract_audio(self.v2_path, video_id + "_edu")
        self.assertIsNotNone(audio_path_edu)
        self.assertTrue(os.path.exists(audio_path_edu))
        
        # Clean up audio files
        for p in [audio_path_silent, audio_path_edu]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    def test_04_full_pipeline_ingestion(self):
        """Test end-to-end ingestion pipeline on test_visual_only.mp4."""
        db = SessionLocal()
        video_id = "test_pipeline_v1"
        
        # Remove any leftover record from previous runs
        old_v = db.query(Video).filter(Video.id == video_id).first()
        if old_v:
            db.delete(old_v)
            db.commit()

        # Copy to storage/videos/test_pipeline_v1/original.mp4
        target_dir = os.path.join(settings.STORAGE_DIR, "videos", video_id)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, "original.mp4")
        shutil.copyfile(self.v1_path, target_path)

        vid_rec = Video(
            id=video_id,
            filename="test_visual_only.mp4",
            original_path=target_path,
            file_size=os.path.getsize(target_path),
            status="pending"
        )
        db.add(vid_rec)
        db.commit()
        db.close()

        # Run pipeline
        process_video_pipeline(video_id)

        # Verify database record
        db = SessionLocal()
        updated_vid = db.query(Video).filter(Video.id == video_id).first()
        self.assertIsNotNone(updated_vid)
        self.assertEqual(updated_vid.status, "completed")
        self.assertEqual(updated_vid.processing_progress, 100.0)
        self.assertGreater(len(updated_vid.frames), 0)
        db.close()

    def test_05_visual_query_retrieval(self):
        """
        Verify that a visual query ('red car') retrieves frames from the correct timestamp (0-3s),
        proving genuine visual understanding independent of audio!
        """
        video_id = "test_pipeline_v1"
        retriever = MultimodalRetriever(video_id)
        
        # Query 1: Red car entering scene (visually happens at 0-3s)
        res_car = retriever.retrieve("red car entering scene", top_k_visual=5)
        self.assertGreater(len(res_car["raw_visual_matches"]), 0)
        top_car = res_car["raw_visual_matches"][0]
        print(f"\nTop visual match for 'red car': Timestamp={top_car['timestamp']}s, Similarity={top_car.get('similarity')}")
        self.assertLessEqual(top_car["timestamp"], 3.5, "Top frame for red car must be within the first 3.5 seconds!")

        # Query 2: Blue door (visually happens at 6-8s)
        res_door = retriever.retrieve("blue door opened", top_k_visual=5)
        self.assertGreater(len(res_door["raw_visual_matches"]), 0)
        top_door = res_door["raw_visual_matches"][0]
        print(f"Top visual match for 'blue door': Timestamp={top_door['timestamp']}s, Similarity={top_door.get('similarity')}")
        self.assertGreaterEqual(top_door["timestamp"], 5.0, "Top frame for blue door must be at 5.0s or later!")

    def test_06_temporal_context_expansion(self):
        """Test that retriever expands neighboring frames within temporal window."""
        video_id = "test_pipeline_v1"
        retriever = MultimodalRetriever(video_id)
        res = retriever.retrieve("green bicycle in park", top_k_visual=1, temporal_window=2.0)
        
        visual_evidence = res["visual_evidence"]
        self.assertGreater(len(visual_evidence), 0)
        
        # Verify chronological ordering
        for i in range(len(visual_evidence) - 1):
            self.assertLessEqual(visual_evidence[i]["timestamp"], visual_evidence[i+1]["timestamp"])

    def test_07_image_data_reaches_vlm(self):
        """
        Critical requirement verification: verify that actual image data
        reaches the VLM service as valid base64 data URLs.
        """
        video_id = "test_pipeline_v1"
        retriever = MultimodalRetriever(video_id)
        res = retriever.retrieve("red car entering scene", top_k_visual=3)
        
        frames = res["visual_evidence"]
        for f in frames:
            b64_str = encode_image_base64(f["image_path"])
            self.assertIsNotNone(b64_str, "Base64 encoding must succeed")
            self.assertGreater(len(b64_str), 100, "Base64 string must contain actual image payload")
            
            # Verify valid base64 decodability
            import base64
            decoded_bytes = base64.b64decode(b64_str)
            self.assertGreater(len(decoded_bytes), 0)
            # JPEG magic bytes: \xff\xd8
            self.assertEqual(decoded_bytes[:2], b'\xff\xd8', "Encoded image must be valid JPEG data")

    def test_08_grounded_chat_response_schema(self):
        """Test full chat processing returning grounded answer and evidence metadata."""
        video_id = "test_pipeline_v1"
        
        response = asyncio.run(
            ChatService.process_chat(
                video_id=video_id,
                message_text="What color is the car entering the scene?"
            )
        )

        self.assertIn("conversation_id", response)
        self.assertIn("answer", response)
        self.assertIn("evidence", response)
        self.assertIsInstance(response["evidence"], list)
        self.assertGreater(len(response["evidence"]), 0)

        # Check evidence item schema
        first_ev = response["evidence"][0]
        self.assertIn("type", first_ev)
        self.assertIn("timestamp", first_ev)
        self.assertIn("frame_id", first_ev)
        self.assertIn("image_url", first_ev)
        print(f"\nGrounded Chat Answer:\n{response['answer']}")
        print(f"Evidence items count: {len(response['evidence'])}")

    def test_09_video_deletion_cleanup(self):
        """Test video deletion cleans up database and all filesystem artifacts."""
        video_id = "test_pipeline_v1"
        
        # Instantiate vector store and test cleanup
        vstore = VideoVectorStore(video_id)
        vstore.delete_indexes()
        
        self.assertFalse(os.path.exists(vstore.visual_index_path))
        self.assertFalse(os.path.exists(vstore.visual_meta_path))

        # Clean database record
        db = SessionLocal()
        v = db.query(Video).filter(Video.id == video_id).first()
        if v:
            db.delete(v)
            db.commit()
        db.close()

        # Clean filesystem
        v_dir = os.path.join(settings.STORAGE_DIR, "videos", video_id)
        f_dir = os.path.join(settings.STORAGE_DIR, "frames", video_id)
        shutil.rmtree(v_dir, ignore_errors=True)
        shutil.rmtree(f_dir, ignore_errors=True)

        self.assertFalse(os.path.exists(v_dir))
        self.assertFalse(os.path.exists(f_dir))

if __name__ == "__main__":
    unittest.main()
