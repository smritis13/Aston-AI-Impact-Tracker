import { useQuery, UseQueryResult } from "react-query";
import { ContentHttpService } from "../services";
/**
 * Custom hook to fetch insights using react-query.
 */
function UseInsights(): UseQueryResult<any, unknown> {
  return useQuery<any, unknown>(
    ["insights"],
    () => ContentHttpService.loadInsights(),
    {
      onSuccess: (data) => {
        // Optional: Debugging or transformation
        console.log("Loaded insights:", data);
      },
    }
  );
}

export default UseInsights;
