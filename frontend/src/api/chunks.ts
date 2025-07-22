import axios from 'axios';
import { config } from '../config';
import { ChunkInfo } from '../types';

export const chunksApi = {
  async getChunks(fileId: string): Promise<ChunkInfo[]> {
    const response = await axios.get<ChunkInfo[]>(`${config.uploadApiUrl}/chunks/${fileId}`);
    return response.data;
  },
}; 