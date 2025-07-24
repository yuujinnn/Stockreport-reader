import { useQuery } from '@tanstack/react-query';
import { chunksApi } from '../api/chunks';
import { useAppStore } from '../store/useAppStore';
import { useEffect } from 'react';

export function useChunks() {
  const { fileId, setChunks } = useAppStore();

  const query = useQuery({
    queryKey: ['chunks', fileId],
    queryFn: () => chunksApi.getChunks(fileId!),
    enabled: !!fileId,
    refetchInterval: 5000, // Poll every 5 seconds for updates
  });

  useEffect(() => {
    if (query.data) {
      setChunks(query.data);
    }
  }, [query.data, setChunks]);

  return {
    chunks: query.data || [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
} 