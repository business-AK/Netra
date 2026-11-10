import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.frame import Frame
from app.schemas.video import FrameResponse

router = APIRouter(tags=["frames"])

@router.get("/api/videos/{video_id}/frames", response_model=List[FrameResponse])
def get_video_frames(video_id: str, db: Session = Depends(get_db)):
    """Returns all extracted frames for a video sorted by timestamp."""
    frames = db.query(Frame).filter(Frame.video_id == video_id).order_by(Frame.timestamp.asc()).all()
    results = []
    for f in frames:
        results.append(FrameResponse(
            id=f.id,
            video_id=f.video_id,
            timestamp=f.timestamp,
            image_url=f"/api/frames/{f.id}",
            frame_index=f.frame_index
        ))
    return results

@router.get("/api/frames/{frame_id}")
def get_frame_image(frame_id: str, db: Session = Depends(get_db)):
    """Returns the raw image file for a given frame ID."""
    frame = db.query(Frame).filter(Frame.id == frame_id).first()
    if not frame or not os.path.exists(frame.image_path):
        raise HTTPException(status_code=404, detail="Frame image not found")

    return FileResponse(frame.image_path, media_type="image/jpeg")

