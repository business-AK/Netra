export interface VisualEvidence {
  type: 'visual';
  timestamp: number;
  frame_id: string;
  image_url: string;
  similarity?: number;
  badge?: string;
}

export interface AudioEvidence {
  type: 'audio';
  start: number;
  end: number;
  text: string;
  similarity?: number;
}

export type EvidenceItem = VisualEvidence | AudioEvidence;

export interface ChatMessageData {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  evidence: EvidenceItem[];
  strategy?: string;
  created_at: string;
}

export interface ChatResponseData {
  conversation_id: string;
  answer: string;
  evidence: EvidenceItem[];
  strategy?: string;
}

export interface VLMSettings {
  provider: string; // 'ollama' | 'openai' | 'gemini' | 'groq' | 'lmstudio' | 'openrouter'
  model: string;
  baseUrl: string;
  apiKey: string;
  summaryN?: number;    // N for summarisation (keyframe count)
  topK?: number;        // K for top-k visual frames
  samplingFps?: number; // Sampled frames per second during upload
}

