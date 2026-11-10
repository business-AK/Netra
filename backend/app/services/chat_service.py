import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.conversation import Conversation, Message
from app.models.video import Video
from app.services.retriever import MultimodalRetriever
from app.services.vlm_service import VLMService

class ChatService:
    @staticmethod
    async def process_chat(
        video_id: str,
        message_text: str,
        conversation_id: Optional[str] = None,
        vlm_provider: Optional[str] = None,
        vlm_model: Optional[str] = None,
        vlm_base_url: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Coordinates conversation management, multimodal retrieval, VLM reasoning,
        and persistence of messages and evidence.
        """
        db: Session = SessionLocal()
        try:
            # 1. Validate video exists
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video {video_id} does not exist.")

            # 2. Get or create conversation
            conv = None
            if conversation_id:
                conv = db.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.video_id == video_id
                ).first()

            if not conv:
                conv = Conversation(video_id=video_id)
                db.add(conv)
                db.commit()
                db.refresh(conv)

            # 3. Retrieve conversation history
            past_messages = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at.asc()).all()

            history_list = [
                {"role": m.role, "content": m.content}
                for m in past_messages
            ]

            # 4. Multimodal Retrieval
            retriever = MultimodalRetriever(video_id)
            retrieval_output = retriever.retrieve(message_text)

            visual_evidence = retrieval_output["visual_evidence"]
            audio_evidence = retrieval_output["audio_evidence"]

            # 5. Build Evidence List for Output
            evidence_items = []
            for vf in visual_evidence:
                evidence_items.append({
                    "type": "visual",
                    "timestamp": vf["timestamp"],
                    "frame_id": vf["frame_id"],
                    "image_url": vf["image_url"],
                    "similarity": vf.get("similarity", 0.0)
                })

            for af in audio_evidence:
                evidence_items.append({
                    "type": "audio",
                    "start": af["start"],
                    "end": af["end"],
                    "text": af["text"],
                    "similarity": af.get("similarity", 0.0)
                })

            # 6. Call VLM Service
            vlm = VLMService(
                provider=vlm_provider,
                model=vlm_model,
                base_url=vlm_base_url,
                api_key=api_key
            )

            answer = await vlm.generate_multimodal_answer(
                query=message_text,
                visual_evidence=visual_evidence,
                audio_evidence=audio_evidence,
                conversation_history=history_list
            )

            # 7. Persist User and Assistant Messages
            user_msg = Message(
                conversation_id=conv.id,
                role="user",
                content=message_text
            )
            assistant_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=answer,
                evidence_json=json.dumps(evidence_items)
            )

            db.add(user_msg)
            db.add(assistant_msg)
            db.commit()

            return {
                "conversation_id": conv.id,
                "answer": answer,
                "evidence": evidence_items
            }

        finally:
            db.close()

