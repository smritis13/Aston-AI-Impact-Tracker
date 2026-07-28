import { useQuery, UseQueryResult } from "react-query";
import { DocumentHttpService } from "../services";

interface FoldersListProps {
  page?: number;
  pageSize?: number;
  path?: string;
  category?: number;
  searchQuery?:string
}

type DocumentsData = any; // Replace with your actual data type

function UseDocumentsList({
  category,
  searchQuery,
  page = 1,
  pageSize = 30,
}: FoldersListProps): UseQueryResult<DocumentsData, unknown> {
  const queryResult = useQuery<DocumentsData, unknown>(
    ["documents_list", searchQuery,category, page, pageSize],
    () => DocumentHttpService.loadDocuments({ searchQuery, page, pageSize }),
    {
      onSuccess: (data) => {
        // console.log("Loaded documents:", data);
      },
      // keepPreviousData: true,
      refetchOnWindowFocus:false
    }
  );

  return queryResult;
}

export default UseDocumentsList;
