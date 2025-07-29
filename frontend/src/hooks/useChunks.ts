import { useQuery } from '@tanstack/react-query';
import { chunksApi } from '../api/chunks';
import { useAppStore } from '../store/useAppStore';
import { useEffect } from 'react';
import type { ChunkInfo } from '../types';

export function useChunks() {
  const { fileId, setChunks } = useAppStore();

  const query = useQuery({
    queryKey: ['chunks', fileId],
    queryFn: async (): Promise<ChunkInfo[]> => {
      console.log(`🔍 Fetching chunks for fileId: ${fileId}`);
      try {
        const chunks = await chunksApi.getChunks(fileId!);
        console.log(`✅ Received ${chunks.length} chunks:`, chunks);
        return chunks;
      } catch (error) {
        console.error(`❌ Error fetching chunks for ${fileId}:`, error);
        throw error;
      }
    },
    enabled: !!fileId,
    // 자동 refetch 비활성화 - 청크는 한 번 로드되면 변경되지 않음
    refetchInterval: false,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    staleTime: Infinity, // 데이터를 항상 fresh로 간주
  });

  // Handle data updates
  useEffect(() => {
    if (query.data) {
      console.log(`🔄 Setting chunks in store: ${query.data.length} chunks`);
      setChunks(query.data);
    }
  }, [query.data, setChunks]);

  // Handle errors
  useEffect(() => {
    if (query.error) {
      console.error('❌ useChunks error:', query.error);
    }
  }, [query.error]);

  // Debug logging
  useEffect(() => {
    console.log(`🔄 useChunks state - fileId: ${fileId}, isLoading: ${query.isLoading}, error: ${!!query.error}, chunks: ${query.data?.length || 0}`);
  }, [fileId, query.isLoading, query.error, query.data]);

  return {
    chunks: query.data || [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
} 