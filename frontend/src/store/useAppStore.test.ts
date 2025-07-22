import { describe, it, expect, beforeEach } from 'vitest';
import { useAppStore } from './useAppStore';

describe('useAppStore', () => {
  beforeEach(() => {
    useAppStore.setState({
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
    });
  });

  it('should set PDF data correctly', () => {
    const { setPdfData } = useAppStore.getState();
    
    setPdfData('test-id', 'http://test.pdf', 'test.pdf', 10);
    
    const state = useAppStore.getState();
    expect(state.fileId).toBe('test-id');
    expect(state.pdfUrl).toBe('http://test.pdf');
    expect(state.filename).toBe('test.pdf');
    expect(state.pages).toBe(10);
    expect(state.currentPage).toBe(1);
  });

  it('should toggle pinned chunks', () => {
    const { togglePinChunk } = useAppStore.getState();
    
    togglePinChunk('chunk1');
    expect(useAppStore.getState().pinnedChunks).toContain('chunk1');
    
    togglePinChunk('chunk2');
    expect(useAppStore.getState().pinnedChunks).toEqual(['chunk1', 'chunk2']);
    
    togglePinChunk('chunk1');
    expect(useAppStore.getState().pinnedChunks).toEqual(['chunk2']);
  });

  it('should add messages with generated id and timestamp', () => {
    const { addMessage } = useAppStore.getState();
    
    addMessage({
      role: 'user',
      content: 'Test message',
      status: 'sent',
    });
    
    const messages = useAppStore.getState().messages;
    expect(messages).toHaveLength(1);
    expect(messages[0].id).toBeDefined();
    expect(messages[0].timestamp).toBeDefined();
    expect(messages[0].content).toBe('Test message');
  });

  it('should set chunks and update hasBBox', () => {
    const { setChunks } = useAppStore.getState();
    
    setChunks([
      {
        chunk_id: 'p1_c1',
        page: 1,
        bbox_norm: [0, 0, 0.5, 0.5],
      },
    ]);
    
    const state = useAppStore.getState();
    expect(state.chunks).toHaveLength(1);
    expect(state.hasBBox).toBe(true);
  });

  it('should reset state', () => {
    const { setPdfData, addMessage, reset } = useAppStore.getState();
    
    setPdfData('test-id', 'http://test.pdf', 'test.pdf', 10);
    addMessage({ role: 'user', content: 'Test', status: 'sent' });
    
    reset();
    
    const state = useAppStore.getState();
    expect(state.fileId).toBeNull();
    expect(state.messages).toHaveLength(0);
  });
}); 