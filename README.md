# Netra - Multimodal VideoRAG

**Netra** is a full-stack, multimodal Video Retrieval-Augmented Generation (VideoRAG) application. It genuinely understands both the **visual** and **auditory** content of videos.

Unlike basic speech-to-text RAG tools that answer questions only from transcripts, Netra extracts synchronized video frames and audio streams, generates dense visual embeddings via **CLIP ViT-B/32**, transcribes speech with **Faster-Whisper**, indexes both into independent **FAISS** vector stores, performs joint multimodal retrieval with temporal context expansion, and sends actual image frames to a **Vision-Language Model (VLM)** for timestamp-grounded question answering.

---

## Key Features

- **Genuine Visual & Audio Understanding**: Answers questions about visible events, objects, actions, and scene transitions even when never spoken in audio.
- **Multimodal Dual-Index Retrieval**:
  - Semantic visual retrieval using **CLIP ViT-B/32** text-to-image similarity.
  - Transcript segment retrieval using **Sentence-Transformers (`all-MiniLM-L6-v2`)**.
- **Temporal Context Expansion**: When a frame is retrieved at timestamp $T$, adjacent frames in $[T - \delta, T + \delta]$ are retrieved to preserve continuous chronological scene context.
- **Direct VLM Image Inspection**: Sends retrieved JPEG frames directly to the VLM (supports Ollama `qwen2.5-vl`, OpenAI `gpt-4o`/`gpt-4o-mini`, OpenRouter, or compatible local/hosted endpoints).
- **Interactive Dual-Pane Workspace**:
  - HTML5 video player with HTTP Range request seeking.
  - Extracted frames gallery.
  - Conversational chat with clickable timestamps (`[00:15]`) and visual/audio evidence cards that seek the video instantly.
- **Configurable & Isolated**: Video vector indexes and metadata are persisted independently per video ID.

---

## System Architecture

```
User Query
    │
    ├─────────────────────────────┬─────────────────────────────┐
    ▼                             ▼                             ▼
CLIP Text Projection      Sentence-Transformers        Conversation History
    │                             │                             │
    ▼                             ▼                             │
Visual FAISS Index           Text FAISS Index                   │
    │                             │                             │
Top-K Visual Frames          Top-K Transcript Chunks            │
    │                             │                             │
    ▼                             │                             │
Temporal Expansion                │                             │
[T - 2s, T + 2s]                  │                             │
    │                             │                             │
    └──────────────┬──────────────┘                             │
                   ▼                                            │
        Context & Image Assembly                                │
        (Base64 JPEG Frames + Dialogue)                         │
                   │                                            │
                   └──────────────────────┬─────────────────────┘
                                          ▼
                             Vision-Language Model (VLM)
                             (Ollama / OpenAI-Compatible)
                                          ▼
                             Grounded Response & Evidence
                             - Answer text with timestamps
                             - Visual frame thumbnails & scores
                             - Spoken audio quotes & intervals
```

---

## Technology Stack

### Frontend
- **Framework**: React 19, TypeScript, Vite
- **Styling**: Tailwind CSS v4, Lucide React icons
- **Networking**: Axios

### Backend
- **Framework**: FastAPI, Uvicorn, Pydantic v2, SQLAlchemy
- **Database**: SQLite
- **Vector Search**: FAISS (`IndexFlatIP` with normalized embeddings)
- **Visual Embeddings**: OpenCLIP (`ViT-B-32`, OpenAI pretrained)
- **Speech Transcription**: Faster-Whisper (`base` or configurable)
- **Text Embeddings**: Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Video Processing**: FFmpeg, FFprobe, OpenCV (`cv2`)

---

## Prerequisites

1. **Python 3.11+** (Tested on Python 3.13)
2. **Node.js 18+** and **npm**
3. **FFmpeg & FFprobe**:
   - Windows (via WinGet): `winget install Gyan.FFmpeg`
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

---

## Installation & Setup

### 1. Clone & Set Up Backend

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt
```

Create or configure `.env` (optional, defaults are pre-configured):
```ini
DATABASE_URL=sqlite:///./storage/videorag.db
STORAGE_DIR=./storage
VISUAL_MODEL=ViT-B-32
PRETRAINED_VISUAL=openai
WHISPER_MODEL=base
TEXT_EMBEDDING_MODEL=all-MiniLM-L6-v2
VLM_PROVIDER=ollama
VLM_MODEL=qwen2.5-vl:7b
VLM_BASE_URL=http://localhost:11434
OPENAI_API_KEY=
FRAME_SAMPLING_FPS=1
TOP_K_VISUAL=10
TOP_K_TEXT=5
MAX_VLM_IMAGES=8
TEMPORAL_WINDOW_SECONDS=2.0
```

### 2. Set Up Frontend

```bash
cd frontend

