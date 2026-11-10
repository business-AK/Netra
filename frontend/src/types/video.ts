export interface VideoItem {
  id: string;
  filename: string;
  duration: number;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_stage: string;
  processing_progress: number;
  processing_error?: string | null;
  created_at: string;
  frames_count: number;
  transcript_segments_count: number;
}

export interface VideoStatus {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_stage: string;
  processing_progress: number;
  processing_error?: string | null;
}

export interface FrameItem {
  id: string;
  video_id: string;
  timestamp: number;
  image_url: string;
  frame_index: number;
}

