import { BaseHttpService } from "core/services/BaseHttpService";
import { useQuery, UseQueryResult } from "react-query";
import { ContentHttpService } from "../services";

export interface Content {
  id: number;
  title: string;
  image: string | null;
  summary: string;
  tags: string[];
  category: {
    id: number;
    name: string;
  };
  // add additional fields as needed
}

interface UseContentListParams {
  category:any;
  searchQuery?: string;
  page: number;
  pageSize: number;
}

function UseContentList({
  category,
  searchQuery,
  page,
  pageSize,
}: UseContentListParams): UseQueryResult<any, unknown> {
  return useQuery<any, unknown>(
    ["contents", category, searchQuery, page, pageSize],
    () =>
      ContentHttpService.loadContents({
        category,
        searchQuery,
        page,
        pageSize,
      }),
    {
      onSuccess: (data) => {
        // Optional: Log or manipulate data on success
        // console.log("Loaded contents:", data);
      },
    }
  );
}

export default UseContentList;