# Install Node dependencies
npm install
```

---

## Running the Application

### Start the Backend Server

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Start the React Frontend

In a separate terminal:
```bash
cd frontend
npm run dev
```
Open your browser at [http://localhost:5173](http://localhost:5173).

---

## VLM Inference Setup

Netra can run with **Local Ollama**, **OpenAI**, or **OpenRouter**:

### Option A: Local Ollama (Offline / Private)
1. Install [Ollama](https://ollama.com).
2. Pull the vision model:
   ```bash
   ollama run qwen2.5-vl:7b
   ```
3. In Netra's UI, click the **Settings** icon in the top header:
   - Provider: `Local Ollama`
   - Model: `qwen2.5-vl:7b`
   - Base URL: `http://localhost:11434`

### Option B: Hosted OpenAI / OpenRouter
In the **Settings** modal:
- Provider: `OpenAI` or `OpenRouter`
- Model: `gpt-4o-mini`, `gpt-4o`, or `qwen/qwen-2.5-vl-72b-instruct:free`
- Base URL: `https://api.openai.com/v1` or `https://openrouter.ai/api/v1`
- API Key: `sk-...`

*(If no external VLM daemon is running, Netra automatically uses its built-in grounded visual-fallback engine to provide exact retrieved timestamps and evidence cards without crashing).*

---

## Running Automated Tests

Netra comes with automated end-to-end tests validating:
1. Video validation and frame extraction with timestamp accuracy.
2. CLIP ViT-B/32 normalized visual embedding generation.
3. Audio extraction & Faster-Whisper transcription (including videos with no speech).
4. Full pipeline ingestion and SQLite persistence.
5. Visual query retrieval (e.g. retrieving visual-only "red car" vs "blue door" timestamps).
6. Temporal context expansion.
7. Base64 JPEG data delivery to the VLM.
8. Grounded chat response schema with clickable evidence.
9. Video deletion and disk index cleanup.

Generate sample test videos and run the test suite:
```bash
# 1. Generate synthetic test videos
python tests/generate_test_videos.py

# 2. Run the test suite
python tests/test_videorag.py
```

---

## Project Structure

```
Netra/
├── backend/
│   ├── app/
│   │   ├── config.py              # Application settings & model configurations
│   │   ├── database.py            # SQLite engine & session management
│   │   ├── main.py                # FastAPI app & middleware
│   │   ├── models/                # SQLAlchemy models (Video, Frame, Transcript, Chat)
│   │   ├── schemas/               # Pydantic validation schemas
│   │   ├── routers/               # API endpoints (/videos, /frames, /chat)
│   │   ├── services/
│   │   │   ├── frame_extractor.py # 1 FPS frame sampling & timestamp tracking
│   │   │   ├── audio_extractor.py # FFmpeg 16kHz mono audio extraction
│   │   │   ├── transcription.py   # Faster-Whisper transcription & token chunking
│   │   │   ├── visual_embedder.py # CLIP ViT-B/32 image & query embedding
│   │   │   ├── text_embedder.py   # Sentence-Transformers text embedding
│   │   │   ├── vector_store.py    # FAISS IndexFlatIP persistence
│   │   │   ├── retriever.py       # Dual retrieval & temporal context expansion
│   │   │   ├── vlm_service.py     # Base64 multimodal VLM integration
│   │   │   ├── chat_service.py    # Multi-turn conversation & evidence assembly
│   │   │   └── video_processor.py # Background asynchronous ingestion worker
│   │   └── utils/                 # Timestamp & FFprobe file utilities
│   ├── storage/                   # Local filesystem storage for videos, frames, indexes
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/            # Header, VideoPlayer, ChatWindow, EvidenceCard, etc.
│   │   ├── pages/                 # Home (Library/Upload) & VideoWorkspace (Dual-pane)
│   │   ├── hooks/                 # useVideoStatus polling hook
│   │   ├── services/              # Axios API client
│   │   ├── types/                 # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── tests/
│   ├── generate_test_videos.py    # Synthetic video generator with visual actions
│   └── test_videorag.py           # Automated end-to-end test suite
└── README.md
```

