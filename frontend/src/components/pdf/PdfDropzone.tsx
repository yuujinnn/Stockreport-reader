import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload } from 'lucide-react';
import { uploadApi } from '../../api/upload';
import { useAppStore } from '../../store/useAppStore';

export function PdfDropzone() {
  const { setPdfData } = useAppStore();
  const [isUploading, setIsUploading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setIsUploading(true);
      setError(null);

      try {
        const response = await uploadApi.uploadPdf(file);
        const pdfUrl = uploadApi.getPdfUrl(response.fileId);
        setPdfData(response.fileId, pdfUrl, response.filename, response.pages);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed');
      } finally {
        setIsUploading(false);
      }
    },
    [setPdfData],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: isUploading,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400 bg-gray-50'
      } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} />
      <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
      {isDragActive ? (
        <p className="text-blue-600 font-medium">Drop the PDF here...</p>
      ) : (
        <div>
          <p className="text-gray-600 mb-2">
            {isUploading ? 'Uploading...' : 'Drag & drop a PDF here, or click to select'}
          </p>
          <p className="text-sm text-gray-500">Only PDF files are supported</p>
        </div>
      )}
      {error && <p className="mt-4 text-red-500 text-sm">{error}</p>}
    </div>
  );
} 