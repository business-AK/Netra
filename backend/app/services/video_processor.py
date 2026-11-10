import os
import traceback
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.config import settings
from app.models.video import Video
from app.models.frame import Frame
from app.models.transcript import TranscriptSegment
from app.services.frame_extractor import extract_frames
from app.services.audio_extractor import extract_audio
from app.services.transcription import transcribe_audio, chunk_transcript
from app.services.visual_embedder import VisualEmbedder
from app.services.text_embedder import TextEmbedder
from app.services.vector_store import VideoVectorStore
from app.utils.file_utils import validate_video_file

def update_video_progress(video_id: str, stage: str, progress: float, error: str = None, status: str = None):
    db: Session = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.processing_stage = stage
            video.processing_progress = progress
            if error:
                video.processing_error = error
                video.status = "failed"
            elif status:
                video.status = status
            db.commit()
    finally:
        db.close()

def process_video_pipeline(video_id: str) -> None:
    """
    Complete multimodal ingestion and indexing pipeline for a video.
    Runs as an asynchronous background worker task.
    """
    db: Session = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            print(f"Error: Video {video_id} not found in database.")
            return

        video.status = "processing"
        video.processing_stage = "validating_media"
        video.processing_progress = 5.0
        db.commit()

        # 1. Validation and Metadata
        is_valid, err_msg, meta = validate_video_file(video.original_path)
        if not is_valid:
            raise ValueError(f"Invalid video format: {err_msg}")

        if meta.get("duration", 0.0) > 0:
            video.duration = meta["duration"]
            db.commit()

        # 2. Extract Frames
        update_video_progress(video_id, stage="extracting_frames", progress=15.0)
        extracted_frames = extract_frames(video.original_path, video_id, fps=settings.FRAME_SAMPLING_FPS)
        if not extracted_frames:
            raise RuntimeError("No frames could be extracted from the video.")

        # Save frame records to database
        db_frames = []
        visual_metadata = []
        for f in extracted_frames:
            frame_obj = Frame(
                video_id=video_id,
                timestamp=f["timestamp"],
                image_path=f["image_path"],
                frame_index=f["frame_index"]
            )
            db.add(frame_obj)
            db_frames.append(frame_obj)
        db.commit()

        # Prepare metadata for visual vector store
        for frame_obj in db_frames:
            visual_metadata.append({
                "frame_id": frame_obj.id,
                "video_id": video_id,
                "timestamp": frame_obj.timestamp,
                "frame_index": frame_obj.frame_index,
                "image_path": frame_obj.image_path,
                "image_url": f"/api/frames/{frame_obj.id}"
            })

        # 3. Visual Embeddings & FAISS Visual Index
        update_video_progress(video_id, stage="generating_visual_embeddings", progress=35.0)
        visual_embedder = VisualEmbedder.get_instance()
        frame_paths = [f["image_path"] for f in extracted_frames]
        visual_embeddings = visual_embedder.embed_images(frame_paths)

        vector_store = VideoVectorStore(video_id)
        vector_store.build_visual_index(visual_embeddings, visual_metadata)

        # 4. Audio Extraction
        update_video_progress(video_id, stage="extracting_audio", progress=55.0)
        audio_path = extract_audio(video.original_path, video_id)

        # 5. Audio Transcription & Chunking
        update_video_progress(video_id, stage="transcribing_speech", progress=70.0)
        transcript_segments = transcribe_audio(audio_path)

        # Save fine-grained transcript segments in SQLite
        for seg in transcript_segments:
            db_seg = TranscriptSegment(
                video_id=video_id,
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"]
            )
            db.add(db_seg)
        db.commit()

        # 6. Text Chunking & FAISS Text Index
        update_video_progress(video_id, stage="building_search_indexes", progress=85.0)
        chunks = chunk_transcript(transcript_segments)
        if chunks:
            text_embedder = TextEmbedder.get_instance()
            chunk_texts = [c["text"] for c in chunks]
            text_embeddings = text_embedder.embed_texts(chunk_texts)
            text_metadata = [
                {
                    "video_id": video_id,
                    "start": c["start"],
                    "end": c["end"],
                    "text": c["text"]
                }
                for c in chunks
            ]
            vector_store.build_text_index(text_embeddings, text_metadata)

        # 7. Completed!
        update_video_progress(video_id, stage="ready_for_questions", progress=100.0, status="completed")
        print(f"Video {video_id} processing completed successfully!")

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Video processing failed for {video_id}:\n{error_details}")
        update_video_progress(video_id, stage="failed", progress=0.0, error=str(e), status="failed")
    finally:
        db.close()

