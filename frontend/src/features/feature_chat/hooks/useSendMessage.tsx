import { useMutation, useQueryClient, UseMutationResult } from "react-query";
import { ChatHttpService } from "../services";

// Define the payload for sending a message
export interface SaveMessagePayload {
  prompt: string;
  conversation_id?: string;
  use_web_search?: boolean;
}

// Define the expected response type from the saveMessage call.
// Replace `any` with the actual type if available.
export type SaveMessageResponse = any;

/**
 * A custom hook for sending a message to the server.
 * @returns {UseMutationResult<SaveMessageResponse, unknown, SaveMessagePayload>} 
 *   The mutation object from react-query that includes properties like mutate, isLoading, isError, etc.
 */
function useSendMessage(): UseMutationResult<SaveMessageResponse, unknown, SaveMessagePayload> {
  const queryClient = useQueryClient();

  const mutation = useMutation<SaveMessageResponse, unknown, SaveMessagePayload>(
    (payload: SaveMessagePayload) => ChatHttpService.sendMessage(payload),
    {
      onSuccess: (data, variables, context) => {
        queryClient.invalidateQueries("messages_list");



      },
      onError: (error, variables, context) => {
        console.error("Error saving message:", error);
      },
    }
  );

  return mutation;
}

export default useSendMessage;
