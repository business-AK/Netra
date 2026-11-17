# Netra - Multimodal VideoRAG

**Netra** is a full-stack, multimodal Video Retrieval-Augmented Generation (VideoRAG) platform. It genuinely understands both the **visual** and **auditory** content of videos.

Unlike traditional audio-only or speech-to-text RAG tools that answer questions solely from transcriptions, Netra extracts synchronized video frames and audio streams, generates dense visual embeddings via **CLIP ViT-B/32**, transcribes speech with **Faster-Whisper**, indexes both into independent **FAISS** vector spaces, routes queries through a **4-tier intelligent multi-pipeline architecture**, and sends actual retrieved image frames to a **Vision-Language Model (VLM)** for timestamp-grounded question answering.

---

## Key Highlights & Innovations

- **Multi-Pipeline Architecture**: Automatically classifies user queries into one of four specialized pipelines:
  1. **`SUMMARIZATION`**: Whole-video timeline keyframe sampling ($N$ frames from 0% to 100%) paired with a token-budgeted chronological dialogue transcript.
  2. **`TEMPORAL_TARGET`**: Direct second targeting $[T - 2.5s, T + 2.5s]$ or relative positions (`start`, `middle`, `end`) without vector drift.
  3. **`SEMANTIC_SEARCH`**: Contrastive visual & speech retrieval powered by CLIP and Sentence-Transformers with temporal context expansion.
  4. **`GENERIC_QA`**: Direct LLM response for general knowledge, technical/coding, or conversational follow-ups not related to the video—with zero false-positive visual cards and zero vision token overhead.
- **Intelligent Query Refining for CLIP**: Interrogative user queries (e.g., *"Is there a cat sitting on a car in this video?"*) suffer from cosine similarity degradation in CLIP's text space. Netra strips conversational filler, prefixes, and punctuation into clean descriptive phrases (e.g., `"cat sitting on a car"`) optimized for OpenCLIP embedding.
- **Transcript Matching & Disambiguation**: When queries seem generic (e.g., *"What is a coding editor?"*), Netra checks if the video's transcript actually discusses those terms. If so, it automatically routes to video semantic search; otherwise, it answers via general knowledge.
- **100% Local & Privacy-First**: Netra runs completely offline on consumer GPUs (e.g., NVIDIA RTX 4060 8GB VRAM) using local **Ollama** models (`qwen3.5-9b`, `qwen2.5-vl`, `llama3.2-vision`) or **LM Studio**. No video frames, audio, or prompts ever leave your machine. Hosted providers (Google Gemini, Groq Vision, OpenAI) are also supported out of the box.
- **Hardware-Adaptive Calibration**:
  - Configure **$N$** (Summary Keyframes: 2–10) to control context window usage on 6GB/8GB GPUs.
  - Configure **$K$** (Top-$K$ Search Frames: 2–12) to calibrate visual evidence density.
  - Configure **Sampling Rate** (0.5 FPS Eco, 1.0 FPS Standard, 2.0 FPS Dense) to balance ingestion speed against temporal granularity.
  - Automatic frame downscaling to 448px via Lanczos resampling, cutting vision tokens by over 60% and preventing Ollama context size errors (`HTTP 400`).
- **Pipeline Debug Visibility**: Every assistant response displays a transparent debug badge indicating exactly which pipeline handled the query (`Debug: Pipeline: SUMMARIZATION | TEMPORAL_TARGET | SEMANTIC_SEARCH | GENERIC_QA`).

---

## Detailed System Architecture

```
                                  User Query
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │   Query Router &    │
                           │    Preprocessor     │
                           └──────────┬──────────┘
                                      │
         ┌────────────────────────────┼───────────────────────────┬───────────────────────────┐
         ▼                            ▼                           ▼                           ▼
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│  SUMMARIZATION   │        │ TEMPORAL_TARGET  │        │ SEMANTIC_SEARCH  │        │    GENERIC_QA    │
│  (Overview/Recap)│        │ (Direct Time/Pos)│        │ (Visual / Audio) │        │ (General/Coding) │
└────────┬─────────┘        └────────┬─────────┘        └────────┬─────────┘        └────────┬─────────┘
         │                           │                           │                           │
         │ Stride Sampling           │ Direct Window             │ 1. Refine Query           │ Pure LLM Mode:
         │ (0% to 100% timeline)     │ [T - 2.5s, T + 2.5s]      │ 2. CLIP Text Embedding    │ - No frame retrieval
         │ + Chronological           │ or Start / Middle / End   │ 3. Text SBERT Embedding   │ - No vision tokens
         │   Transcript Budget       │                           │ 4. FAISS Search           │ - Fast text answer
         │                           │                           │ 5. Temporal Expansion     │
         └─────────────┬─────────────┴─────────────┬─────────────┴─────────────┬─────────────┘
                       │                           │                           │
                       ▼                           ▼                           ▼
                 Visual Frames               Transcript Chunks       Conversation History
               (448px Thumbnails)          (Time-stamped Quotes)        (Prior Turns)
                       │                           │                           │
                       └───────────────────────────┼───────────────────────────┘
                                                   ▼
                                     Multimodal VLM Service
                                 (Ollama / Gemini / Groq / OpenAI)
                                                   ▼
                                      Grounded Response Package
                                      - Natural language answer
                                      - Clickable timestamps ([00:15])
                                      - Interactive evidence cards
                                      - Pipeline Debug Badge
```

