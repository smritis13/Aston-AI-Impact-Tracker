import { useQuery, useQueryClient, UseQueryResult } from "react-query";
import { ChatHttpService } from "../services";

interface ChatMessagesListProps {
  size?: number;
  conversationId?: string;
}

type ChatMessagesData = {
  messages: any[];
  [key: string]: any;
};

const normalizeMessages = (response: any): ChatMessagesData => {
  const payload = response?.data ?? response;

  if (payload && typeof payload === "object") {
    return {
      ...payload,
      messages: Array.isArray(payload.messages) ? payload.messages : [],
    };
  }

  return {
    messages: [],
  };
};

function useChatMessagesList({ conversationId, size = 30 }: ChatMessagesListProps): UseQueryResult<ChatMessagesData, unknown> {
  const queryClient = useQueryClient();

  return useQuery<ChatMessagesData, unknown>(
    ["messages_list", conversationId],
    async () => {
      const response = await ChatHttpService.loadMessages({ conversationId });
      return normalizeMessages(response);
    },
    {
      onSuccess: (data) => {
        // console.log(data);
      },
    }
  );
}

export default useChatMessagesList;
