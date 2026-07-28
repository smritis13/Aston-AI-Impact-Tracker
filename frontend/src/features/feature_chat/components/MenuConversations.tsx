import React from "react";
import { Link } from "react-router-dom";
import useChatMessagesList from "../hooks/ChatMessagesList";
import useConversationsList from "../hooks/UseConversationsList";

type Props = {};

function MenuConversations({}: Props) {

    const { data, isLoading, isError } = useConversationsList({ page: 1, pageSize: 30 });

  return (
    <>
      <li className="slide">
        {Array.isArray(data) && data.map((conversation:any) => (
            <Link key={conversation.conversation_id+'conv'} to={`/chat/${conversation.conversation_id}`} className="side-menu__item">
                <span className="side-menu__label eclipse">{conversation.title ?? 'New Chat'}</span>
            </Link>
        ))}
      </li>
    </>
  );
}

export default MenuConversations;
