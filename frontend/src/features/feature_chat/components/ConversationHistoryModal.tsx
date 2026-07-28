import React from 'react';
import CustomModal from 'core/components/shared/CustomModal';
import ConversationHistory from './ConversationHistory';

interface ConversationHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect?: (conversationId: string) => void;
}

const ConversationHistoryModal: React.FC<ConversationHistoryModalProps> = ({
  isOpen,
  onClose,
  onSelect,
}) => {
  return (
    <CustomModal
      isOpen={isOpen}
      onClose={onClose}
      title="Conversation History"
      size="lg"
      showFooter={false}
    >
      <div className="conversation-history-modal">
        {isOpen && (
          <ConversationHistory onSelect={(conversationId) => {
            onSelect?.(conversationId);
            onClose();
          }} />
        )}
      </div>
    </CustomModal>
  );
};

export default ConversationHistoryModal; 
