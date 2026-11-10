import React, { useRef, useImperativeHandle, forwardRef, useState } from 'react';
import { Play, Pause, RotateCcw, Volume2, VolumeX, Maximize2, Images } from 'lucide-react';
import { api } from '../services/api';
import { FrameItem } from '../types/video';

export interface VideoPlayerRef {
  seekTo: (seconds: number) => void;
  play: () => void;
  pause: () => void;
}

interface VideoPlayerProps {
  videoId: string;
  duration?: number;
  frames?: FrameItem[];
  onFrameSelect?: (frame: FrameItem) => void;
}

export const VideoPlayer = forwardRef<VideoPlayerRef, VideoPlayerProps>(
  ({ videoId, duration, frames = [], onFrameSelect }, ref) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [currentTime, setCurrentTime] = useState<number>(0);
    const [isPlaying, setIsPlaying] = useState<boolean>(false);
    const [isMuted, setIsMuted] = useState<boolean>(false);
    const [showFrames, setShowFrames] = useState<boolean>(false);

    useImperativeHandle(ref, () => ({
      seekTo: (seconds: number) => {
        if (videoRef.current) {
          videoRef.current.currentTime = seconds;
          videoRef.current.play().catch(() => {});
          setIsPlaying(true);
        }
      },
      play: () => {
        videoRef.current?.play().catch(() => {});
        setIsPlaying(true);
      },
      pause: () => {
        videoRef.current?.pause();
        setIsPlaying(false);
      },
    }));

    const formatTime = (secs: number) => {
      const total = Math.max(0, Math.floor(secs));
      const m = Math.floor(total / 60);
      const s = total % 60;
      return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    const handleTimeUpdate = () => {
      if (videoRef.current) {
        setCurrentTime(videoRef.current.currentTime);
      }
    };

    const togglePlay = () => {
      if (!videoRef.current) return;
      if (isPlaying) {
        videoRef.current.pause();
        setIsPlaying(false);
      } else {
        videoRef.current.play().catch(() => {});
        setIsPlaying(true);
      }
    };

    const toggleMute = () => {
      if (!videoRef.current) return;
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    };

    const streamUrl = api.getVideoStreamUrl(videoId);

    return (
      <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl backdrop-blur-md">
        {/* Main Video View */}
        <div className="relative bg-black flex-1 flex items-center justify-center min-h-[300px] overflow-hidden group">
          <video
            ref={videoRef}
            src={streamUrl}
            className="w-full h-full object-contain max-h-[500px]"
            onTimeUpdate={handleTimeUpdate}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            controls
            playsInline
          />
        </div>

        {/* Video toolbar / Frame gallery switcher */}
        <div className="p-4 bg-slate-950/60 border-t border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFrames(!showFrames)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-xl border transition ${
                showFrames
                  ? 'bg-indigo-600/30 border-indigo-500 text-indigo-300'
                  : 'bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Images className="w-3.5 h-3.5" />
              <span>Extracted Frames ({frames.length})</span>
            </button>
          </div>

          <div className="text-xs font-mono text-slate-400">
            <span className="text-indigo-400 font-semibold">{formatTime(currentTime)}</span>
            {duration ? ` / ${formatTime(duration)}` : ''}
          </div>
        </div>

        {/* Collapsible Frames Gallery */}
        {showFrames && frames.length > 0 && (
          <div className="p-4 bg-slate-950/90 border-t border-slate-800/80 animate-in slide-in-from-bottom-2 duration-200">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Sampled Video Frames (~1 FPS)
            </div>
            <div className="flex gap-2.5 overflow-x-auto pb-2 scrollbar-thin">
              {frames.map((frame) => (
                <div
                  key={frame.id}
                  onClick={() => {
                    if (videoRef.current) {
                      videoRef.current.currentTime = frame.timestamp;
                      videoRef.current.play().catch(() => {});
                    }
                    onFrameSelect?.(frame);
                  }}
                  className="flex-shrink-0 cursor-pointer group relative rounded-xl overflow-hidden border border-slate-800 hover:border-indigo-500 transition-all w-28"
                >
                  <img
                    src={frame.image_url}
                    alt={`Frame at ${frame.timestamp}s`}
                    className="w-full h-16 object-cover group-hover:scale-105 transition-transform"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-1.5">
                    <span className="text-[10px] font-mono text-white font-medium">
                      {formatTime(frame.timestamp)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }
);

