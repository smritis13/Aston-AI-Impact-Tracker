import { AxiosProgressEvent } from "axios";
import HttpService from "core/services/Http/HttpService";

export class DocumentHttpService {


  static async deleteDocument(documentId:number) {

    var service = new HttpService();
    var response;

    response = await service.delete(`/document/${documentId}`);

    return response
}


  static async loadDocuments({searchQuery='/',page=1, pageSize=30}) {

      var service = new HttpService();
      var response;

      var query = `?page=${page}&size=${pageSize}&query=${searchQuery}`

      response = await service.get(`/document/${query}`);

      if(response.statusCode==200){
        return response.data;
      }

      return response
  }

    
    

    static async uploadDocument(
        file: File,
        categoryId?:number,
        onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
      ) {
        const service = new HttpService();
        const formData = new FormData();
        formData.append('file', file);
        if(categoryId){
          formData.append('category', categoryId+'');
        }

        const response = await service.postWithProgress(
          '/document/',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            },
            onUploadProgress, // Pass the progress callback to monitor progress
          }
        );
      
        return response;
      }

}