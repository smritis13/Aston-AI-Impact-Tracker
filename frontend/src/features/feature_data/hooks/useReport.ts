import { useQuery, UseQueryResult } from "react-query";
import { ContentHttpService } from "../services";

export interface Report {
  id: number;
  created_at: string;
  updated_at: string;
  sort_order: number;
  topic: string;
  query: string;
  generated_report: string;
  metadata?: {
    completeness?: {
      requested: number;
      found: number;
      stopped_reason: string;
    };
    token_usage?: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
      calls: number;
    };
    search_api_usage?: {
      provider: string;
      calls_total: number;
      calls_failed: number;
    };
    content_provenance?: {
      total_evidence_items: number;
      items_with_verbatim_quote: number;
      items_with_quantitative_metric: number;
      items_with_specific_citation_location: number;
      note: string;
    };
    research_summary?: string;
    [key: string]: any;
  };
}

function useReport(id: any | undefined): UseQueryResult<any, unknown> {
  return useQuery<any, unknown>(
    ["report", id],
    () => ContentHttpService.loadReport(id),
    {
      enabled: !!id,
      onSuccess: (data) => {
        // console.log("Loaded Report:", data);
      },
    }
  );
}

export default useReport; 
