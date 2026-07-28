import React from 'react';
import { Link } from 'react-router-dom';
import useConversationsList from '../hooks/UseConversationsList';

interface ConversationHistoryProps {
  onSelect?: (conversationId: string) => void;
}

const ConversationHistory: React.FC<ConversationHistoryProps> = ({ onSelect }) => {
  const { data, isLoading, isError } = useConversationsList({ page: 1, pageSize: 30 });

  if (isLoading) {
    return <div className="p-3">Loading conversations...</div>;
  }

  if (isError) {
    return <div className="p-3 text-danger">Error loading conversations</div>;
  }

  return (
    <div className="conversation-history">
      <div className="list-group">
        {Array.isArray(data) && data.map((conversation: any) => (
          <Link
            key={conversation.conversation_id}
            to={`/chat/${conversation.conversation_id}`}
            className="list-group-item list-group-item-action"
            onClick={() => onSelect && onSelect(conversation.conversation_id)}
          >
            <div className="d-flex w-100 justify-content-between">
              <h6 className="mb-1 text-truncate">{conversation.title ?? 'New Chat'}</h6>
              <small className="text-muted">
                {new Date(conversation.created_at).toLocaleDateString()}
              </small>
            </div>
            <p className="mb-1 text-muted small text-truncate">
              {conversation.last_message ?? 'No messages yet'}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default ConversationHistory; 
