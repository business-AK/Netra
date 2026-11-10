import React from 'react';
import { Bot, User, Clock, Film } from 'lucide-react';
import { ChatMessageData } from '../types/chat';
import { EvidenceCard } from './EvidenceCard';

interface ChatMessageProps {
  message: ChatMessageData;
  onSeek: (seconds: number) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onSeek }) => {
  const isUser = message.role === 'user';

  // Helper to parse MM:SS or HH:MM:SS into seconds
  const parseTimeToSeconds = (str: string) => {
    const parts = str.split(':').map(Number);
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    return 0;
  };

  // Render text and make timestamps like [00:15] or 01:23 clickable
  const renderFormattedText = (content: string) => {
    const timestampRegex = /\[?(\b\d{1,2}:\d{2}(?::\d{2})?\b)\]?/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = timestampRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        parts.push(content.substring(lastIndex, match.index));
      }
      const timeStr = match[1];
      const seconds = parseTimeToSeconds(timeStr);
      parts.push(
        <button
          key={`${match.index}-${timeStr}`}
          onClick={() => onSeek(seconds)}
          className="inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded-md bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 font-mono text-xs border border-indigo-500/30 transition align-baseline"
          title={`Seek video to ${timeStr}`}
        >
          <Clock className="w-3 h-3 text-indigo-400" />
          <span>{timeStr}</span>
        </button>
      );
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex));
    }

    return (
      <div className="whitespace-pre-wrap leading-relaxed text-sm">
        {parts.map((p, i) => (typeof p === 'string' ? <span key={i}>{p}</span> : p))}
      </div>
    );
  };

  return (
    <div className={`flex gap-3.5 my-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-white shadow-md ${
          isUser
            ? 'bg-slate-700'
            : 'bg-gradient-to-tr from-indigo-600 to-cyan-500 shadow-indigo-500/20'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message Content */}
      <div className={`max-w-[85%] space-y-3 ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`p-4 rounded-2xl shadow-sm ${
            isUser
              ? 'bg-indigo-600 text-white rounded-tr-none'
              : 'bg-slate-900 border border-slate-800 text-slate-100 rounded-tl-none'
          }`}
        >
          {renderFormattedText(message.content)}
        </div>

        {/* Evidence Carousel if available */}
        {!isUser && message.evidence && message.evidence.length > 0 && (
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <Film className="w-3.5 h-3.5 text-indigo-400" />
              <span>Retrieved Multimodal Evidence ({message.evidence.length})</span>
            </div>
            <div className="flex gap-2.5 overflow-x-auto pb-2 scrollbar-thin pt-1">
              {message.evidence.map((ev, idx) => (
                <EvidenceCard key={idx} evidence={ev} onSeek={onSeek} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

