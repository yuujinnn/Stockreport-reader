import React from 'react';
import { User, Bot, AlertCircle } from 'lucide-react';
import { Message } from '../../types';
import classNames from 'classnames';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isError = message.status === 'error';

  return (
    <div className={classNames('flex gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <Bot className="w-5 h-5 text-blue-600" />
          </div>
        </div>
      )}

      <div
        className={classNames(
          'max-w-[70%] rounded-lg px-4 py-2',
          isUser
            ? 'bg-gray-100 text-gray-900'
            : isError
            ? 'bg-red-50 text-red-900 border border-red-200'
            : 'bg-white border border-gray-200',
        )}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* Page references */}
        {message.pages && message.pages.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.pages.map((page) => (
              <span
                key={page}
                className="inline-block px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded"
              >
                p.{page}
              </span>
            ))}
          </div>
        )}

        {/* Error indicator */}
        {isError && (
          <div className="mt-2 flex items-center gap-1 text-sm text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span>오류 발생</span>
          </div>
        )}

        {/* Timestamp */}
        <div className="mt-1 text-xs text-gray-500">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
            <User className="w-5 h-5 text-gray-600" />
          </div>
        </div>
      )}
    </div>
  );
} 