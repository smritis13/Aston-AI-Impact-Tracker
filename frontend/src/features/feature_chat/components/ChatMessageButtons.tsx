import React, { useState } from "react";
import Utils from "core/utils";

interface ChatMessage {
  id: number;
  text: string;
  sender: "user" | "system";
}

interface ChatMessageButtonsProps {
  message: ChatMessage;
  iconsVisibilityClass: string;
}

export const ChatMessageButtons: React.FC<ChatMessageButtonsProps> = ({
  message,
  iconsVisibilityClass,
}) => {
  // State for showing temporary check icons for download and copy actions.
  const [activeButton, setActiveButton] = useState<{ [key: string]: boolean }>({});

  // State for like/dislike toggling.
  const [liked, setLiked] = useState(false);
  const [disliked, setDisliked] = useState(false);

  // Helper function to show the check icon for a specific action for 2 seconds.
  const showCheck = (action: string) => {
    setActiveButton((prev) => ({ ...prev, [action]: true }));
    setTimeout(() => {
      setActiveButton((prev) => ({ ...prev, [action]: false }));
    }, 2000);
  };

  // Download handler.
  const onDownload = (message: ChatMessage) => {
    Utils.downloadMessage(message);
    showCheck("download");
  };

  // Copy handler.
  const onCopy = (message: ChatMessage) => {
    Utils.copyMessage(message);
    showCheck("copy");
  };

  // Like handler: toggles the like active state.
  const onLike = (message: ChatMessage) => {
    setLiked((prev) => !prev);
    // If liking, remove dislike if set.
    if (!liked && disliked) {
      setDisliked(false);
    }
    // Utils.likeMessage(message);
  };

  // Dislike handler: toggles the dislike active state.
  const onDislike = (message: ChatMessage) => {
    setDisliked((prev) => !prev);
    // If disliking, remove like if set.
    if (!disliked && liked) {
      setLiked(false);
    }
    // Utils.dislikeMessage(message);
  };

  // Render the buttons only for system messages.
  if (message.sender !== "system") {
    return null;
  }

  return (
    <div className={`message-icons ${iconsVisibilityClass}`}>
      <button
        type="button"
        className="btn btn-light icon-btn"
        onClick={() => onDownload(message)}
      >
        {activeButton["download"] ? (
          <i className="las la-check"></i>
        ) : (
          <i className="las la-download"></i>
        )}
      </button>
      <button
        type="button"
        className="btn btn-light icon-btn"
        onClick={() => onCopy(message)}
      >
        {activeButton["copy"] ? (
          <i className="las la-check"></i>
        ) : (
          <i className="las la-copy"></i>
        )}
      </button>
      <button
        type="button"
        className={`btn btn-light icon-btn ${liked ? "active" : ""}`}
        onClick={() => onLike(message)}
      >
        <i className="las la-thumbs-up"></i>
      </button>
      <button
        type="button"
        className={`btn btn-light icon-btn ${disliked ? "active" : ""}`}
        onClick={() => onDislike(message)}
      >
        <i className="las la-thumbs-down"></i>
      </button>
    </div>
  );
};
