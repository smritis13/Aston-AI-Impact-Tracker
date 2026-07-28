import MainLayout from "core/components/layout/MainLayout";
import React, { useEffect, useState } from "react";
import Composer from "../components/Composer";
import useChatMessagesList from "../hooks/ChatMessagesList";
import { useQueryClient } from "react-query";
import ChatLayout from "core/components/layout/ChatLayout";
import { useParams } from "react-router-dom";
import { ChatMessageItem } from "../components/ChatMessageItem";
import PusherListener from "../components/PusherListener";

// Define the shape of a single chat message.
interface ChatMessage {
  id: number;
  text: string;
  sender: "user" | "system";
}

type Props = {};

const ChatPage = (props: Props) => {
  const queryClient = useQueryClient();

  const { conversationId } = useParams<{ conversationId: string }>();

  const { data, isLoading, isError } = useChatMessagesList({ conversationId: conversationId });

  const [thinking, setThinking] = React.useState(false);
  const [currentThought, setCurrentThought] = useState<string>("");
  const [showScrollButton, setShowScrollButton] = React.useState(false);

  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const thoughtTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const { scrollTop, scrollHeight, clientHeight } = target;
    const atBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 10;
    setShowScrollButton(!atBottom);
  };

  useEffect(() => {
    if(!showScrollButton){
      scrollToBottom();
    }
  }, [data?.messages?.length, thinking, currentThought]);

  const handleThoughtReceived = (thought: string) => {
    // Clear any existing timeout
    if (thoughtTimeoutRef.current) {
      clearTimeout(thoughtTimeoutRef.current);
    }
    
    // Set the new thought
    if (!thought.toLowerCase().includes("error")) {
      setCurrentThought(thought);
    }
    
    // Set a timeout to clear the thought after 4 seconds
    thoughtTimeoutRef.current = setTimeout(() => {
      setCurrentThought("");
    }, 10000);
  };

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (thoughtTimeoutRef.current) {
        clearTimeout(thoughtTimeoutRef.current);
      }
    };
  }, []);

  const handleOnMessageSent = (message: string) => {
    const newMessage: ChatMessage = {
      id: Date.now(), // You might want a better id generation strategy.
      text: message,
      sender: "user",
    };
  
    // Update the cached query data by appending the new message.
    queryClient.setQueryData(["messages_list", conversationId], (oldData: any) => {
      if (oldData && oldData.data && Array.isArray(oldData.data.messages)) {
        return {
          ...oldData,
          data: {
            ...oldData.data,
            messages: [...oldData.data.messages, newMessage],
          },
        };
      }
      // If no previous messages exist, return an object with the new message.
      return { data: { messages: [newMessage] } };
    });
    // Optionally, you can also trigger a scroll here:
    scrollToBottom();
  };
  
  const handleThinking = (thinking: boolean) => {
    setThinking(thinking);   
  };

  const handleScrollEnd = () => {
    if (containerRef.current) {
      scrollToBottom();
    }
  };

  const messages: ChatMessage[] = Array.isArray(data?.messages) ? (data?.messages as ChatMessage[]) : [];
  const hasData = messages.length > 0;

  if(isLoading) return (<></>)

  return (
    <ChatLayout>
      <div className="container d-flex justify-content-center">
        <div className={`custom-chat-container position-relative ${(hasData) && 'has-message'} `} >
          <h2 className="mb-4 help-title">What can I help with?</h2>
          <div className="messages" ref={containerRef} onScroll={handleScroll}>
            {isLoading && <p>Loading messages...</p>}
            {isError && <p>Error loading messages.</p>}
            {hasData && (
              messages.map((message: ChatMessage,index : number) => (
                <ChatMessageItem
                    key={message.id}
                    message={message}
                    isLastMessage={index === messages.length - 1}
                  />
              ))
            )}
            {thinking && (
              <div className="thinking-text">
                <i className="bi bi-arrow-repeat spin mr-2"></i>
                {currentThought || "Thinking..."}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          {showScrollButton && (
            <button
              onClick={handleScrollEnd}
              type="button"
              className="btn btn-icon btn-outline-primary rounded-pill chat-go-top-btn"
            >
              {isLoading ? <i className="las la-stop"></i> : <i className="bi bi-arrow-down"></i>}
            </button>
          )}
          <Composer
              conversationId={conversationId}
              onThinking={handleThinking}
              onMessageSent={handleOnMessageSent}
          />
          <PusherListener 
            conversationId={conversationId} 
            onThoughtReceived={handleThoughtReceived} 
          />
        </div>
      </div>
    </ChatLayout>
  );
};

export default ChatPage;
