export interface UploadResponse {
  fileId: string;
  pages: number | null;
  filename: string;
  uploadedAt: string;
}

export interface ChunkInfo {
  chunk_id: string;
  page: number;
  bbox_norm: [number, number, number, number]; // [left, top, right, bottom]
  chunk_type: 'text' | 'image' | 'table';
  content: string;
  label?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  pages?: number[];
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
}

export interface QueryRequest {
  query: string;
  pinChunks?: string[];
  fileId?: string;
}

export interface QueryStreamChunk {
  content?: string;
  done?: boolean;
  pages?: number[];
  error?: string;
} 