### 1. Ingestion Pipeline
1. **Video Ingestion & Validation**: Verifies video streams and duration with FFprobe and OpenCV.
2. **Frame Sampling**: Extracts frames at user-selected sampling rate (0.5 FPS, 1.0 FPS, or 2.0 FPS) and records precise timestamps.
3. **Visual Vector Embedding**: Normalizes extracted frames and encodes them with **OpenCLIP `ViT-B-32`** into 512-dimensional $L_2$-normalized vectors stored in a video-specific FAISS `IndexFlatIP`.
4. **Audio Extraction**: Isolates audio to a 16kHz mono WAV file using FFmpeg.
5. **Speech Transcription**: Runs **Faster-Whisper** (`base` or configurable) with timestamp word-level boundaries and token-bounded chunking.
6. **Transcript Vector Embedding**: Encodes transcript chunks with **Sentence-Transformers `all-MiniLM-L6-v2`** into 384-dimensional vectors stored in a secondary FAISS `IndexFlatIP`.

### 2. Multi-Pipeline Routing & Retrieval
- **Pipeline A (`SUMMARIZATION`)**: Triggered by queries like *"summarize this video"* or *"what happens in this video"*. Instead of taking top-$K$ semantic hits that cluster around repetitive high-contrast scenes, it samples $N$ keyframes evenly across the entire video timeline and pairs them with a 1,200-word budgeted dialogue transcript.
- **Pipeline B (`TEMPORAL_TARGET`)**: Triggered by specific timestamps (e.g., *"at 02:15"*, *"at 45 seconds"*) or positional anchors (*"at the beginning"*, *"at the end"*, *"in the middle"*). Directly retrieves frames in the window $[T - 2.5s, T + 2.5s]$ without semantic vector drift.
- **Pipeline C (`SEMANTIC_SEARCH`)**: Triggered by questions asking about visual entities, actions, colors, clothing, or scene events. Refines conversational queries into descriptive phrases, searches the visual FAISS index, and expands retrieved keyframes to include temporal neighbors $[T - 2s, T + 2s]$.
- **Pipeline D (`GENERIC_QA`)**: The least-touched fallback for questions like *"what is a coding editor"*, *"how to detect cancer symptoms"*, *"write a quicksort in python"*, or chit-chat. Bypasses frame retrieval to eliminate false-positive visual cards and provide fast, accurate answers. If the video's transcript explicitly discusses the topic, it automatically upgrades to `SEMANTIC_SEARCH`.

### 3. VLM Reasoning & Grounding
- Resizes retrieved frames to a maximum dimension of 448px before base64 encoding, preserving clarity while cutting visual token count from ~700 down to ~250 tokens per image.
- Passes images, transcript segments, and conversation history to the configured VLM with a 5-minute (300s) cold-load timeout.
- Supports multi-stage auto-retry: if local Ollama encounters a context limit error, Netra automatically retries with expanded context (`num_ctx: 16384`) or reduced keyframes.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Lucide React, Axios |
| **Backend** | Python 3.11+ / 3.13, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy |
| **Database** | SQLite (`videorag.db`) |
| **Vector Indexing** | FAISS (`IndexFlatIP` with cosine/inner product normalization) |
| **Visual Model** | OpenCLIP `ViT-B-32` (OpenAI weights) |
| **Audio & Speech** | Faster-Whisper, FFmpeg 9.0+ / Gyan build |
| **Text Model** | Sentence-Transformers `all-MiniLM-L6-v2` |
| **Media Processing** | OpenCV (`cv2`), Pillow (PIL) |
| **VLM Providers** | Local Ollama, Google Gemini, Groq Cloud, LM Studio, OpenAI, OpenRouter |

