import { BaseHttpService } from "core/services/BaseHttpService";
import { useQuery, UseQueryResult } from "react-query";


function UseCategoriesList(): UseQueryResult<any, unknown> {
  return useQuery<any, unknown>(
    ["categories_list"],
    () => BaseHttpService.loadCategories({}), 
    {
      onSuccess: (data) => {
        // console.log("Loaded categories:", data);
      },
    }
  );
}

export default UseCategoriesList;
