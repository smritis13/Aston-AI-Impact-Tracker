// src/features/feature_data/components/StreamView.tsx
import React, { useEffect, useState } from 'react';

interface StreamMessage {
  type: 'stream_thought' | 'stream_status' | 'stream_report' | 'stream_batch';
  stream_id: string;
  thought?: string;
  status?: string;
  content?: string;
  thoughts?: string[];
  data?: Record<string, any>;
}

interface StreamViewProps {
  reportId?: number | null;
  streamId: string;
  channelType?: 'thoughts' | 'status' | 'report';
  channelPrefix?: string;
}

const StreamView: React.FC<StreamViewProps> = ({
  reportId = null,
  streamId,
  channelType = 'thoughts',
  channelPrefix,
}) => {
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!streamId) {
      setError('No streamId provided');
      return;
    }

    // Get the current hostname and protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NODE_ENV === 'development' ? 'localhost' : 'backend';
    const port = process.env.NODE_ENV === 'development' ? ':8000' : ':8000';
    
    // Construct the WebSocket URL dynamically
    let wsUrl;
    if (channelPrefix) {
      wsUrl = `${protocol}//${host}${port}/ws/stream/${streamId}/${channelType}/?channel_prefix=${channelPrefix}`;
    } else if (reportId) {
      wsUrl = `${protocol}//${host}${port}/ws/stream/${reportId}/${streamId}/${channelType}/`;
    } else {
      wsUrl = `${protocol}//${host}${port}/ws/stream/${streamId}/${channelType}/`;
    }
    
    console.log('Attempting WebSocket connection to:', wsUrl);
    console.log('Stream ID:', streamId);
    console.log('Report ID:', reportId);
    console.log('Channel Type:', channelType);
    console.log('Channel Prefix:', channelPrefix);

    let socket: WebSocket;
    try {
      socket = new WebSocket(wsUrl);
    } catch (err) {
      console.error('WebSocket creation failed:', err);
      setError(`WebSocket creation failed: ${err}`);
      return;
    }

    socket.onopen = () => {
      console.log(`Connected to ${channelType} channel`);
      setError(null);
    };

    socket.onmessage = (event) => {
      try {
        const data: StreamMessage = JSON.parse(event.data);
        console.log(`Received ${data.type}:`, data);
        setMessages((prev) => [...prev, data]);
      } catch (err) {
        console.error('Failed to parse message:', err);
      }
    };

    socket.onclose = (event) => {
      console.log('Disconnected:', event);
      console.log('Close code:', event.code);
      console.log('Close reason:', event.reason);
      setError(`WebSocket disconnected: code=${event.code}, reason=${event.reason}`);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection failed');
    };

    return () => {
      console.log('Closing WebSocket');
      socket.close();
    };
  }, [reportId, streamId, channelType, channelPrefix]);

  return (
    <div>
      <h1>StreamView</h1>
      <h2>Channel: {channelType}</h2>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      <ul>
        {messages.map((msg, index) => (
          <li key={index}>
            {msg.type}: {JSON.stringify(msg)}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default StreamView;