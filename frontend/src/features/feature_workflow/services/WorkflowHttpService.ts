import HttpService from "core/services/Http/HttpService";

export class WorkflowHttpService {
  static async loadWorkflows() {
    const service = new HttpService();
    const response = await service.get('/workflow/');
    
    if (response.statusCode === 200) {
      return response.data;
    }
    return response;
  }

  static async loadWorkflow(workflowId: string) {
    const service = new HttpService();
    const response = await service.get(`/workflow/${workflowId}/`);
    
    if (response.statusCode === 200) {
      return response.data;
    }
    return response;
  }
} 