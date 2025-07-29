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
        {pinnedChunkDetails.map((chunk) => {
          const getChipStyles = () => {
            switch (chunk!.chunk_type) {
              case 'text':
                return 'bg-green-100 text-green-800 hover:bg-green-200';
              case 'image':
                return 'bg-purple-100 text-purple-800 hover:bg-purple-200';
              case 'table':
                return 'bg-orange-100 text-orange-800 hover:bg-orange-200';
              default:
                return 'bg-gray-100 text-gray-800 hover:bg-gray-200';
            }
          };

          return (
            <div
              key={chunk!.chunk_id}
              className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${getChipStyles()}`}
            >
              <span className="text-xs">
                {chunk!.chunk_type === 'text' ? '📝' : chunk!.chunk_type === 'image' ? '🖼️' : '📊'}
              </span>
              <span>
                {chunk!.label || `p.${chunk!.page} #${chunk!.chunk_id.split('_')[1]}`}
              </span>
              <button
                onClick={() => togglePinChunk(chunk!.chunk_id)}
                className="ml-1 rounded-full p-0.5 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
} 