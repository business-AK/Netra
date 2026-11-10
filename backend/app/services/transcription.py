import os
from typing import List, Dict, Any, Optional
from faster_whisper import WhisperModel
from app.config import settings

_whisper_model_instance = None

def get_whisper_model() -> WhisperModel:
    global _whisper_model_instance
    if _whisper_model_instance is None:
        # Check if CUDA is available, else fallback to CPU
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        print(f"Loading Faster-Whisper '{settings.WHISPER_MODEL}' on {device} ({compute_type})...")
        _whisper_model_instance = WhisperModel(
            settings.WHISPER_MODEL,
            device=device,
            compute_type=compute_type
        )
    return _whisper_model_instance

def transcribe_audio(audio_path: Optional[str]) -> List[Dict[str, Any]]:
    """
    Transcribes the provided audio file into timestamped segments.
    Returns a list of segments: [{"start": 12.4, "end": 15.8, "text": "..."}]
    """
    if not audio_path or not os.path.exists(audio_path):
        return []

    try:
        model = get_whisper_model()
        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=False,
            vad_filter=True, # remove non-speech silence
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        result_segments = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                result_segments.append({
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": text
                })
        return result_segments
    except Exception as e:
        print(f"Error during audio transcription: {e}")
        return []

def chunk_transcript(segments: List[Dict[str, Any]], target_chunk_words: int = 150, overlap_words: int = 30) -> List[Dict[str, Any]]:
    """
    Combines fine-grained Whisper segments into coherent chunks of 150-250 words,
    maintaining accurate overall start_time and end_time.
    """
    if not segments:
        return []

    chunks = []
    current_words = []
    current_start = segments[0]["start"]
    current_end = segments[0]["end"]

    for seg in segments:
        words = seg["text"].split()
        if not words:
            continue

        if len(current_words) + len(words) > target_chunk_words and len(current_words) > 0:
            chunk_text = " ".join(current_words)
            chunks.append({
                "start": current_start,
                "end": current_end,
                "text": chunk_text
            })
            # Overlap: keep the last few words
            overlap = current_words[-overlap_words:] if len(current_words) >= overlap_words else []
            current_words = overlap + words
            current_start = seg["start"]
            current_end = seg["end"]
        else:
            current_words.extend(words)
            current_end = seg["end"]

    if current_words:
        chunks.append({
            "start": current_start,
            "end": current_end,
            "text": " ".join(current_words)
        })

    return chunks

