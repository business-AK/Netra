import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse, ConversationResponse, MessageResponse
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])

@router.post("/api/videos/{video_id}/chat", response_model=ChatResponse)
async def chat_with_video(video_id: str, request: ChatRequest):
    """
    Submits a natural language query for the video.
    Retrieves visual frames and transcript chunks, passes them to VLM,
    and returns a grounded answer with timestamps and evidence.
    """
    try:
        response = await ChatService.process_chat(
            video_id=video_id,
            message_text=request.message,
            conversation_id=request.conversation_id,
            vlm_provider=request.vlm_provider,
            vlm_model=request.vlm_model,
            vlm_base_url=request.vlm_base_url,
            api_key=request.api_key
        )
        return ChatResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@router.get("/api/videos/{video_id}/conversations", response_model=List[ConversationResponse])
def list_video_conversations(video_id: str, db: Session = Depends(get_db)):
    """Lists all conversations for a specific video."""
    convs = db.query(Conversation).filter(Conversation.video_id == video_id).order_by(Conversation.created_at.desc()).all()
    results = []
    for c in convs:
        msgs = []
        for m in c.messages:
            ev = []
            if m.evidence_json:
                try:
                    ev = json.loads(m.evidence_json)
                except Exception:
                    ev = []
            msgs.append(MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                evidence=ev,
                created_at=m.created_at
            ))
        results.append(ConversationResponse(
            id=c.id,
            video_id=c.video_id,
            created_at=c.created_at,
            messages=msgs
        ))
    return results

@router.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieves conversation history with messages and evidence."""
    c = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msgs = []
    for m in c.messages:
        ev = []
        if m.evidence_json:
            try:
                ev = json.loads(m.evidence_json)
            except Exception:
                ev = []
        msgs.append(MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            evidence=ev,
            created_at=m.created_at
        ))

    return ConversationResponse(
        id=c.id,
        video_id=c.video_id,
        created_at=c.created_at,
        messages=msgs
    )

