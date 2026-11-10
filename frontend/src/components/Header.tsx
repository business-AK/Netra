import React from 'react';
import { Eye, Settings, Video as VideoIcon } from 'lucide-react';

interface HeaderProps {
  onOpenSettings: () => void;
  onGoHome?: () => void;
  activeVideoTitle?: string;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenSettings,
  onGoHome,
  activeVideoTitle,
}) => {
  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <button
          onClick={onGoHome}
          className="flex items-center gap-2.5 group text-left focus:outline-none"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-[1px] shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center">
              <Eye className="w-5 h-5 text-indigo-400 group-hover:text-cyan-300 transition-colors" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base tracking-tight text-white">Netra</span>
              <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 rounded border border-indigo-500/30">
                VideoRAG
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-none">Multimodal Video Understanding</p>
          </div>
        </button>

        {activeVideoTitle && (
          <div className="hidden md:flex items-center gap-2 pl-4 ml-4 border-l border-slate-800 text-xs text-slate-300">
            <VideoIcon className="w-3.5 h-3.5 text-indigo-400" />
            <span className="max-w-[280px] truncate font-medium text-slate-200">
              {activeVideoTitle}
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {activeVideoTitle && (
          <button
            onClick={onGoHome}
            className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 rounded-lg border border-slate-700/60 transition"
          >
            Switch Video
          </button>
        )}
        <button
          onClick={onOpenSettings}
          title="Inference & VLM Settings"
          className="p-2 text-slate-400 hover:text-indigo-300 bg-slate-800/40 hover:bg-slate-800 rounded-lg border border-slate-800 hover:border-slate-700 transition"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};

