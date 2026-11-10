from datetime import datetime
from typing import Optional, List, Union, Literal
from pydantic import BaseModel

class VisualEvidence(BaseModel):
    type: Literal["visual"] = "visual"
    timestamp: float
    frame_id: str
    image_url: str
    similarity: Optional[float] = None

class AudioEvidence(BaseModel):
    type: Literal["audio"] = "audio"
    start: float
    end: float
    text: str
    similarity: Optional[float] = None

EvidenceItem = Union[VisualEvidence, AudioEvidence]

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    vlm_provider: Optional[str] = None
    vlm_model: Optional[str] = None
    vlm_base_url: Optional[str] = None
    api_key: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    evidence: List[dict]

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    evidence: List[dict] = []
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    video_id: str
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

