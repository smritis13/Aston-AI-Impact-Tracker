import HttpService from "core/services/Http/HttpService";

export interface Category {
  id: number;
  name: string;
  parent?: number;
  sort_order: number;
}

export interface Metric {
  id: number;
  category: number;
  name: string;
  description?: string;
  tags: string[];
}

export class CategoryHttpService {
  private static service = new HttpService();

  static async getCategories(): Promise<any> {
    const response = await this.service.get("/base/category/");
    return response.data;
  }

  static async getCategory(id: number): Promise<any> {
    const response = await this.service.get(`/base/category/${id}/`);
    return response.data;
  }

  static async saveCategory(category: any): Promise<any> {

    var response;
    if(category.id){ 
      response = await this.service.put(`/base/category/${category.id}/`, category);
    }else{
      response = await this.service.post("/base/category/", category);
    }
    return response.data;
  }

 
  static async deleteCategory(categoryId: number) {
    var response;

    var service = new HttpService();

    response = await service.delete(`/base/category/${categoryId}/`);

    console.log(response);

    if(response.statusCode==200){
      return response.data;
    }

    return response;
  }

  static async getCategoryMetrics(categoryId: number): Promise<any> {
    const response = await this.service.get(`/base/category/${categoryId}/metrics/`);
    return response.data;
  }

  static async createMetric(categoryId: number, metric: Partial<Metric>): Promise<any> {
    const response = await this.service.post(`/base/category/${categoryId}/metrics/`, metric);
    return response.data;
  }

    static async updateMetric(categoryId: number, metricId: number, metric: Partial<Metric>): Promise<any> {
    const response = await this.service.put(`/base/category/${categoryId}/metrics/${metricId}/`, metric);
    return response.data;
  }

  static async deleteMetric(categoryId: number, metricId: number): Promise<void> {
    await this.service.delete(`/api/categories/${categoryId}/metrics/${metricId}/`);
  }
} 