import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
from app.routers import videos, frames, chat

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Netra - Multimodal VideoRAG API",
    description="Multimodal Video Retrieval-Augmented Generation using CLIP, Faster-Whisper, and Vision-Language Models.",
    version="1.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(videos.router)
app.include_router(frames.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {
        "app": "Netra Multimodal VideoRAG",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "visual_model": settings.VISUAL_MODEL,
        "whisper_model": settings.WHISPER_MODEL,
        "text_model": settings.TEXT_EMBEDDING_MODEL,
        "vlm_provider": settings.VLM_PROVIDER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

