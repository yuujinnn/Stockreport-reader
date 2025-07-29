import axios from 'axios';
import { config } from '../config';
import type { ChunkInfo } from '../types';

export const chunksApi = {
  async getChunks(fileId: string): Promise<ChunkInfo[]> {
    const url = `${config.uploadApiUrl}/chunks/${fileId}`;
    console.log(`🌐 Calling chunks API: ${url}`);
    
    try {
      const response = await axios.get<ChunkInfo[]>(url);
      console.log(`✅ Chunks API response: status ${response.status}, data:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`❌ Chunks API error for ${url}:`, error);
      if (axios.isAxiosError(error)) {
        console.error(`❌ Axios error details:`, {
          status: error.response?.status,
          data: error.response?.data,
          message: error.message
        });
      }
      throw error;
    }
  },
}; 