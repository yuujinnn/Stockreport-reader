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
  // 페이지 크기 정보 추가 (백엔드에서 사용한 실제 크기)
  page_width?: number;
  page_height?: number;
  // 원본 픽셀 좌표 추가 (디버깅 및 재계산용)
  bbox_pixels?: [number, number, number, number]; // [left, top, right, bottom] in pixels
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
  pdfFilename?: string;
}

export interface QueryStreamChunk {
  content?: string;
  done?: boolean;
  pages?: number[];
  error?: string;
} 