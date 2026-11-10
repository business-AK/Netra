import os
import shutil
import uuid
import mimetypes
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.video import Video
from app.schemas.video import VideoResponse, VideoStatusResponse
from app.services.video_processor import process_video_pipeline
from app.services.vector_store import VideoVectorStore

router = APIRouter(prefix="/api/videos", tags=["videos"])

ALLOWED_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}

@router.post("/upload", response_model=VideoStatusResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts video upload, validates extension, saves to storage, creates DB entry,
    and dispatches asynchronous background processing. Returns video ID immediately.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    video_id = str(uuid.uuid4())
    video_dir = os.path.join(settings.STORAGE_DIR, "videos", video_id)
    os.makedirs(video_dir, exist_ok=True)
    
    file_path = os.path.join(video_dir, f"original{ext}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    file_size = os.path.getsize(file_path)

    # Create video record
    video = Video(
        id=video_id,
        filename=file.filename,
        original_path=file_path,
        file_size=file_size,
        status="pending",
        processing_stage="uploaded",
        processing_progress=0.0
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Dispatch background processing task
    background_tasks.add_task(process_video_pipeline, video_id)

    return VideoStatusResponse(
        id=video.id,
        filename=video.filename,
        status=video.status,
        processing_stage=video.processing_stage,
        processing_progress=video.processing_progress,
        processing_error=video.processing_error
    )

@router.get("", response_model=List[VideoResponse])
def list_videos(db: Session = Depends(get_db)):
    """Lists all uploaded videos with metadata."""
    videos = db.query(Video).order_by(Video.created_at.desc()).all()
    results = []
    for v in videos:
        results.append(VideoResponse(
            id=v.id,
            filename=v.filename,
            duration=v.duration or 0.0,
            file_size=v.file_size or 0,
            status=v.status,
            processing_stage=v.processing_stage,
            processing_progress=v.processing_progress or 0.0,
            processing_error=v.processing_error,
            created_at=v.created_at,
            frames_count=len(v.frames),
            transcript_segments_count=len(v.transcript_segments)
        ))
    return results

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: str, db: Session = Depends(get_db)):
    """Returns single video metadata and counts."""
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")

    return VideoResponse(
        id=v.id,
        filename=v.filename,
        duration=v.duration or 0.0,
        file_size=v.file_size or 0,
        status=v.status,
        processing_stage=v.processing_stage,
        processing_progress=v.processing_progress or 0.0,
        processing_error=v.processing_error,
        created_at=v.created_at,
        frames_count=len(v.frames),
        transcript_segments_count=len(v.transcript_segments)
    )

@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(video_id: str, db: Session = Depends(get_db)):
    """Returns processing status and progress for polling."""
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")

    return VideoStatusResponse(
        id=v.id,
        filename=v.filename,
        status=v.status,
        processing_stage=v.processing_stage,
        processing_progress=v.processing_progress or 0.0,
        processing_error=v.processing_error
    )

@router.delete("/{video_id}")
def delete_video(video_id: str, db: Session = Depends(get_db)):
    """
    Deletes video, database records, extracted frames, indexes, and files.
    """
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")

    # 1. Delete vector indexes
    vector_store = VideoVectorStore(video_id)
    vector_store.delete_indexes()

    # 2. Delete original video directory
    video_dir = os.path.join(settings.STORAGE_DIR, "videos", video_id)
    if os.path.exists(video_dir):
        shutil.rmtree(video_dir, ignore_errors=True)

    # 3. Delete extracted frames directory
    frames_dir = os.path.join(settings.STORAGE_DIR, "frames", video_id)
    if os.path.exists(frames_dir):
        shutil.rmtree(frames_dir, ignore_errors=True)

    # 4. Delete audio file
    audio_path = os.path.join(settings.STORAGE_DIR, "audio", f"{video_id}.wav")
    if os.path.exists(audio_path):
        try:
            os.remove(audio_path)
        except Exception:
            pass

    # 5. Delete DB record (cascades to frames, transcripts, conversations, messages)
    db.delete(v)
    db.commit()

    return {"message": f"Video {video_id} and all associated resources deleted successfully"}

@router.get("/{video_id}/stream")
def stream_video(video_id: str, request: Request, range: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """
    Streams video file supporting HTTP Range requests for seeking in HTML5 players.
    """
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v or not os.path.exists(v.original_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    file_path = v.original_path
    file_size = os.path.getsize(file_path)
    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or "video/mp4"

    if range:
        byte_range = range.strip().lower()
        if byte_range.startswith("bytes="):
            parts = byte_range[6:].split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
            start = max(0, start)
            end = min(end, file_size - 1)
            chunk_length = end - start + 1

            def range_generator():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_remaining = chunk_length
                    while bytes_remaining > 0:
                        chunk_size = min(64 * 1024, bytes_remaining)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        bytes_remaining -= len(data)
                        yield data

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_length),
                "Content-Type": content_type,
            }
            return StreamingResponse(range_generator(), status_code=206, headers=headers)

    # Full file stream fallback
    def file_generator():
        with open(file_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                yield chunk

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": content_type,
    }
    return StreamingResponse(file_generator(), headers=headers)

