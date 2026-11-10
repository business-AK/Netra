import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, MessageSquare, Bot } from 'lucide-react';
import { ChatMessageData, VLMSettings } from '../types/chat';
import { ChatMessage } from './ChatMessage';
import { SuggestedQuestions } from './SuggestedQuestions';

interface ChatWindowProps {
  messages: ChatMessageData[];
  isLoading: boolean;
  onSendMessage: (text: string) => void;
  onSeek: (seconds: number) => void;
  vlmSettings?: VLMSettings;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onSeek,
  vlmSettings,
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl backdrop-blur-md">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Bot className="w-8 h-8" />
            </div>
            <div className="max-w-md space-y-2">
              <h3 className="text-lg font-bold text-slate-100">Ask Anything About This Video</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Netra connects visual frames via CLIP embeddings and spoken dialogue via Whisper. Ask about visible objects, actions, conversations, or scene changes.
              </p>
            </div>
            <div className="w-full max-w-md pt-2">
              <SuggestedQuestions onSelectQuestion={(q) => onSendMessage(q)} />
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} onSeek={onSeek} />
            ))}

            {isLoading && (
              <div className="flex gap-3.5 my-4">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center flex-shrink-0 text-white animate-pulse">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl rounded-tl-none space-y-2 max-w-sm">
                  <div className="flex items-center gap-2 text-xs text-indigo-400 font-medium">
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                    <span>Searching visual frames & analyzing evidence...</span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Dual retrieval over visual and audio FAISS indexes
                  </p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input area */}
      <div className="p-4 bg-slate-950/80 border-t border-slate-800/80 space-y-3">
        {messages.length > 0 && (
          <div className="hidden sm:block">
            <SuggestedQuestions onSelectQuestion={(q) => onSendMessage(q)} />
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex items-end gap-2.5">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about the video (e.g. 'What is the person doing at 01:20?')"
              className="w-full bg-slate-900 border border-slate-800 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none max-h-32 transition"
            />
          </div>
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="p-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 text-white rounded-2xl shadow-lg shadow-indigo-600/20 transition flex-shrink-0 active:scale-95"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

