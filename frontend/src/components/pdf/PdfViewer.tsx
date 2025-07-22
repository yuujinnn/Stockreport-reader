import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { ChunkOverlay } from './ChunkOverlay';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set worker URL
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

export function PdfViewer() {
  const { pdfUrl, pages, currentPage, setCurrentPage, hasBBox, chunks } = useAppStore();
  const [scale, setScale] = useState(1.0);
  const [pageWidth, setPageWidth] = useState<number>(0);
  const [pageHeight, setPageHeight] = useState<number>(0);

  if (!pdfUrl) return null;

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= (pages || 1)) {
      setCurrentPage(newPage);
    }
  };

  const handleZoom = (delta: number) => {
    setScale((prev) => Math.max(0.5, Math.min(2.0, prev + delta)));
  };

  const currentPageChunks = chunks.filter((chunk) => chunk.page === currentPage);

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Controls */}
      <div className="flex items-center justify-between p-4 bg-white border-b">
        <div className="flex items-center gap-2">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <span className="px-4 py-2 text-sm">
            Page {currentPage} of {pages || '...'}
          </span>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === pages}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={() => handleZoom(-0.1)} className="p-2 rounded hover:bg-gray-100">
            <ZoomOut className="w-5 h-5" />
          </button>
          <span className="px-3 text-sm">{Math.round(scale * 100)}%</span>
          <button onClick={() => handleZoom(0.1)} className="p-2 rounded hover:bg-gray-100">
            <ZoomIn className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="flex justify-center">
          <div className="relative">
            <Document file={pdfUrl} loading={<div>Loading PDF...</div>}>
              <Page
                pageNumber={currentPage}
                scale={scale}
                onLoadSuccess={(page) => {
                  setPageWidth(page.width);
                  setPageHeight(page.height);
                }}
              />
            </Document>

            {/* Chunk Overlays */}
            {hasBBox && pageWidth > 0 && pageHeight > 0 && (
              <div
                className="absolute top-0 left-0"
                style={{
                  width: pageWidth * scale,
                  height: pageHeight * scale,
                }}
              >
                {currentPageChunks.map((chunk) => (
                  <ChunkOverlay
                    key={chunk.chunk_id}
                    chunk={chunk}
                    pageWidth={pageWidth}
                    pageHeight={pageHeight}
                    scale={scale}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 