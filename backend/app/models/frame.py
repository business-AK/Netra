import uuid
from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Frame(Base):
    __tablename__ = "frames"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)
    image_path = Column(String, nullable=False)
    frame_index = Column(Integer, nullable=False)

    video = relationship("Video", back_populates="frames")

