import { useQuery, UseQueryResult } from "react-query";
import { ContentHttpService, FieldOptions } from "../services";

function UseFieldOptions(themeId?: number): UseQueryResult<FieldOptions, Error> {
  return useQuery<FieldOptions, Error>(
    ["fieldOptions", themeId],
    () => ContentHttpService.getFieldOptions(themeId),
    {
      staleTime: 5 * 60 * 1000, // Cache for 5 minutes
      cacheTime: 30 * 60 * 1000, // Keep in cache for 30 minutes
    }
  );
}

export default UseFieldOptions; 