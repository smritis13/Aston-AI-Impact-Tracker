import { useQuery, UseQueryResult } from "react-query";
import { ContentHttpService } from "../services";



export function useReportThoughts(reportId: number | undefined): UseQueryResult<any> {
  return useQuery<any, unknown>(
    ["report", reportId],
    async () => {
      const data = await ContentHttpService.loadReport(reportId) as any;
      return data;
    },
    {
      enabled: !!reportId,
      // refetchInterval: 1000, // Poll every 100 milliseconds while report is being generated
      onSuccess: (data) => {
        console.log("Loaded Report:", data);
      },
    }
  );
} 