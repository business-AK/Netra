from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class VideoBase(BaseModel):
    filename: str

class VideoCreate(VideoBase):
    pass

class VideoStatusResponse(BaseModel):
    id: str
    filename: str
    status: str
    processing_stage: str
    processing_progress: float
    processing_error: Optional[str] = None

class VideoResponse(BaseModel):
    id: str
    filename: str
    duration: float
    file_size: int
    status: str
    processing_stage: str
    processing_progress: float
    processing_error: Optional[str] = None
    created_at: datetime
    frames_count: int = 0
    transcript_segments_count: int = 0

    class Config:
        from_attributes = True

class FrameResponse(BaseModel):
    id: str
    video_id: str
    timestamp: float
    image_url: str
    frame_index: int

    class Config:
        from_attributes = True

