import { useQuery, UseQueryResult } from "react-query";
import { ContentHttpService } from "../services";
/**
 * Custom hook to fetch insights using react-query.
 */
function useReports(): UseQueryResult<any, unknown> {
  return useQuery<any, unknown>(
    ["reports"],
    () => ContentHttpService.loadReports(),
    {
      onSuccess: (data) => {
        // Optional: Debugging or transformation
        // console.log("Loaded Reports:", data);
      },
    }
  );
}

export default useReports;
