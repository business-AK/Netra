import React, { useState, useEffect } from 'react';
import { Film, Clock, Trash2, ArrowRight, Sparkles, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { VideoItem, VideoStatus } from '../types/video';
import { VideoUploader } from '../components/VideoUploader';
import { ProcessingStatus } from '../components/ProcessingStatus';
import { useVideoStatus } from '../hooks/useVideoStatus';

interface HomeProps {
  onSelectVideo: (videoId: string) => void;
}

export const Home: React.FC<HomeProps> = ({ onSelectVideo }) => {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [activeProcessingId, setActiveProcessingId] = useState<string | null>(null);
  const [isLoadingVideos, setIsLoadingVideos] = useState<boolean>(true);

  const { statusData, isCompleted } = useVideoStatus(activeProcessingId);

  const loadVideos = async () => {
    try {
      setIsLoadingVideos(true);
      const list = await api.listVideos();
      setVideos(list);
    } catch (err) {
      console.error('Failed to load videos:', err);
    } finally {
      setIsLoadingVideos(false);
    }
  };

  useEffect(() => {
    loadVideos();
  }, []);

  const handleUploadSuccess = (status: VideoStatus) => {
    setActiveProcessingId(status.id);
    loadVideos();
  };

  const handleDelete = async (e: React.MouseEvent, videoId: string) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this video and its indexes?')) {
      return;
    }
    try {
      await api.deleteVideo(videoId);
      if (activeProcessingId === videoId) {
        setActiveProcessingId(null);
      }
      loadVideos();
    } catch (err) {
      console.error('Failed to delete video:', err);
    }
  };

  const formatDuration = (secs: number) => {
    const total = Math.max(0, Math.floor(secs));
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 space-y-16">
      {/* Hero Section */}
      <div className="text-center space-y-4 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Multimodal Video Understanding & Retrieval</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
          Ask questions to your videos with genuine visual & audio reasoning.
        </h1>
        <p className="text-slate-400 text-sm md:text-base leading-relaxed">
          Netra extracts timestamped visual frames via CLIP and transcribes spoken dialogue via Whisper. Ask any question and receive grounded answers with clickable visual evidence.
        </p>
      </div>

      {/* Uploader or Active Processing View */}
      <div>
        {activeProcessingId ? (
          <div className="space-y-4">
            <ProcessingStatus
              statusData={statusData}
              onContinueToWorkspace={() => onSelectVideo(activeProcessingId)}
              onRetry={() => {
                setActiveProcessingId(null);
              }}
            />
            {isCompleted && (
              <div className="text-center">
                <button
                  onClick={() => setActiveProcessingId(null)}
                  className="text-xs text-slate-500 hover:text-slate-300 underline"
                >
                  Upload another video
                </button>
              </div>
            )}
          </div>
        ) : (
          <VideoUploader onUploadSuccess={handleUploadSuccess} />
        )}
      </div>

      {/* Video Library */}
      <div className="space-y-6 pt-6 border-t border-slate-900">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Film className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Video Index Library</h2>
          </div>
          <span className="text-xs text-slate-500">{videos.length} indexed video(s)</span>
        </div>

        {isLoadingVideos ? (
          <div className="flex items-center justify-center p-12 text-slate-500 text-sm gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
            <span>Loading library...</span>
          </div>
        ) : videos.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-slate-800/80 rounded-3xl bg-slate-900/20 text-slate-500 text-xs">
            No videos uploaded yet. Upload a video above to begin indexing.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {videos.map((vid) => {
              const isReady = vid.status === 'completed';
              const isProcessing = vid.status === 'processing' || vid.status === 'pending';
              const isFailed = vid.status === 'failed';

              return (
                <div
                  key={vid.id}
                  onClick={() => {
                    if (isReady) {
                      onSelectVideo(vid.id);
                    } else if (isProcessing) {
                      setActiveProcessingId(vid.id);
                    }
                  }}
                  className={`group p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between ${
                    isReady
                      ? 'bg-slate-900/60 border-slate-800 hover:border-indigo-500/60 hover:shadow-xl hover:shadow-indigo-500/5'
                      : isProcessing
                      ? 'bg-indigo-950/20 border-indigo-500/30'
                      : 'bg-rose-950/20 border-rose-500/30'
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-indigo-400 flex-shrink-0">
                        <Film className="w-5 h-5" />
                      </div>
                      <div className="flex items-center gap-1.5">
                        {isReady && (
                          <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 rounded-md border border-emerald-500/20 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Ready
                          </span>
                        )}
                        {isProcessing && (
                          <span className="px-2 py-0.5 text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 rounded-md border border-indigo-500/20 flex items-center gap-1 animate-pulse">
                            <Loader2 className="w-3 h-3 animate-spin" /> {Math.round(vid.processing_progress)}%
                          </span>
                        )}
                        {isFailed && (
                          <span className="px-2 py-0.5 text-[10px] font-semibold bg-rose-500/10 text-rose-400 rounded-md border border-rose-500/20 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> Failed
                          </span>
                        )}
                        <button
                          onClick={(e) => handleDelete(e, vid.id)}
                          title="Delete video"
                          className="p-1 text-slate-500 hover:text-rose-400 hover:bg-slate-800 rounded-md transition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-sm text-slate-100 truncate group-hover:text-indigo-300 transition">
                        {vid.filename}
                      </h4>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {formatSize(vid.file_size)} • {new Date(vid.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        {formatDuration(vid.duration)}
                      </span>
                      <span>•</span>
                      <span>{vid.frames_count} frames</span>
                    </div>

                    {isReady && (
                      <span className="text-indigo-400 font-medium flex items-center gap-1 text-[11px] group-hover:translate-x-0.5 transition-transform">
                        Chat <ArrowRight className="w-3 h-3" />
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

