import os
import cv2
from typing import List, Dict, Any
from app.config import settings

def extract_frames(video_path: str, video_id: str, fps: float = 1.0) -> List[Dict[str, Any]]:
    """
    Extracts frames from video approximately every (1 / fps) seconds using OpenCV.
    Preserves exact timestamp of each extracted frame.
    Resizes frames to a max resolution for efficient embedding and storage.
    """
    output_dir = os.path.join(settings.STORAGE_DIR, "frames", video_id)
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps if total_frames > 0 else 0.0

    # Step in frames between sampled frames
    frame_interval = max(1, int(round(video_fps / fps)))
    
    extracted = []
    current_frame = 0
    saved_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if current_frame % frame_interval == 0:
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            # If timestamp is 0 or negative after the first frame, compute from frame index
            if timestamp <= 0.0 and current_frame > 0:
                timestamp = current_frame / video_fps

            saved_index += 1
            filename = f"frame_{saved_index:06d}.jpg"
            file_path = os.path.join(output_dir, filename)

            # Resize if large to conserve RAM/disk while maintaining visual fidelity
            h, w = frame.shape[:2]
            max_dim = 640
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            else:
                resized_frame = frame

            # Write JPEG
            cv2.imwrite(file_path, resized_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

            extracted.append({
                "frame_index": saved_index,
                "timestamp": round(timestamp, 3),
                "image_path": file_path,
                "filename": filename
            })

        current_frame += 1

    cap.release()
    return extracted

