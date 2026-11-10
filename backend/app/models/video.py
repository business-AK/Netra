import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_path = Column(String, nullable=False)
    duration = Column(Float, default=0.0)
    file_size = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_stage = Column(String, default="uploaded")
    processing_progress = Column(Float, default=0.0)  # 0.0 to 100.0
    processing_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    frames = relationship("Frame", back_populates="video", cascade="all, delete-orphan")
    transcript_segments = relationship("TranscriptSegment", back_populates="video", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="video", cascade="all, delete-orphan")

