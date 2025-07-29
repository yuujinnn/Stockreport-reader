import React from 'react';
import { Pin } from 'lucide-react';
import type { ChunkInfo } from '../../types';
import { useAppStore } from '../../store/useAppStore';
import classNames from 'classnames';

interface ChunkOverlayProps {
  chunk: ChunkInfo;
  pageWidth: number;
  pageHeight: number;
  scale: number;
}

export function ChunkOverlay({ chunk, pageWidth, pageHeight, scale }: ChunkOverlayProps) {
  const { pinnedChunks, togglePinChunk } = useAppStore();
  const [isHovered, setIsHovered] = React.useState(false);

  const isPinned = pinnedChunks.includes(chunk.chunk_id);
  const [left, top, right, bottom] = chunk.bbox_norm;

  // Calculate pixel positions
  const style = {
    left: `${left * pageWidth * scale}px`,
    top: `${top * pageHeight * scale}px`,
    width: `${(right - left) * pageWidth * scale}px`,
    height: `${(bottom - top) * pageHeight * scale}px`,
  };

  // 청크 타입별 색상 설정
  const getChunkColors = () => {
    const baseClasses = 'absolute border-2 transition-all cursor-pointer group';
    
    if (isPinned) {
      return {
        text: 'border-green-500 bg-green-200 bg-opacity-40',
        image: 'border-purple-500 bg-purple-200 bg-opacity-40', 
        table: 'border-orange-500 bg-orange-200 bg-opacity-40',
      }[chunk.chunk_type];
    }
    
    if (isHovered) {
      return {
        text: 'border-blue-500 bg-blue-200 bg-opacity-30',
        image: 'border-purple-400 bg-purple-200 bg-opacity-30',
        table: 'border-orange-400 bg-orange-200 bg-opacity-30',
      }[chunk.chunk_type];
    }
    
    return {
      text: 'border-blue-400 bg-blue-100 bg-opacity-20',
      image: 'border-purple-300 bg-purple-100 bg-opacity-20',
      table: 'border-orange-300 bg-orange-100 bg-opacity-20',
    }[chunk.chunk_type];
  };

  return (
    <div
      className={classNames(
        'absolute border-2 transition-all cursor-pointer group',
        getChunkColors()
      )}
      style={style}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => togglePinChunk(chunk.chunk_id)}
    >
      <button
        className={classNames(
          'absolute -top-8 right-0 px-2 py-1 text-xs font-medium rounded shadow-sm transition-all',
          'flex items-center gap-1',
          {
            'bg-white text-gray-700 hover:bg-gray-50': !isPinned,
            'bg-green-500 text-white hover:bg-green-600': isPinned && chunk.chunk_type === 'text',
            'bg-purple-500 text-white hover:bg-purple-600': isPinned && chunk.chunk_type === 'image',
            'bg-orange-500 text-white hover:bg-orange-600': isPinned && chunk.chunk_type === 'table',
            'opacity-0 group-hover:opacity-100': !isPinned,
          },
        )}
      >
        <Pin className="w-3 h-3" />
        {isPinned ? '인용됨' : `+ ${chunk.chunk_type === 'text' ? '텍스트' : chunk.chunk_type === 'image' ? '이미지' : '테이블'}`}
      </button>
      {chunk.label && (
        <div className="absolute -bottom-6 left-0 px-1 py-0.5 text-xs bg-gray-800 text-white rounded">
          {chunk.label}
        </div>
      )}
    </div>
  );
} 