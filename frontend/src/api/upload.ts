import axios from 'axios';
import { config } from '../config';

export interface UploadResponse {
  fileId: string;
  pages?: number;
  filename: string;
  uploadedAt: string;
  processingStatus: string;
}

export interface ExistingFile {
  file_id: string;
  filename: string;
  saved_filename: string;
  pages: number;
  upload_timestamp: string;
  rag_status: 'completed' | 'processing' | 'not_processed';
  has_chunks: boolean;
  download_url: string;
  chunks_url?: string;
}

export interface ExistingFilesResponse {
  files: ExistingFile[];
  total: number;
  summary: {
    total_files: number;
    rag_completed: number;
    rag_processing: number;
    not_processed: number;
  };
}

export const uploadApi = {
  async uploadPdf(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${config.uploadApiUrl}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  async getExistingFiles(): Promise<ExistingFilesResponse> {
    const response = await axios.get(`${config.uploadApiUrl}/files`);
    return response.data;
  },

  getPdfUrl(fileId: string): string {
    return `${config.uploadApiUrl}/file/${fileId}/download`;
  },
}; 