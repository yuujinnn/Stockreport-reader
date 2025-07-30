import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { ChatInput } from './ChatInput';
import { PinnedChips } from './PinnedChips';
import { MessageBubble } from './MessageBubble';

export function ChatPane() {
  const { messages, isStreaming } = useAppStore();
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 120px)' }}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg mb-2">시작하기</p>
            <p className="text-sm">PDF를 업로드하고 질문을 입력하세요</p>
          </div>
        ) : (
          messages.map((message) => <MessageBubble key={message.id} message={message} />)
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - 더 많은 패딩과 고정 위치 */}
      <div className="border-t bg-white p-6 pb-8">
        <PinnedChips />
        <ChatInput disabled={isStreaming} />
      </div>
    </div>
  );
} 