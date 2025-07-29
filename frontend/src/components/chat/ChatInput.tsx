import React, { useState } from 'react';
import { Send } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { chatApi } from '../../api/chat';

interface ChatInputProps {
  disabled?: boolean;
}

export function ChatInput({ disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const { fileId, filename, pinnedChunks, addMessage, updateMessage, setIsStreaming, messages } = useAppStore();

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || disabled) return;

    const userMessage = input.trim();
    setInput('');

    // 어시스턴트 메시지 ID를 미리 생성
    const assistantMessageId = `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Add user message
    addMessage({
      role: 'user',
      content: userMessage,
      status: 'sent',
    });

    // Create assistant message with pre-generated ID
    addMessage({
      role: 'assistant',
      content: '',
      status: 'sending',
    });

    // 어시스턴트 메시지 ID를 안전하게 가져오기 (새로 추가된 마지막 메시지)
    // 약간의 지연을 두고 상태가 업데이트된 후 ID를 가져옴
    setTimeout(() => {
      const currentMessages = useAppStore.getState().messages;
      const lastAssistantMessage = currentMessages
        .filter(msg => msg.role === 'assistant')
        .pop();
      
      if (!lastAssistantMessage) {
        console.error('❌ Assistant message not found');
        return;
      }

      const actualAssistantMessageId = lastAssistantMessage.id;
      console.log(`🤖 Using assistant message ID: ${actualAssistantMessageId}`);

      setIsStreaming(true);

      // 스트리밍 처리를 별도 함수로 분리
      handleStreaming(userMessage, actualAssistantMessageId);
    }, 50); // 50ms 지연으로 상태 업데이트 보장
  };

  const handleStreaming = async (userMessage: string, assistantMessageId: string) => {
    try {
      let accumulatedContent = '';
      let pages: number[] = [];

      for await (const chunk of chatApi.streamQuery({
        query: userMessage,
        pinChunks: pinnedChunks.length > 0 ? pinnedChunks : undefined,
        fileId: fileId || undefined,
        pdfFilename: filename || undefined,
      })) {
        if (chunk.content) {
          accumulatedContent += chunk.content;
          updateMessage(assistantMessageId, {
            content: accumulatedContent,
            status: 'sending',
          });
        }

        if (chunk.done && chunk.pages) {
          pages = chunk.pages;
        }

        if (chunk.error) {
          throw new Error(chunk.error);
        }
      }

      // Final update
      updateMessage(assistantMessageId, {
        content: accumulatedContent,
        pages,
        status: 'sent',
      });
    } catch (error) {
      updateMessage(assistantMessageId, {
        content: 'Error: ' + (error instanceof Error ? error.message : 'Unknown error'),
        status: 'error',
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      // Enter만 눌렀을 때: 전송
      e.preventDefault();
      handleSubmit();
    }
    // Shift + Enter: 줄바꿈 (기본 동작 유지)
  };

  return (
    <form onSubmit={handleSubmit} className="mt-4">
      <div className="flex gap-2 items-end">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={disabled ? '응답을 기다리는 중...' : '질문을 입력하세요... (Shift + Enter: 줄바꿈, Enter: 전송)'}
          rows={3}
          className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 resize-none overflow-y-auto min-h-[76px] max-h-[120px]"
          style={{ lineHeight: '1.5' }}
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex-shrink-0"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
      <div className="mt-1 text-xs text-gray-500">
        <kbd className="px-1 py-0.5 bg-gray-100 border rounded text-xs">Shift</kbd> + 
        <kbd className="px-1 py-0.5 bg-gray-100 border rounded text-xs ml-1">Enter</kbd> 줄바꿈 | 
        <kbd className="px-1 py-0.5 bg-gray-100 border rounded text-xs ml-2">Enter</kbd> 전송
      </div>
    </form>
  );
} 