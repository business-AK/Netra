import React from 'react';
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Camera,
  Layers,
  Volume2,
  Mic,
  Database,
  Sparkles,
  ArrowRight,
  RotateCw,
} from 'lucide-react';
import { VideoStatus } from '../types/video';

interface ProcessingStatusProps {
  statusData: VideoStatus | null;
  onContinueToWorkspace: () => void;
  onRetry?: () => void;
}

interface StageConfig {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  threshold: number;
}

const STAGES: StageConfig[] = [
  {
    id: 'extracting_frames',
    name: 'Frame Extraction',
    description: 'Sampling video frames at ~1 FPS with exact timestamps',
    icon: Camera,
    threshold: 15,
  },
  {
    id: 'generating_visual_embeddings',
    name: 'Visual Embeddings',
    description: 'Projecting frame images into 512-dim CLIP ViT-B/32 space',
    icon: Layers,
    threshold: 35,
  },
  {
    id: 'extracting_audio',
    name: 'Audio Extraction',
    description: 'Extracting 16kHz mono audio stream via FFmpeg',
    icon: Volume2,
    threshold: 55,
  },
  {
    id: 'transcribing_speech',
    name: 'Speech Transcription',
    description: 'Transcribing speech to timestamped text with Faster-Whisper',
    icon: Mic,
    threshold: 70,
  },
  {
    id: 'building_search_indexes',
    name: 'Search Indexing',
    description: 'Building dual visual and transcript FAISS vector indexes',
    icon: Database,
    threshold: 85,
  },
  {
    id: 'ready_for_questions',
    name: 'Ready for Questions',
    description: 'Multimodal indexing complete. Ready for conversational QA',
    icon: Sparkles,
    threshold: 100,
  },
];

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  statusData,
  onContinueToWorkspace,
  onRetry,
}) => {
  if (!statusData) return null;

  const currentStage = statusData.processing_stage;
  const progress = statusData.processing_progress || 0;
  const isFailed = statusData.status === 'failed';
  const isCompleted = statusData.status === 'completed';

  const getStageState = (stage: StageConfig, index: number) => {
    if (isFailed) {
      if (stage.id === currentStage) return 'failed';
    }
    if (isCompleted || progress >= stage.threshold) {
      return 'completed';
    }
    if (stage.id === currentStage) {
      return 'in_progress';
    }
    return 'pending';
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-slate-900/60 border border-slate-800 rounded-3xl p-8 backdrop-blur-md shadow-2xl animate-in fade-in">
      {/* Title & Progress */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            Multimodal Processing Pipeline
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md truncate">
            {statusData.filename}
          </p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-extrabold text-indigo-400 font-mono">
            {Math.round(progress)}%
          </span>
          <p className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">
            {statusData.status}
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mb-8 p-0.5 border border-slate-700/50">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${
            isFailed
              ? 'bg-rose-500'
              : 'bg-gradient-to-r from-indigo-500 via-indigo-400 to-cyan-400'
          }`}
          style={{ width: `${Math.max(5, progress)}%` }}
        />
      </div>

      {/* Stages list */}
      <div className="space-y-4 mb-8">
        {STAGES.map((stage, idx) => {
          const state = getStageState(stage, idx);
          const Icon = stage.icon;

          return (
            <div
              key={stage.id}
              className={`flex items-start gap-4 p-3.5 rounded-2xl transition border ${
                state === 'in_progress'
                  ? 'bg-indigo-950/30 border-indigo-500/40 shadow-lg shadow-indigo-500/5'
                  : state === 'completed'
                  ? 'bg-slate-850/40 border-slate-800/80 text-slate-300'
                  : state === 'failed'
                  ? 'bg-rose-950/20 border-rose-500/40 text-rose-300'
                  : 'bg-slate-900/20 border-slate-800/40 text-slate-500'
              }`}
            >
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  state === 'completed'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : state === 'in_progress'
                    ? 'bg-indigo-500/20 text-indigo-400 animate-pulse'
                    : state === 'failed'
                    ? 'bg-rose-500/20 text-rose-400'
                    : 'bg-slate-800/60 text-slate-600'
                }`}
              >
                {state === 'completed' ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : state === 'failed' ? (
                  <AlertCircle className="w-5 h-5 text-rose-400" />
                ) : (
                  <Icon className="w-5 h-5" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4
                    className={`text-sm font-semibold ${
                      state === 'in_progress'
                        ? 'text-indigo-300'
                        : state === 'completed'
                        ? 'text-slate-200'
                        : state === 'failed'
                        ? 'text-rose-300'
                        : 'text-slate-500'
                    }`}
                  >
                    {stage.name}
                  </h4>
                  {state === 'in_progress' && (
                    <span className="flex items-center gap-1.5 text-[11px] text-indigo-400 font-medium">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
                      In progress...
                    </span>
                  )}
                  {state === 'completed' && (
                    <span className="text-[11px] text-emerald-400 font-medium">Done</span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5">{stage.description}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Error message if failed */}
      {isFailed && (
        <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-start gap-3 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" />
          <div className="flex-1">
            <h5 className="font-semibold text-rose-200">Processing Failed</h5>
            <p className="text-xs mt-1 text-rose-300/90">{statusData.processing_error}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="mt-3 flex items-center gap-1.5 px-3 py-1.5 bg-rose-600/30 hover:bg-rose-600/50 text-rose-200 text-xs font-medium rounded-lg border border-rose-500/40 transition"
              >
                <RotateCw className="w-3.5 h-3.5" /> Retry Processing
              </button>
            )}
          </div>
        </div>
      )}

      {/* Action button once completed */}
      {isCompleted && (
        <div className="flex justify-end">
          <button
            onClick={onContinueToWorkspace}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-sm rounded-2xl shadow-xl shadow-indigo-600/30 transition transform hover:scale-[1.02] active:scale-95"
          >
            <span>Open Video Chat Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};

