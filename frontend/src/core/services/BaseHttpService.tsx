import { AxiosProgressEvent } from "axios";
import HttpService from "core/services/Http/HttpService";

export class BaseHttpService {


  static async loadCategories({parent=0,page=1, pageSize=30}) {

    var service = new HttpService();
    var response;

    var query = `?page=${page}&size=${pageSize}`
    if(parent && parent>0){
      query += `&parent=${parent}`;
    }

    response = await service.get(`/base/category/${query}`);

    return response
}

    

}