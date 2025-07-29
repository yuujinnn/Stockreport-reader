import React, { useEffect } from 'react';
import { FileText } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { PdfDropzone } from '../pdf/PdfDropzone';
import { PdfViewer } from '../pdf/PdfViewer';
import { ChatPane } from '../chat/ChatPane';
import { useChunks } from '../../hooks/useChunks';

export function MainLayout() {
  const { pdfUrl, filename, fileId } = useAppStore();
  
  // Fetch chunks data
  useChunks();

  // 디버깅: 상태 변화 추적
  useEffect(() => {
    console.log('🏠 MainLayout state:', { fileId, pdfUrl: !!pdfUrl, filename });
  }, [fileId, pdfUrl, filename]);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-semibold">Stockreport Reader</h1>
          </div>
          {filename && (
            <div className="text-sm text-gray-600">
              현재 파일: <span className="font-medium">{filename}</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Left Panel - PDF */}
        <div className="w-1/2 border-r bg-white">
          {pdfUrl ? <PdfViewer /> : (
            <div className="h-full flex items-center justify-center p-8">
              <PdfDropzone />
            </div>
          )}
        </div>

        {/* Right Panel - Chat */}
        <div className="w-1/2">
          <ChatPane />
        </div>
      </div>
    </div>
  );
} 