---

## Prerequisites

1. **Python 3.11+** (Tested on Python 3.13)
2. **Node.js 18+** and **npm**
3. **FFmpeg & FFprobe**:
   - **Windows** (via WinGet): `winget install Gyan.FFmpeg`
   - **Linux**: `sudo apt install ffmpeg`
   - **macOS**: `brew install ffmpeg`
4. *(Optional for local offline inference)*: **[Ollama](https://ollama.com)** with a multimodal or instruction-tuned model.

---

## Installation & Setup

### 1. Clone & Set Up Backend

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt
```

Configure `backend/.env` (optional, defaults are pre-configured for local Ollama):
```ini
DATABASE_URL=sqlite:///./storage/videorag.db
STORAGE_DIR=./storage
VISUAL_MODEL=ViT-B-32
PRETRAINED_VISUAL=openai
WHISPER_MODEL=base
TEXT_EMBEDDING_MODEL=all-MiniLM-L6-v2

# VLM Inference Provider ("ollama", "gemini", "groq", "lmstudio", "openai")
VLM_PROVIDER=ollama
VLM_MODEL=hf.co/HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive:Q4_K_M
VLM_BASE_URL=http://localhost:11434

# API Keys (leave blank for local Ollama / LM Studio)
GEMINI_API_KEY=
GROQ_API_KEY=
OPENAI_API_KEY=

# Ingestion & Retrieval defaults
FRAME_SAMPLING_FPS=1.0
TOP_K_VISUAL=6
MAX_VLM_IMAGES=5
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

### 1. Start the Backend API

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Start the Frontend Dev Server

In a separate terminal:
```bash
cd frontend
npm run dev
```
Open your browser at [http://localhost:5173](http://localhost:5173).

---

## Privacy & Local LLM Setup

Netra is built from the ground up for complete offline privacy. When using local Ollama or LM Studio, **no video content, extracted frames, audio transcripts, or queries leave your machine**.

### Option A: Local Ollama (Recommended for Privacy)
1. Install [Ollama](https://ollama.com).
2. Pull your preferred vision or instruction model:
   ```bash
   ollama pull qwen3.5-9b:latest
   # Or a specialized Vision-Language Model:
   ollama pull qwen2.5-vl:7b
   ```
3. Open Netra at `http://localhost:5173`, click the **Settings** icon in the top navigation bar:
   - **Provider**: `Local Ollama`
   - **Model**: `qwen3.5-9b:latest` (or `qwen2.5-vl:7b`)
   - **Base URL**: `http://localhost:11434`
   - **Hardware Calibration**: Adjust $N$ (Summary Frames), $K$ (Search Frames), and Sampling FPS to match your GPU VRAM.

### Option B: Google Gemini (Fast & Generous Free Tier)
- Select `Google Gemini` in Settings.
- Enter your Gemini API key from [Google AI Studio](https://aistudio.google.com).
- Model: `gemini-2.0-flash` or `gemini-1.5-flash`.

### Option C: Groq Cloud (Ultra-Fast Vision Inference)
- Select `Groq Vision` in Settings.
- Enter your Groq API key from [Groq Console](https://console.groq.com).
- Model: `llama-3.2-11b-vision-preview`.

---

## Automated Test Suite

Netra includes an end-to-end automated test suite verifying all layers:
1. Video validation and frame extraction with timestamp tracking.
2. OpenCLIP `ViT-B-32` normalized 512-dim visual embeddings.
3. Audio extraction and Faster-Whisper transcription (including silent video resilience).
4. Full pipeline ingestion and SQLite persistence.
5. Contrastive visual search (e.g., retrieving visual-only "red car" vs "blue door" timestamps).
6. Temporal context expansion.
7. 448px image resizing and Base64 JPEG delivery to VLM.
8. Grounded chat response schema with clickable evidence.
9. Summarization routing and whole-timeline stride sampling.
10. Temporal target retrieval for specific timestamps and anchors.
11. Generic QA routing separation (ensuring questions like *"what is a coding editor"* route to direct LLM mode with zero false-positive evidence cards).
12. Video deletion and filesystem index cleanup.

```bash
# 1. Generate synthetic test videos
python tests/generate_test_videos.py

# 2. Run the automated test suite
python tests/test_videorag.py
```

---

## Project Structure

```
Netra/
├── backend/
│   ├── app/
│   │   ├── config.py              # Application settings, paths & model parameters
│   │   ├── database.py            # SQLite engine, session maker & schema migrations
│   │   ├── main.py                # FastAPI initialization & CORS middleware
│   │   ├── models/                # SQLAlchemy database models
│   │   │   ├── video.py           # Video metadata & processing status
│   │   │   ├── frame.py           # Extracted frame timestamps & image paths
│   │   │   ├── transcript.py      # Transcribed speech segments & intervals
│   │   │   └── conversation.py    # Multi-turn chat sessions, messages & pipeline strategy
│   │   ├── schemas/               # Pydantic validation schemas
│   │   │   ├── video.py           # Video upload & status responses
│   │   │   ├── frame.py           # Frame list schemas
│   │   │   └── chat.py            # Chat request, response & evidence schemas
│   │   ├── routers/               # FastAPI route endpoints
│   │   │   ├── videos.py          # Video upload, status, list, delete & HTTP Range streaming
│   │   │   ├── frames.py          # Frame list & JPEG image serving
│   │   │   └── chat.py            # Chat QA endpoint & conversation history
│   │   ├── services/              # Core AI & processing services
│   │   │   ├── frame_extractor.py # Configurable FPS frame sampling with OpenCV
│   │   │   ├── audio_extractor.py # FFmpeg 16kHz mono audio extraction
│   │   │   ├── transcription.py   # Faster-Whisper transcription & token chunking
│   │   │   ├── visual_embedder.py # OpenCLIP ViT-B/32 visual embedding
│   │   │   ├── text_embedder.py   # Sentence-Transformers text embedding
│   │   │   ├── vector_store.py    # FAISS IndexFlatIP persistence per video ID
│   │   │   ├── query_router.py    # 4-tier query router & CLIP query preprocessor
│   │   │   ├── retriever.py       # Specialized dispatch: Summary, Temporal, Semantic & Generic
│   │   │   ├── vlm_service.py     # Base64 multimodal client (Ollama/Gemini/Groq/OpenAI)
│   │   │   ├── chat_service.py    # Multi-turn orchestration & evidence packaging
│   │   │   └── video_processor.py # Background asynchronous ingestion worker
│   │   └── utils/
│   │       ├── file_utils.py      # Video validation, FFprobe inspection & base64 downscaling
│   │       └── timestamp_utils.py # Second-to-string formatters & parsers
│   ├── storage/                   # Video storage, frame caches, and FAISS indexes (.gitignored)
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
├── frontend/
│   ├── src/
│   │   ├── components/            # UI components
│   │   │   ├── Header.tsx         # Navigation header & settings trigger
│   │   │   ├── VideoUploader.tsx  # Drag-and-drop uploader with sampling FPS selector
│   │   │   ├── ProcessingStatus.tsx # Stage progression checklist & progress bar
│   │   │   ├── VideoPlayer.tsx    # HTML5 video player with Range streaming & seek ref
│   │   │   ├── ChatWindow.tsx     # Conversational chat container
│   │   │   ├── ChatMessage.tsx    # Message bubble with clickable timestamps & Debug Badge
│   │   │   ├── EvidenceCard.tsx   # Multimodal thumbnail proof cards & seek triggers
│   │   │   ├── SettingsModal.tsx  # GUI for LLM providers & Hardware Calibration (N, K, FPS)
│   │   │   └── SuggestedQuestions.tsx # Contextual suggested prompt pills
│   │   ├── pages/
│   │   │   ├── Home.tsx           # Video library, upload view & ingestion monitor
│   │   │   └── VideoWorkspace.tsx # Split-screen video player & conversational VideoRAG
│   │   ├── hooks/
│   │   │   └── useVideoStatus.ts  # Video ingestion status polling hook
│   │   ├── services/
│   │   │   └── api.ts             # Axios API client with 5-minute cold-load timeout
│   │   ├── types/
│   │   │   ├── chat.ts            # Chat, Evidence & VLMSettings TypeScript interfaces
│   │   │   └── video.ts           # Video & Frame TypeScript interfaces
│   │   ├── App.tsx                # Main view router & settings persistence
│   │   ├── main.tsx
│   │   └── index.css              # Tailwind CSS styles
│   ├── package.json
│   ├── vite.config.ts
│   └── .gitignore
├── tests/
│   ├── generate_test_videos.py    # Synthetic video generator with visual action overlays
│   └── test_videorag.py           # 12-test automated unit and integration suite
├── .gitignore
└── README.md
```

