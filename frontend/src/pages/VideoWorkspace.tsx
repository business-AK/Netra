import React, { useState, useEffect, useRef } from 'react';
import { Loader2, ArrowLeft, Layers, Mic, Info } from 'lucide-react';
import { api } from '../services/api';
import { VideoItem, FrameItem } from '../types/video';
import { ChatMessageData, VLMSettings } from '../types/chat';
import { VideoPlayer, VideoPlayerRef } from '../components/VideoPlayer';
import { ChatWindow } from '../components/ChatWindow';

interface VideoWorkspaceProps {
  videoId: string;
  onBack: () => void;
  vlmSettings?: VLMSettings;
}

export const VideoWorkspace: React.FC<VideoWorkspaceProps> = ({
  videoId,
  onBack,
  vlmSettings,
}) => {
  const [video, setVideo] = useState<VideoItem | null>(null);
  const [frames, setFrames] = useState<FrameItem[]>([]);
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoadingVideo, setIsLoadingVideo] = useState<boolean>(true);
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);

  const playerRef = useRef<VideoPlayerRef>(null);

  // Load video details, frames, and conversations
  useEffect(() => {
    let isMounted = true;

    const init = async () => {
      try {
        setIsLoadingVideo(true);
        const [videoData, framesData, convs] = await Promise.all([
          api.getVideo(videoId),
          api.getVideoFrames(videoId),
          api.getConversations(videoId),
        ]);

        if (!isMounted) return;
        setVideo(videoData);
        setFrames(framesData);

        // Load existing messages if conversation exists
        if (convs && convs.length > 0) {
          const latestConv = convs[0];
          setConversationId(latestConv.id);
          setMessages(latestConv.messages || []);
        }
      } catch (err) {
        console.error('Error loading video workspace:', err);
      } finally {
        if (isMounted) setIsLoadingVideo(false);
      }
    };

    init();

    return () => {
      isMounted = false;
    };
  }, [videoId]);

  const handleSeek = (seconds: number) => {
    if (playerRef.current) {
      playerRef.current.seekTo(seconds);
    }
  };

  const handleSendMessage = async (text: string) => {
    // Optimistic user message
    const tempUserMsg: ChatMessageData = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      evidence: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsChatLoading(true);

    try {
      const response = await api.sendChatMessage(
        videoId,
        text,
        conversationId,
        vlmSettings
      );

      setConversationId(response.conversation_id);

      const assistantMsg: ChatMessageData = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        evidence: response.evidence || [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error('Chat error:', err);
      const errMsg: ChatMessageData = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${err?.response?.data?.detail || err.message || 'Failed to process question'}`,
        evidence: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsChatLoading(false);
    }
  };

  if (isLoadingVideo) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh] gap-3 text-slate-400">
        <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
        <span>Loading video workspace...</span>
      </div>
    );
  }

  if (!video) {
    return (
      <div className="p-12 text-center text-slate-400 space-y-4">
        <p>Video not found.</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-slate-800 text-slate-200 rounded-xl text-xs"
        >
          Back to Library
        </button>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-4rem)] p-4 md:p-6 flex flex-col overflow-hidden">
      {/* Top bar with back and video info */}
      <div className="flex items-center justify-between pb-3 flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white bg-slate-900/60 hover:bg-slate-800 border border-slate-800 rounded-xl transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Library</span>
          </button>
          <h2 className="text-sm font-bold text-slate-100 max-w-md truncate">
            {video.filename}
          </h2>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1 px-2 py-1 bg-slate-900/80 rounded-lg border border-slate-800">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            {video.frames_count} Visual Frames
          </span>
          <span className="flex items-center gap-1 px-2 py-1 bg-slate-900/80 rounded-lg border border-slate-800">
            <Mic className="w-3.5 h-3.5 text-purple-400" />
            {video.transcript_segments_count} Speech Segments
          </span>
        </div>
      </div>

      {/* Main 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0">
        {/* Left Column: Video Player */}
        <div className="lg:col-span-6 xl:col-span-7 flex flex-col min-h-0">
          <VideoPlayer
            ref={playerRef}
            videoId={video.id}
            duration={video.duration}
            frames={frames}
            onFrameSelect={(f) => handleSeek(f.timestamp)}
          />
        </div>

        {/* Right Column: Chat Interface */}
        <div className="lg:col-span-6 xl:col-span-5 flex flex-col min-h-0">
          <ChatWindow
            messages={messages}
            isLoading={isChatLoading}
            onSendMessage={handleSendMessage}
            onSeek={handleSeek}
            vlmSettings={vlmSettings}
          />
        </div>
      </div>
    </div>
  );
};

