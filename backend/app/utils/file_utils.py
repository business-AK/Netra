import os
import shutil
import subprocess
import json
from typing import Optional, Tuple, Dict, Any

def get_ffmpeg_path() -> str:
    """Finds available ffmpeg binary."""
    # Check PATH first
    path = shutil.which("ffmpeg")
    if path and os.path.exists(path):
        return path
    
    # Check known winget installation location
    winget_path = r"C:\Users\kumbh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
    if os.path.exists(winget_path):
        return winget_path

    # Check imageio_ffmpeg
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass

    return "ffmpeg"

def get_ffprobe_path() -> str:
    """Finds available ffprobe binary."""
    path = shutil.which("ffprobe")
    if path and os.path.exists(path):
        return path

    winget_path = r"C:\Users\kumbh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffprobe.exe"
    if os.path.exists(winget_path):
        return winget_path

    return "ffprobe"

def validate_video_file(file_path: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validates that the file is a readable video format using ffprobe and cv2.
    Returns (is_valid, error_message, metadata_dict).
    """
    ffprobe_bin = get_ffprobe_path()
    metadata: Dict[str, Any] = {"duration": 0.0, "has_audio": False, "has_video": False, "width": 0, "height": 0}

    # Attempt ffprobe inspection
    try:
        cmd = [
            ffprobe_bin,
            "-v", "error",
            "-show_entries", "format=duration,size:stream=codec_type,width,height",
            "-of", "json",
            file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            streams = info.get("streams", [])
            for s in streams:
                if s.get("codec_type") == "video":
                    metadata["has_video"] = True
                    metadata["width"] = s.get("width", 0)
                    metadata["height"] = s.get("height", 0)
                elif s.get("codec_type") == "audio":
                    metadata["has_audio"] = True

            fmt = info.get("format", {})
            try:
                metadata["duration"] = float(fmt.get("duration", 0.0))
            except (ValueError, TypeError):
                metadata["duration"] = 0.0
    except Exception:
        pass

    # Fallback to OpenCV if ffprobe did not find video stream
    if not metadata["has_video"]:
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                if frame_count > 0:
                    metadata["has_video"] = True
                    metadata["duration"] = frame_count / fps
                    metadata["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    metadata["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
        except Exception as e:
            return False, f"Failed to open video file: {str(e)}", metadata

    if not metadata["has_video"]:
        return False, "File does not contain a valid or decodable video stream", metadata

    return True, None, metadata

