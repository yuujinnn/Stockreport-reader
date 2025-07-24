import React from 'react';
import { X } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

export function PinnedChips() {
  const { pinnedChunks, chunks, togglePinChunk, hasBBox } = useAppStore();

  if (!hasBBox || pinnedChunks.length === 0) return null;

  const pinnedChunkDetails = pinnedChunks
    .map((chunkId) => chunks.find((c) => c.chunk_id === chunkId))
    .filter(Boolean);

  return (
    <div className="mb-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm text-gray-600">인용할 청크:</span>
        <span className="text-xs text-gray-500">({pinnedChunks.length}개 선택됨)</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {pinnedChunkDetails.map((chunk) => (
          <div
            key={chunk!.chunk_id}
            className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
          >
            <span>
              {chunk!.label || `p.${chunk!.page} #${chunk!.chunk_id.split('_')[1]}`}
            </span>
            <button
              onClick={() => togglePinChunk(chunk!.chunk_id)}
              className="ml-1 hover:bg-green-200 rounded-full p-0.5"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
} 