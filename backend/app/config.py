import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Root backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Netra - Multimodal VideoRAG"
    STORAGE_DIR: str = str(BASE_DIR / "storage")
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'storage' / 'videorag.db'}"
    
    # AI Models
    VISUAL_MODEL: str = "ViT-B-32"
    PRETRAINED_VISUAL: str = "openai"
    WHISPER_MODEL: str = "base"
    TEXT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # VLM configuration
    VLM_PROVIDER: str = "ollama"  # "ollama", "openai", "custom", or "local_fallback"
    VLM_MODEL: str = "qwen2.5-vl:7b"
    VLM_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str = ""
    
    # Ingestion & Retrieval parameters
    FRAME_SAMPLING_FPS: float = 1.0
    TOP_K_VISUAL: int = 10
    TOP_K_TEXT: int = 5
    MAX_VLM_IMAGES: int = 8
    TEMPORAL_WINDOW_SECONDS: float = 2.0
    
    # Host settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "videos"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "frames"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "indexes"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "audio"), exist_ok=True)

