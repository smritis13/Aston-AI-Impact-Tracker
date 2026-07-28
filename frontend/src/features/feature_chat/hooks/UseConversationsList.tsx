import { useQuery, UseQueryResult } from "react-query";
import { ChatHttpService } from "../services";

interface ConversationsListProps {
  page?: number;
  pageSize?: number;
}

type ConversationsData = any[];

const normalizeConversations = (response: any): ConversationsData => {
  if (Array.isArray(response)) {
    return response;
  }

  if (Array.isArray(response?.data)) {
    return response.data;
  }

  if (Array.isArray(response?.data?.results)) {
    return response.data.results;
  }

  if (Array.isArray(response?.results)) {
    return response.results;
  }

  return [];
};

function useConversationsList({
  page = 1,
  pageSize = 30,
}: ConversationsListProps): UseQueryResult<ConversationsData, unknown> {
  return useQuery<ConversationsData, unknown>(
    ["conversations_list", page, pageSize],
    async () => {
      const response = await ChatHttpService.loadConversations({ page, pageSize });
      return normalizeConversations(response);
    },
    {
      onSuccess: (data) => {
        // You can perform side effects with the loaded data here.
        // For example: console.log("Loaded conversations:", data);
      },
    }
  );
}

export default useConversationsList;
