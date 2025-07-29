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
  const { pinnedChunks, togglePinChunk, isCitationMode } = useAppStore();
  const [isHovered, setIsHovered] = React.useState(false);

  const isPinned = pinnedChunks.includes(chunk.chunk_id);
  
  // 페이지 크기가 유효하지 않으면 렌더링하지 않음
  if (pageWidth <= 0 || pageHeight <= 0) {
    console.warn(`⚠️ Invalid page size for chunk ${chunk.chunk_id}: ${pageWidth}x${pageHeight}`);
    return null;
  }

  // 이전 파란색 박스 방식으로 복원 (200% 확대시 완벽했던 방식)
  // chunk.bbox_norm을 사용하고 2배 스케일 적용
  const [left, top, right, bottom] = chunk.bbox_norm;
  
  // 2배 스케일을 고정으로 적용 (사용자 확대/축소와 무관)
  const effectiveScale = 2;
  
  const style = {
    position: 'absolute' as const,
    left: `${left * pageWidth * effectiveScale}px`,
    top: `${top * pageHeight * effectiveScale}px`,
    width: `${(right - left) * pageWidth * effectiveScale}px`,
    height: `${(bottom - top) * pageHeight * effectiveScale}px`,
  };
  
  console.log(`🎯 Chunk ${chunk.chunk_id} (BLUE BOX METHOD WITH FIXED 2X SCALE):`);
  console.log(`  📐 Frontend page size: ${pageWidth}x${pageHeight}, scale: ${scale}`);
  console.log(`  🔄 bbox_norm: [${left.toFixed(4)}, ${top.toFixed(4)}, ${right.toFixed(4)}, ${bottom.toFixed(4)}]`);
  console.log(`  🔵 Fixed scale (2x): ${effectiveScale}`);
  console.log(`  ✅ Final pixels: left=${(left * pageWidth * effectiveScale).toFixed(1)}px, top=${(top * pageHeight * effectiveScale).toFixed(1)}px, width=${((right - left) * pageWidth * effectiveScale).toFixed(1)}px, height=${((bottom - top) * pageHeight * effectiveScale).toFixed(1)}px`);
  if (chunk.bbox_pixels) {
    console.log(`  📊 Compare with backend pixels: [${chunk.bbox_pixels.join(', ')}] (page: ${chunk.page_width}x${chunk.page_height})`);
  }

  // 청크 타입별 색상 설정
  const getChunkColors = () => {
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

  const handleChunkClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    
    // 인용 모드가 활성화되어 있을 때만 클릭 동작
    if (!isCitationMode) {
      console.log(`🚫 Citation mode is disabled, ignoring click on chunk ${chunk.chunk_id}`);
      return;
    }
    
    console.log(`🖱️ Chunk ${chunk.chunk_id} clicked! Current pinned state: ${isPinned}`);
    togglePinChunk(chunk.chunk_id);
    console.log(`✅ togglePinChunk called for ${chunk.chunk_id}`);
  };

  return (
    <div
      className={`absolute border-2 transition-all group ${getChunkColors()} ${
        isCitationMode ? 'cursor-pointer' : 'cursor-default'
      }`}
      style={{
        left: style.left,
        top: style.top,
        width: style.width,
        height: style.height,
        zIndex: 1000, // 높은 z-index 설정
        pointerEvents: 'auto', // 클릭 이벤트 활성화
      }}
      onMouseEnter={() => {
        setIsHovered(true);
        console.log(`🖱️ Mouse entered chunk ${chunk.chunk_id}`);
      }}
      onMouseLeave={() => {
        setIsHovered(false);
        console.log(`🖱️ Mouse left chunk ${chunk.chunk_id}`);
      }}
      onClick={handleChunkClick}
    >
      {/* 인용 모드가 활성화되어 있을 때만 버튼 표시 */}
      {isCitationMode && (
        <button
          className={`absolute -top-8 right-0 p-1 rounded shadow-sm transition-all ${
            isPinned 
              ? 'bg-green-500 text-white hover:bg-green-600' 
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
          style={{
            zIndex: 1001, // 버튼의 z-index를 더 높게
          }}
          onClick={handleChunkClick}
        >
          <Pin className="w-3 h-3" />
        </button>
      )}
    </div>
  );
} 