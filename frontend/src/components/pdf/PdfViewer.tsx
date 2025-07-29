import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, BookmarkPlus } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { ChunkOverlay } from './ChunkOverlay';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker - use LOCAL worker file to avoid CDN issues
if (typeof window !== 'undefined') {
  try {
    // Use local worker file served by Vite (copied from node_modules)
    // For pdfjs-dist 5.3.31, use the .min.mjs extension
    pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';
    
    console.log('PDF worker configured (LOCAL):', pdfjs.GlobalWorkerOptions.workerSrc);
    console.log('PDF.js version:', pdfjs.version);
  } catch (error) {
    console.error('Failed to configure PDF worker:', error);
  }
}

export function PdfViewer() {
  const { pdfUrl, pages, currentPage, setCurrentPage, chunks, pinAllChunksInPage } = useAppStore();
  const [scale, setScale] = useState(1.0);
  const [numPages, setNumPages] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pageSize, setPageSize] = useState<{ width: number; height: number }>({ width: 0, height: 0 });

  console.log('PdfViewer render - pdfUrl:', pdfUrl);

  if (!pdfUrl) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-500 text-lg mb-2">PDF를 업로드해주세요</p>
          <p className="text-gray-400 text-sm">PDF 파일을 드래그하거나 클릭하여 업로드하세요</p>
        </div>
      </div>
    );
  }

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= numPages) {
      setCurrentPage(newPage);
    }
  };

  const handleZoom = (delta: number) => {
    setScale(prev => Math.max(0.5, Math.min(2.0, prev + delta)));
  };

  const onDocumentLoadSuccess = ({ numPages: totalPages }: { numPages: number }) => {
    console.log('✅ PDF loaded successfully! Total pages:', totalPages);
    setNumPages(totalPages);
    setLoading(false);
    setError(null);
  };

  const onDocumentLoadError = (error: any) => {
    console.error('❌ PDF load error:', error);
    setError(`PDF 로드 오류: ${error?.message || '알 수 없는 오류'}`);
    setLoading(false);
  };

  const onPageLoadSuccess = (page: any) => {
    console.log('✅ Page loaded successfully:', page.pageNumber);
    console.log('📐 Page dimensions - Original:', page.originalWidth, 'x', page.originalHeight);
    console.log('📐 Page dimensions - Rendered:', page.width, 'x', page.height);
    
    // 실제 렌더링된 크기를 사용 (스케일 적용된 크기)
    setPageSize({
      width: page.width,
      height: page.height
    });
  };

  const onPageLoadError = (error: any) => {
    console.error('❌ Page load error:', error);
  };

  const currentPageChunks = chunks.filter((chunk: any) => chunk.page === currentPage);
  
  // 현재 페이지 청크 통계
  const chunkStats = currentPageChunks.reduce((acc, chunk) => {
    acc[chunk.chunk_type] = (acc[chunk.chunk_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // 디버깅 로그
  useEffect(() => {
    console.log(`📖 PdfViewer - Page ${currentPage}: ${chunks.length} total chunks, ${currentPageChunks.length} on current page`);
    if (currentPageChunks.length > 0) {
      console.log(`📊 Current page chunk stats:`, chunkStats);
      console.log(`📋 Current page chunks:`, currentPageChunks);
    }
  }, [currentPage, chunks.length, currentPageChunks.length, chunkStats]);

  return (
    <div className="flex-1 flex flex-col bg-gray-100">
      {/* Controls */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="p-2 rounded-md bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm font-medium">
              {currentPage} / {numPages || pages || '?'}
            </span>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage >= numPages}
              className="p-2 rounded-md bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* 청크 통계 및 페이지 전체 인용 */}
          {currentPageChunks.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="text-xs text-gray-600">
                청크: {currentPageChunks.length}개
                {chunkStats.text && ` (텍스트 ${chunkStats.text})`}
                {chunkStats.image && ` (이미지 ${chunkStats.image})`}
                {chunkStats.table && ` (테이블 ${chunkStats.table})`}
              </div>
              <button
                onClick={() => pinAllChunksInPage(currentPage)}
                className="flex items-center gap-1 px-3 py-1 text-xs bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
              >
                <BookmarkPlus className="w-3 h-3" />
                페이지 전체 인용
              </button>
            </div>
          )}
          
          {/* 줌 컨트롤 */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleZoom(-0.2)}
              className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-sm font-medium min-w-[60px] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={() => handleZoom(0.2)}
              className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="flex justify-center">
          {error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md text-center">
              <p className="text-red-800 font-medium mb-2">PDF 로딩 오류</p>
              <p className="text-red-600 text-sm">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                페이지 새로고침
              </button>
            </div>
          ) : (
            <div className="relative">
              <Document
                file={pdfUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading={
                  <div className="flex items-center justify-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-3 text-gray-600">PDF 로딩 중...</span>
                  </div>
                }
                error={
                  <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                    <p className="text-red-800 font-medium">PDF를 로드할 수 없습니다</p>
                    <p className="text-red-600 text-sm mt-1">파일이 손상되었거나 지원되지 않는 형식일 수 있습니다</p>
                  </div>
                }
              >
                <div className="relative">
                  <Page
                    pageNumber={currentPage}
                    scale={scale}
                    onLoadSuccess={onPageLoadSuccess}
                    onLoadError={onPageLoadError}
                    renderTextLayer={true}
                    renderAnnotationLayer={true}
                  />
                  
                  {/* Chunk overlays */}
                  {currentPageChunks.map((chunk: any) => (
                    <ChunkOverlay
                      key={chunk.chunk_id}
                      chunk={chunk}
                      pageWidth={pageSize.width}
                      pageHeight={pageSize.height}
                      scale={scale}
                    />
                  ))}
                </div>
              </Document>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 