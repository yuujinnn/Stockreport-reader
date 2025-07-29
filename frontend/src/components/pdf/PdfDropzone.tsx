import React, { useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadApi, type ExistingFile } from '../../api/upload';
import { useAppStore } from '../../store/useAppStore';

export function PdfDropzone() {
  const { 
    setPdfData, 
    existingFiles, 
    isLoadingFiles, 
    setExistingFiles, 
    setIsLoadingFiles,
    loadExistingFile 
  } = useAppStore();

  // 컴포넌트 마운트 시 기존 파일들 로드
  useEffect(() => {
    loadExistingFiles();
  }, []);

  const loadExistingFiles = async () => {
    try {
      setIsLoadingFiles(true);
      const response = await uploadApi.getExistingFiles();
      setExistingFiles(response.files);
    } catch (error) {
      console.error('Error loading existing files:', error);
    } finally {
      setIsLoadingFiles(false);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    try {
      console.log('📤 Uploading file:', file.name);
      const response = await uploadApi.uploadPdf(file);
      
      console.log('✅ Upload successful:', response);
      const pdfUrl = uploadApi.getPdfUrl(response.fileId);
      
      setPdfData(response.fileId, pdfUrl, response.filename, response.pages ?? null);
      
      // 업로드 후 기존 파일 목록 새로고침
      loadExistingFiles();
    } catch (error) {
      console.error('❌ Upload failed:', error);
      alert('파일 업로드에 실패했습니다.');
    }
  }, [setPdfData]);

  const handleExistingFileSelect = (file: ExistingFile) => {
    loadExistingFile(file);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
  });

  const getStatusIcon = (status: ExistingFile['rag_status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusText = (status: ExistingFile['rag_status']) => {
    switch (status) {
      case 'completed':
        return '분석 완료';
      case 'processing':
        return '분석 중';
      default:
        return '분석 대기';
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* 파일 업로드 영역 */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors mb-6
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        {isDragActive ? (
          <p className="text-blue-600 font-medium">PDF 파일을 여기에 놓으세요</p>
        ) : (
          <div>
            <p className="text-gray-600 font-medium mb-2">PDF 파일을 드래그하거나 클릭하여 업로드</p>
            <p className="text-gray-400 text-sm">분석 후 문서 내용을 기반으로 질문할 수 있습니다</p>
          </div>
        )}
      </div>

      {/* 기존 파일 목록 */}
      <div className="flex-1 overflow-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">기존 파일</h3>
          <button
            onClick={loadExistingFiles}
            disabled={isLoadingFiles}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors disabled:opacity-50"
          >
            {isLoadingFiles ? '로딩 중...' : '새로고침'}
          </button>
        </div>

        {isLoadingFiles ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">파일 목록 로딩 중...</span>
          </div>
        ) : existingFiles.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p>아직 업로드된 파일이 없습니다</p>
          </div>
        ) : (
          <div className="space-y-3">
            {existingFiles.map((file) => (
              <div
                key={file.file_id}
                onClick={() => handleExistingFileSelect(file)}
                className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-5 h-5 text-gray-600 flex-shrink-0" />
                      <h4 className="font-medium text-gray-900 truncate">{file.filename}</h4>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>{file.pages} 페이지</span>
                      <span>•</span>
                      <span>{new Date(file.upload_timestamp).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    {getStatusIcon(file.rag_status)}
                    <span className={`text-sm ${
                      file.rag_status === 'completed' ? 'text-green-600' :
                      file.rag_status === 'processing' ? 'text-yellow-600' :
                      'text-gray-500'
                    }`}>
                      {getStatusText(file.rag_status)}
                    </span>
                  </div>
                </div>
                {file.rag_status === 'completed' && (
                  <div className="mt-2 text-xs text-green-600">
                    ✓ 질문하기 준비 완료
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 