import { config } from '../config';
import type { QueryRequest, QueryStreamChunk } from '../types';

export const chatApi = {
  async* streamQuery(request: QueryRequest): AsyncGenerator<QueryStreamChunk, void, unknown> {
    console.log('Sending query request:', request);
    
    try {
      const response = await fetch(`${config.queryApiUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Query API error:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle regular JSON response (not SSE for now)
      const data = await response.json();
      console.log('Received response:', data);
      
      if (data.success && data.answer) {
        // Simulate streaming by yielding the full answer at once
        yield {
          content: data.answer,
          done: false,
        };
        
        // Send done signal
        yield {
          done: true,
          pages: [], // Backend doesn't provide pages yet
        };
      } else {
        throw new Error(data.error || 'Unknown error occurred');
      }
    } catch (error) {
      console.error('Chat API error:', error);
      throw error;
    }
  },
}; 