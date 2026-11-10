import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
import cv2
import numpy as np
import wave
import struct
import math
import subprocess
from app.utils.file_utils import get_ffmpeg_path

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)

def generate_tone_wav(file_path: str, duration_sec: float = 6.0, freq: float = 440.0):
    sample_rate = 16000
    n_samples = int(sample_rate * duration_sec)
    with wave.open(file_path, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(n_samples):
            # 440Hz sine wave tone with brief pulses
            val = int(10000.0 * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            wav_file.writeframes(struct.pack("<h", val))

def create_video_1():
    """Video 1: Visual-only activities with minimal/no speech."""
    raw_video = os.path.join(SAMPLES_DIR, "v1_raw.mp4")
    final_video = os.path.join(SAMPLES_DIR, "test_visual_only.mp4")
    
    fps = 10
    duration = 8 # 8 seconds
    total_frames = fps * duration
    width, height = 640, 480
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(raw_video, fourcc, fps, (width, height))

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        if t < 3.0:
            # 0-3s: Red car moving across scene
            x = int(50 + (t / 3.0) * 450)
            y = 240
            cv2.rectangle(img, (x, y), (x + 100, y + 50), (0, 0, 220), -1)
            cv2.putText(img, f"Red Car Entering [{t:.1f}s]", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            cv2.putText(img, "Visual Activity: Car enters scene", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        elif t < 6.0:
            # 3-6s: Green bicycle in park
            x = int(100 + ((t - 3.0) / 3.0) * 350)
            y = 240
            cv2.circle(img, (x, y), 40, (0, 220, 0), -1)
            cv2.putText(img, f"Green Bicycle [{t:.1f}s]", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(img, "Visual Activity: Person riding bicycle", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        else:
            # 6-8s: Blue door opens
            cv2.rectangle(img, (260, 150), (380, 400), (220, 100, 0), -1)
            cv2.putText(img, f"Blue Door Opened [{t:.1f}s]", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 100, 0), 2)
            cv2.putText(img, "Visual Activity: Person opens blue door", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

        out.write(img)

    out.release()
    
    # Transcode to standard h264 with ffmpeg without audio
    ffmpeg = get_ffmpeg_path()
    subprocess.run([ffmpeg, "-y", "-i", raw_video, "-c:v", "libx264", "-pix_fmt", "yuv420p", final_video],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists(raw_video):
        os.remove(raw_video)
    print(f"Generated {final_video}")

def create_video_2():
    """Video 2: Educational video with slides and synthetic narration."""
    raw_video = os.path.join(SAMPLES_DIR, "v2_raw.mp4")
    wav_file = os.path.join(SAMPLES_DIR, "v2_tone.wav")
    final_video = os.path.join(SAMPLES_DIR, "test_educational.mp4")
    
    fps = 10
    duration = 9
    total_frames = fps * duration
    width, height = 640, 480
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(raw_video, fourcc, fps, (width, height))

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        img = np.full((height, width, 3), 30, dtype=np.uint8) # Dark background

        if t < 3.0:
            cv2.putText(img, "Lecture 1: Machine Learning", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            cv2.putText(img, "Topic: Introduction to Vector Search", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            cv2.putText(img, "Slide: Foundational Concepts", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
        elif t < 6.0:
            cv2.putText(img, "Lecture 2: Multimodal Representations", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            cv2.putText(img, "Topic: CLIP ViT-B/32 Visual Embeddings", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)
            cv2.putText(img, "Slide: Cross-Modal Alignment", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
        else:
            cv2.putText(img, "Lecture 3: Faster-Whisper Transcription", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            cv2.putText(img, "Topic: Time-aligned Audio Segments", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 180, 0), 2)
            cv2.putText(img, "Slide: Token Chunking and FAISS", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

        out.write(img)

    out.release()
    generate_tone_wav(wav_file, duration_sec=duration, freq=300.0)

    ffmpeg = get_ffmpeg_path()
    subprocess.run([
        ffmpeg, "-y",
        "-i", raw_video,
        "-i", wav_file,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        final_video
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for p in [raw_video, wav_file]:
        if os.path.exists(p):
            os.remove(p)
    print(f"Generated {final_video}")

def create_video_3():
    """Video 3: General video with both visual events and sound."""
    raw_video = os.path.join(SAMPLES_DIR, "v3_raw.mp4")
    wav_file = os.path.join(SAMPLES_DIR, "v3_tone.wav")
    final_video = os.path.join(SAMPLES_DIR, "test_general.mp4")
    
    fps = 10
    duration = 7
    total_frames = fps * duration
    width, height = 640, 480
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(raw_video, fourcc, fps, (width, height))

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        img = np.zeros((height, width, 3), dtype=np.uint8)

        # Draw a yellow sun
        cv2.circle(img, (540, 80), 50, (0, 220, 255), -1)

        if t < 3.5:
            # Walking person
            x = int(80 + (t / 3.5) * 200)
            cv2.circle(img, (x, 260), 25, (255, 255, 255), -1)
            cv2.line(img, (x, 285), (x, 380), (255, 255, 255), 4)
            cv2.putText(img, f"Outdoor Scene: Person Walking [{t:.1f}s]", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        else:
            # Person sitting on bench
            cv2.rectangle(img, (240, 340), (400, 370), (0, 120, 200), -1)
            cv2.circle(img, (320, 300), 25, (255, 255, 255), -1)
            cv2.putText(img, f"Outdoor Scene: Person Sitting [{t:.1f}s]", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        out.write(img)

    out.release()
    generate_tone_wav(wav_file, duration_sec=duration, freq=500.0)

    ffmpeg = get_ffmpeg_path()
    subprocess.run([
        ffmpeg, "-y",
        "-i", raw_video,
        "-i", wav_file,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        final_video
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for p in [raw_video, wav_file]:
        if os.path.exists(p):
            os.remove(p)
    print(f"Generated {final_video}")

if __name__ == "__main__":
    create_video_1()
    create_video_2()
    create_video_3()
    print("All 3 test videos generated successfully!")
