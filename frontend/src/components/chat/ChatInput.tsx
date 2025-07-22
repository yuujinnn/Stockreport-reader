import React, { useState } from 'react';
import { Send } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { chatApi } from '../../api/chat';

interface ChatInputProps {
  disabled?: boolean;
}

export function ChatInput({ disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const { fileId, pinnedChunks, addMessage, updateMessage, setIsStreaming, messages } = useAppStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message
    addMessage({
      role: 'user',
      content: userMessage,
      status: 'sent',
    });

    // Create assistant message
    addMessage({
      role: 'assistant',
      content: '',
      status: 'sending',
    });

    // Get the assistant message ID (it's the last message)
    const assistantMessageId = useAppStore.getState().messages[useAppStore.getState().messages.length - 1].id;

    setIsStreaming(true);

    try {
      let accumulatedContent = '';
      let pages: number[] = [];

      for await (const chunk of chatApi.streamQuery({
        query: userMessage,
        pinChunks: pinnedChunks.length > 0 ? pinnedChunks : undefined,
        fileId: fileId || undefined,
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

  return (
    <form onSubmit={handleSubmit} className="mt-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={disabled}
          placeholder={disabled ? '응답을 기다리는 중...' : '질문을 입력하세요...'}
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </form>
  );
} 