import axios from 'axios';
import { config } from '../config';
import type { UploadResponse } from '../types';

export const uploadApi = {
  async uploadPdf(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<UploadResponse>(`${config.uploadApiUrl}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  getPdfUrl(fileId: string): string {
    // Properly encode the fileId to handle special characters
    const encodedFileId = encodeURIComponent(fileId);
    return `${config.uploadApiUrl}/file/${encodedFileId}/download`;
  },
}; 