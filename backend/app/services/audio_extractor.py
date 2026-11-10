import os
import subprocess
from typing import Optional
from app.config import settings
from app.utils.file_utils import get_ffmpeg_path, validate_video_file

def extract_audio(video_path: str, video_id: str) -> Optional[str]:
    """
    Extracts audio stream from video using FFmpeg.
    Converts to 16kHz mono PCM WAV required by Faster-Whisper.
    Returns the path to the extracted WAV file, or None if no audio exists.
    """
    # First check if the video has an audio stream
    _, _, meta = validate_video_file(video_path)
    if not meta.get("has_audio", True):
        return None

    audio_dir = os.path.join(settings.STORAGE_DIR, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    output_wav = os.path.join(audio_dir, f"{video_id}.wav")

    ffmpeg_bin = get_ffmpeg_path()
    cmd = [
        ffmpeg_bin,
        "-y",               # overwrite output
        "-i", video_path,   # input file
        "-vn",              # disable video
        "-acodec", "pcm_s16le", # 16-bit PCM
        "-ar", "16000",     # 16kHz sample rate
        "-ac", "1",         # mono channel
        output_wav
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_wav) and os.path.getsize(output_wav) > 1000:
            return output_wav
        else:
            # Maybe the video has no audio tracks despite initial detection
            if os.path.exists(output_wav):
                try:
                    os.remove(output_wav)
                except Exception:
                    pass
            return None
    except Exception as e:
        print(f"Warning: Audio extraction encountered exception: {e}")
        return None

