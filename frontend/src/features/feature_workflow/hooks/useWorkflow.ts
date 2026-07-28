import { useQuery, UseQueryResult } from "react-query";
import { WorkflowHttpService } from "../services/WorkflowHttpService";

function useWorkflow(id: string | undefined): UseQueryResult<any, unknown> {
  return useQuery<any, unknown>(
    ["workflow", id],
    () => {
      if (!id) throw new Error("Workflow ID is required");
      return WorkflowHttpService.loadWorkflow(id);
    },
    {
      enabled: !!id,
      onSuccess: (data) => {
        console.log("Loaded Workflow:", data);
      },
    }
  );
}

export default useWorkflow; 