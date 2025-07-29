import { create } from 'zustand';
import type { ChunkInfo, Message } from '../types';
import type { ExistingFile } from '../api/upload';

interface AppState {
  // PDF state
  fileId: string | null;
  pdfUrl: string | null;
  filename: string | null;
  pages: number | null;
  currentPage: number;

  // Chunks state
  chunks: ChunkInfo[];
  pinnedChunks: string[];
  hasBBox: boolean;

  // Citation mode state
  isCitationMode: boolean;

  // Chat state
  messages: Message[];
  isStreaming: boolean;

  // Existing files state
  existingFiles: ExistingFile[];
  isLoadingFiles: boolean;

  // Actions
  setPdfData: (fileId: string, pdfUrl: string, filename: string, pages: number | null) => void;
  setCurrentPage: (page: number) => void;
  setChunks: (chunks: ChunkInfo[]) => void;
  togglePinChunk: (chunkId: string) => void;
  togglePageCitation: (page: number) => void;  // 페이지 전체 인용 토글로 변경
  clearPinnedChunks: () => void;
  setCitationMode: (enabled: boolean) => void;  // 인용 모드 토글
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  setExistingFiles: (files: ExistingFile[]) => void;
  setIsLoadingFiles: (loading: boolean) => void;
  loadExistingFile: (file: ExistingFile) => void;
  reset: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  fileId: null,
  pdfUrl: null,
  filename: null,
  pages: null,
  currentPage: 1,
  chunks: [],
  pinnedChunks: [],
  hasBBox: false,
  isCitationMode: false,
  messages: [],
  isStreaming: false,
  existingFiles: [],
  isLoadingFiles: false,

  // Actions
  setPdfData: (fileId, pdfUrl, filename, pages) =>
    set({
      fileId,
      pdfUrl,
      filename,
      pages,
      currentPage: 1,
      chunks: [],
      pinnedChunks: [],
      hasBBox: false,
    }),

  setCurrentPage: (page) => set({ currentPage: page }),

  setChunks: (chunks) =>
    set({
      chunks,
      hasBBox: chunks.length > 0,
    }),

  togglePinChunk: (chunkId) =>
    set((state) => ({
      pinnedChunks: state.pinnedChunks.includes(chunkId)
        ? state.pinnedChunks.filter((id) => id !== chunkId)
        : [...state.pinnedChunks, chunkId],
    })),

  togglePageCitation: (page: number) => {
    const state = get();
    const pageChunks = state.chunks.filter((chunk) => chunk.page === page);
    const pageChunkIds = pageChunks.map((chunk) => chunk.chunk_id);
    
    // 페이지의 모든 청크가 이미 인용되어 있는지 확인
    const allPageChunksPinned = pageChunkIds.every(id => state.pinnedChunks.includes(id));
    
    if (allPageChunksPinned) {
      // 페이지 전체 인용 해제
      const newPinnedChunks = state.pinnedChunks.filter(id => !pageChunkIds.includes(id));
      set({ pinnedChunks: newPinnedChunks });
    } else {
      // 페이지 전체 인용 추가
      const newPinnedChunks = [...new Set([...state.pinnedChunks, ...pageChunkIds])];
      set({ pinnedChunks: newPinnedChunks });
    }
  },

  setCitationMode: (enabled) => set({ isCitationMode: enabled }),

  clearPinnedChunks: () => set({ pinnedChunks: [] }),

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: Date.now().toString(),
          timestamp: new Date(),
        },
      ],
    })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) => (msg.id === id ? { ...msg, ...updates } : msg)),
    })),

  setIsStreaming: (isStreaming) => set({ isStreaming }),

  setExistingFiles: (files) => set({ existingFiles: files }),

  setIsLoadingFiles: (loading) => set({ isLoadingFiles: loading }),

  loadExistingFile: (file) => {
    const pdfUrl = `http://localhost:9000${file.download_url}`;
    set({
      fileId: file.file_id,
      pdfUrl,
      filename: file.filename,
      pages: file.pages,
      currentPage: 1,
      chunks: [],
      pinnedChunks: [],
      hasBBox: false,
    });
  },

  reset: () =>
    set({
      fileId: null,
      pdfUrl: null,
      filename: null,
      pages: null,
      currentPage: 1,
      chunks: [],
      pinnedChunks: [],
      hasBBox: false,
      messages: [],
      isStreaming: false,
    }),
})); 