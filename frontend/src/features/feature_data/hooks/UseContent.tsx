import { useQuery, UseQueryResult } from "react-query";
import { ContentHttpService } from "../services";




function UseContent(id: number): UseQueryResult<any, unknown> {
  return useQuery<any, unknown>(
    ["content", id],
    () => ContentHttpService.loadContent(id),
    {
      onSuccess: (data) => {
        // Optional: Log or manipulate data on success
        // console.log("Loaded content:", data);
      },
    }
  );
}

export default UseContent;
