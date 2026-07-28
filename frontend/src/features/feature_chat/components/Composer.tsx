import React, { useEffect, useRef, useState } from "react";
import useSendMessage from "../hooks/useSendMessage";
import { useNavigate } from "react-router-dom";
import SelectTheme from "../../feature_data/components/SelectTheme";

type Props = {
  onThinking: (thinking: boolean) => void;
  onMessageSent: (message: string) => void;
  conversationId?: string;
};

export interface SaveMessagePayload {
  prompt: string;
  conversation_id?: string;
  use_web_search?: boolean;
  deep_research?: boolean;
}

function Composer({ onMessageSent, conversationId, onThinking }: Props) {
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const [prompt, setMessage] = useState("");
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [deepResearch, setDeepResearch] = useState(false);
  const [themeId, setThemeId] = useState<number | null>(null);

  const navigate = useNavigate();
  const { mutate, isLoading, isError } = useSendMessage();

  useEffect(() => {
    textAreaRef.current?.focus();
  }, []);

  const handleSendMessage = () => {
    if (!prompt.trim()) return;

    setMessage("");
    onThinking(true);
    onMessageSent(prompt);

    const payload: SaveMessagePayload & { theme_id?: number | null } = {
      prompt,
      conversation_id: conversationId,
      use_web_search: useWebSearch,
      deep_research: deepResearch,
      theme_id: themeId || undefined,
    };

    mutate(payload, {
      onSuccess: (data) => {
        textAreaRef.current?.focus();
        const conversationId = data.data?.conversation_id;
        if (conversationId && window.location.pathname.includes("chat")) {
          navigate(`/chat/${conversationId}`);
        }
        onThinking(false);
      },
      onError: (error) => {
        console.error("Error sending message:", error);
        onThinking(false);
      },
    });
  };

  const iconButtonClass = (active: boolean) =>
    `d-flex align-items-center gap-2 px-3 py-1 me-2 border rounded-pill 
     ${active ? "border-primary text-primary bg-light" : "border-light text-muted bg-transparent"}`;

  return (
    <div className="composer">
      
      <textarea
        ref={textAreaRef}
        placeholder="Ask me any questions"
        value={prompt}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
          }
        }}
      ></textarea>

      <button
        onClick={handleSendMessage}
        type="button"
        className="btn btn-icon btn-outline-primary rounded-pill composer-send-btn"
        disabled={isLoading || !prompt.trim()}
      >
        {isLoading ? <i className="las la-stop"></i> : <i className="bi bi-arrow-up"></i>}
      </button>

      <div className="mt-2 d-flex flex-wrap align-items-start full-width">
        <button
          className={iconButtonClass(useWebSearch)}
          onClick={() => {setUseWebSearch((prev) => !prev); setDeepResearch(false);}}
          type="button"
        >
          <i className="bi bi-globe"></i>
          <span>Search</span>
        </button>
        <button
          className={iconButtonClass(deepResearch)}
          onClick={() => {setDeepResearch((prev) => !prev); setUseWebSearch(false);}}
          type="button"
        >
          <i className="bi bi-layers"></i>
          <span>Deep Research</span>
        </button>
        <SelectTheme className="composer-select text-muted" value={themeId} onChange={setThemeId} />
      </div>

      {isError && <div className="error mt-2">Failed to send the message.</div>}
    </div>
  );
}

export default Composer;
