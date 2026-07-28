import { useQuery, UseQueryResult } from "react-query";
import { WorkflowHttpService } from "../services/WorkflowHttpService";

export interface Workflow {
  id: number;
  name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

function useWorkflows(): UseQueryResult<any, unknown> {
  return useQuery<any, unknown>(
    ["workflows"],
    () => WorkflowHttpService.loadWorkflows(),
    {
      onSuccess: (data) => {
        console.log("Loaded Workflows:", data);
      },
    }
  );
}

export default useWorkflows; 