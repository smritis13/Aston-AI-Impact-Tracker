import axios, { AxiosProgressEvent, AxiosRequestConfig } from 'axios';
import { HTTPResponse } from './HTTPResponse'; // Import the HTTPResponse class

class HttpService {
  private apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000'; 
  private timeout = 30000; // 30 second timeout
  // private apiUrl = 'https://alixpartners.jobflowconnect.com/api'; 
  // private apiUrl = 'https://django-backend-app.azurewebsites.net'; 
  
  constructor() {
   
  }

  public getApiUrl(): string {
    return this.apiUrl;
  }

  public async get<T>(endpoint: string): Promise<HTTPResponse<T>> {
    // console.log('GET REQUEST:', `${this.apiUrl}${endpoint}`);
    try {
      const response = await axios.get(`${this.apiUrl}${endpoint}`, { timeout: this.timeout });
      return new HTTPResponse<T>(response.status, response.data);
    } catch (error: any) {
      return this.handleError<T>(error);
    }
  }

  public async post<T>(endpoint: string, data: any): Promise<HTTPResponse<T>> {
    try {
      const response = await axios.post(`${this.apiUrl}${endpoint}`, data, { timeout: this.timeout });
      return new HTTPResponse<T>(response.status, response.data);
    } catch (error: any) {
      return this.handleError<T>(error);
    }
  }

  public async put<T>(endpoint: string, data: any): Promise<HTTPResponse<T>> {
    try {
      const response = await axios.put(`${this.apiUrl}${endpoint}`, data, { timeout: this.timeout });
      return new HTTPResponse<T>(response.status, response.data);
    } catch (error: any) {
      return this.handleError<T>(error);
    }
  }

  public async delete<T>(endpoint: string): Promise<HTTPResponse<T>> {
    try {
      const response = await axios.delete(`${this.apiUrl}${endpoint}`, { timeout: this.timeout });
      return new HTTPResponse<T>(response.status, response.data);
    } catch (error: any) {
      return this.handleError<T>(error);
    }
  }
  public async patch<T>(endpoint: string, data: any): Promise<HTTPResponse<T>> {
    try {
      const response = await axios.patch(`${this.apiUrl}${endpoint}`, data, { timeout: this.timeout });

      
      return new HTTPResponse<T>(response.status, response.data);
    } catch (error: any) {
      return this.handleError<T>(error);
    }
  }

  private handleError<T>(error: any): HTTPResponse<T> {
    let errorMessage = 'An unexpected error occurred.';


    if (error.response) {
      const responseData = error.response.data;
      const status = error.response.status;

      // Extract messages from validation errors
      if (responseData.errors) {
        const errorMessages = Object.keys(responseData.errors).map((key) => {
          // Join all messages for a specific field
          return `${responseData.errors[key].join(', ')}`;
        });
        errorMessage = errorMessages.join(' | ');
      }else if(responseData.error){
        errorMessage = responseData.error;
      }
      else {
        errorMessage = responseData?.message || errorMessage;
      }

      return new HTTPResponse<T>(status, undefined, errorMessage);
    } else if (error.request) {
      errorMessage =
        'No response received from the server. Please try again later.';
      return new HTTPResponse<T>(0, undefined, errorMessage);
    } else {
      errorMessage = error.message;
      return new HTTPResponse<T>(0, undefined, errorMessage);
    }
  }

  public async postWithProgress<T>(
    endpoint: string,
    data: any,
    config?: AxiosRequestConfig
  ): Promise<HTTPResponse<T>> {
    try {
      const configWithTimeout = { ...config, timeout: this.timeout };
      const response = await axios.post(`${this.apiUrl}${endpoint}`, data, configWithTimeout);
      return new HTTPResponse<T>(response.status, response.data);
    } catch (error: any) {

      if (error.response) {
        console.error("HTTP Error Status:", error.response.status);
        console.error("HTTP Error Data:", error.response.data);
      } else {
        console.error("Error without response:", error);
      }

      return this.handleError<T>(error);
    }
  }
}

export default HttpService;
