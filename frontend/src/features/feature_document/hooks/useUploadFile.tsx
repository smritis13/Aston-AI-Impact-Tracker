import { useMutation, useQueryClient } from "react-query";
import { DocumentHttpService } from "../services";
import { AxiosProgressEvent } from "axios";
import { useState } from "react";

interface UploadFileProps {
  file: File;
  categoryId?: number;
}

interface UploadFileResponse {
  progress: number;
  status: "uploading" | "done" | "error";
}

const useUploadFile = () => {
  
  const queryClient = useQueryClient();
  
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: UploadFileResponse }>({});

  const uploadFileMutation = useMutation(
    async ({ file, categoryId }: UploadFileProps) => {
      return DocumentHttpService.uploadDocument(file,categoryId, (progressEvent: AxiosProgressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / (progressEvent.total ?? 100));
        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: { progress, status: "uploading" },
        }));
      });
    },
    {
      onSuccess: (_, { file }) => {
        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: { progress: 100, status: "done" },
        }));

        queryClient.invalidateQueries("documents_list");

      },
      onError: (_, { file }) => {
        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: { progress: 0, status: "error" },
        }));
      },
    }
  );

  return { uploadFileMutation, uploadProgress };
};

export default useUploadFile;
