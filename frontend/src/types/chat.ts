export interface VisualEvidence {
  type: 'visual';
  timestamp: number;
  frame_id: string;
  image_url: string;
  similarity?: number;
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
  created_at: string;
}

export interface ChatResponseData {
  conversation_id: string;
  answer: string;
  evidence: EvidenceItem[];
}

export interface VLMSettings {
  provider: string; // 'ollama' | 'openai' | 'custom'
  model: string;
  baseUrl: string;
  apiKey: string;
}

