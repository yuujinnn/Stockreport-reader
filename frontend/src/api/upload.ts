import axios from 'axios';
import { config } from '../config';
import { UploadResponse } from '../types';

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
    return `${config.uploadApiUrl}/file/${fileId}/download`;
  },
}; 