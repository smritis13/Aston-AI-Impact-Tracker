import React, { useEffect, useState } from 'react';
import Pusher from 'pusher-js';

interface PusherListenerProps {
  conversationId?: string;
  streamKey?: string;
  onThoughtReceived: (thought: string) => void;
  onUseCaseReceived?: (useCase: any) => void;  // Optional callback for use cases
  onProgress?: (progress: number) => void; // Optional callback for progress
  onComplete?: (status: 'success' | 'stopped' | 'error', message?: string) => void; // Optional callback for completion
}

// Utility to decode Unicode escapes (e.g., \u2139 → ℹ)
function decodeUnicodeEscapes(str: string): string {
  return str.replace(/\\u([0-9a-fA-F]{4})/g, (_match, grp) => String.fromCharCode(parseInt(grp, 16)));
}

const PusherListener: React.FC<PusherListenerProps> = ({ conversationId, streamKey, onThoughtReceived, onUseCaseReceived, onProgress, onComplete }) => {
  const [thoughts, setThoughts] = useState<string[]>([]);
  const [progress, setProgress] = useState<number>(0);

  useEffect(() => {

    if (!conversationId && !streamKey) return;

    // Initialize Pusher
    const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY || 'defbc8c80d248ea09e11', {
      cluster: process.env.REACT_APP_PUSHER_CLUSTER || 'eu',
    });

    // Determine channel name based on props
    const channelName = conversationId 
      ? `conversation-${conversationId}`
      : `stream-${streamKey}`;

    console.log('Subscribing to channel:', channelName);

    // Subscribe to the channel
    const channel = pusher.subscribe(channelName);

    // Listen for stream_thought events
    channel.bind('stream_thought', (data: { thought: string, progress: number }) => {
      let thought = data.thought;
      const progress = data?.progress || 0;
      // console.log('Received thought:', thought);
      if(progress && onProgress) {
        onProgress(progress);
      }

      // Decode Unicode escapes in the thought string
      thought = decodeUnicodeEscapes(thought);

      // Check if the thought contains a use case
      const useCaseMatch = thought.match(/<usecase>(.*?)<\/usecase>/)?.[1];
      if (useCaseMatch) {
        if(onUseCaseReceived) {
          try {
            // Convert Python-style JSON to valid JavaScript JSON
            const sanitizedJson = useCaseMatch
              // replace keys written as 'key': …   →  "key": …
              .replace(/'([^']+?)':/g, '"$1":')
              // wrap single-quoted values in double quotes & escape inner quotes
              .replace(/:\s*'([^']*)'/g, (_, v) => ':"' + v.replace(/"/g, '\\"') + '"')
              // simple literals
              .replace(/\bNone\b/g, 'null')
              .replace(/\bTrue\b/g, 'true')
              .replace(/\bFalse\b/g, 'false');

            const useCaseData = JSON.parse(sanitizedJson);
            console.log('Extracted use case:', useCaseData);
            onUseCaseReceived(useCaseData);
          } catch (e) {
            console.error('Failed to parse use case data:', e);
            console.error('Original use case string:', useCaseMatch);
          }
        }
      } else {
        // Check for completion messages (use startsWith since failure/success
        // messages may carry extra detail appended after the canonical prefix)
        if (onComplete) {
          const trimmedThought = thought.trim();
          if (trimmedThought.startsWith('Search completed successfully!')) {
            onComplete('success', trimmedThought);
          } else if (trimmedThought.startsWith('Search stopped by user request.')) {
            onComplete('stopped', trimmedThought);
          } else if (trimmedThought.startsWith('Search failed due to an error')) {
            onComplete('error', trimmedThought);
          }
        }
        // Handle as regular thought
        setThoughts(prevThoughts => [...prevThoughts, thought]);
        onThoughtReceived(thought);
      }
    });

    // Cleanup on unmount
    return () => {
      try {
        // Safely unsubscribe from the channel
        if (channel) {
          try {
            channel.unbind_all();
            channel.unsubscribe();
          } catch (e) {
            console.error('Error unsubscribing from channel:', e);
          }
        }
        
        // Safely disconnect Pusher
        if (pusher) {
          try {
            pusher.disconnect();
          } catch (e) {
            console.error('Error disconnecting Pusher:', e);
          }
        }
      } catch (error) {
        console.error('Error during Pusher cleanup:', error);
      }
    };
  }, [conversationId, streamKey, onThoughtReceived, onUseCaseReceived, onProgress, onComplete]);

  return null;
};

export default PusherListener; 
