import MarkdownRenderer from "core/components/shared/MarkdownRenderer";
import React from "react";
import { ChatMessageButtons } from "./ChatMessageButtons";
import References from "./ReferencesWidget";

export interface Reference {
  title: string;
  url: string;
  file_type?: string;
  server_url?: string;
}

interface ChatMessage {
  id: number;
  text: string;
  sender: "user" | "system";
  references?: Reference[]
}

interface ChatMessageItemProps {
  message: ChatMessage;
  isLastMessage: boolean;

}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  isLastMessage,
}) => {
  const messageClass =
    message.sender === "user" ? "user-message" : "system-message";

  // Determine icon visibility class: always-visible for the last user message, hover-only otherwise.
  const iconsVisibilityClass =
    message.sender === "system" && isLastMessage ? "always-visible" : "hover-only";

  return (
    <div id={`message_${message.id}`} className={messageClass}>
      <div className="message-body">
        <p className="mb-0">
          <MarkdownRenderer markdownText={message.text} />
        </p>
        <ChatMessageButtons
            message={message}
            iconsVisibilityClass={iconsVisibilityClass}
          />

        {message && message.references && message.references.length > 0 && (<References references={message.references} />)}
      </div>
    </div>
  );
};
