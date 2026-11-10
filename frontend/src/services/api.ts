import axios from 'axios';
import { VideoItem, VideoStatus, FrameItem } from '../types/video';
import { ChatResponseData, VLMSettings } from '../types/chat';

const client = axios.create({
  baseURL: '',
  timeout: 180000, // 3 minutes timeout for cold-loading large 7B-11B models into GPU/RAM
});

export const api = {
  // Video Management
  uploadVideo: async (file: File, onUploadProgress?: (progressEvent: any) => void): Promise<VideoStatus> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await client.post<VideoStatus>('/api/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    });
    return response.data;
  },

  listVideos: async (): Promise<VideoItem[]> => {
    const response = await client.get<VideoItem[]>('/api/videos');
    return response.data;
  },

  getVideo: async (videoId: string): Promise<VideoItem> => {
    const response = await client.get<VideoItem>(`/api/videos/${videoId}`);
    return response.data;
  },

  getVideoStatus: async (videoId: string): Promise<VideoStatus> => {
    const response = await client.get<VideoStatus>(`/api/videos/${videoId}/status`);
    return response.data;
  },

  deleteVideo: async (videoId: string): Promise<void> => {
    await client.delete(`/api/videos/${videoId}`);
  },

  getVideoFrames: async (videoId: string): Promise<FrameItem[]> => {
    const response = await client.get<FrameItem[]>(`/api/videos/${videoId}/frames`);
    return response.data;
  },

  getVideoStreamUrl: (videoId: string): string => {
    return `/api/videos/${videoId}/stream`;
  },

  // Chat API
  sendChatMessage: async (
    videoId: string,
    message: string,
    conversationId?: string | null,
    vlmSettings?: VLMSettings
  ): Promise<ChatResponseData> => {
    const payload: any = {
      message,
      conversation_id: conversationId || null,
    };

    if (vlmSettings) {
      if (vlmSettings.provider) payload.vlm_provider = vlmSettings.provider;
      if (vlmSettings.model) payload.vlm_model = vlmSettings.model;
      if (vlmSettings.baseUrl) payload.vlm_base_url = vlmSettings.baseUrl;
      if (vlmSettings.apiKey) payload.api_key = vlmSettings.apiKey;
    }

    const response = await client.post<ChatResponseData>(`/api/videos/${videoId}/chat`, payload);
    return response.data;
  },

  getConversations: async (videoId: string): Promise<any[]> => {
    const response = await client.get<any[]>(`/api/videos/${videoId}/conversations`);
    return response.data;
  },

  getConversation: async (conversationId: string): Promise<any> => {
    const response = await client.get<any>(`/api/conversations/${conversationId}`);
    return response.data;
  },
};

