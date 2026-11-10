import React from 'react';
import { Eye, Mic, Clock, ArrowUpRight } from 'lucide-react';
import { EvidenceItem, VisualEvidence, AudioEvidence } from '../types/chat';

interface EvidenceCardProps {
  evidence: EvidenceItem;
  onSeek: (seconds: number) => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence, onSeek }) => {
  const formatTime = (secs: number) => {
    const total = Math.max(0, Math.floor(secs));
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (evidence.type === 'visual') {
    const v = evidence as VisualEvidence;
    return (
      <div
        onClick={() => onSeek(v.timestamp)}
        className="group flex-shrink-0 w-44 bg-slate-900/90 border border-slate-800 hover:border-indigo-500/80 rounded-2xl overflow-hidden shadow-lg hover:shadow-indigo-500/10 transition-all cursor-pointer"
      >
        <div className="relative aspect-video bg-black overflow-hidden">
          <img
            src={v.image_url}
            alt={`Visual evidence at ${formatTime(v.timestamp)}`}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
          <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded-md bg-black/70 backdrop-blur-md flex items-center gap-1 text-[10px] text-cyan-300 font-medium border border-cyan-500/30">
            <Eye className="w-2.5 h-2.5" />
            <span>Frame</span>
          </div>
          {v.similarity && (
            <div className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded-md bg-black/70 backdrop-blur-md text-[10px] text-indigo-300 font-mono border border-indigo-500/30">
              {Math.round(v.similarity * 100)}%
            </div>
          )}
        </div>

        <div className="p-2.5 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-mono font-medium text-slate-200">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            <span>{formatTime(v.timestamp)}</span>
          </div>
          <span className="text-[10px] font-medium text-indigo-400 group-hover:text-indigo-300 flex items-center gap-0.5">
            Seek <ArrowUpRight className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </span>
        </div>
      </div>
    );
  }

  // Audio Evidence
  const a = evidence as AudioEvidence;
  return (
    <div
      onClick={() => onSeek(a.start)}
      className="group flex-shrink-0 w-52 bg-slate-900/90 border border-slate-800 hover:border-indigo-500/80 rounded-2xl p-3 shadow-lg hover:shadow-indigo-500/10 transition-all cursor-pointer flex flex-col justify-between"
    >
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="px-2 py-0.5 rounded-md bg-purple-500/20 text-purple-300 flex items-center gap-1 text-[10px] font-semibold border border-purple-500/30">
            <Mic className="w-2.5 h-2.5" />
            <span>Audio Transcript</span>
          </div>
          {a.similarity && (
            <span className="text-[10px] font-mono text-purple-300">
              {Math.round(a.similarity * 100)}%
            </span>
          )}
        </div>
        <p className="text-xs text-slate-300 italic line-clamp-3 leading-relaxed">
          "{a.text}"
        </p>
      </div>

      <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400">
          <Clock className="w-3 h-3 text-purple-400" />
          <span>{formatTime(a.start)} - {formatTime(a.end)}</span>
        </div>
        <span className="text-[10px] font-medium text-purple-400 group-hover:text-purple-300 flex items-center gap-0.5">
          Seek <ArrowUpRight className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </span>
      </div>
    </div>
  );
};

