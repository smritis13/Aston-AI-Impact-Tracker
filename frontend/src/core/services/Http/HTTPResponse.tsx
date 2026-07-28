// HTTPResponse.ts
export class HTTPResponse<T> {
  public statusCode: number;
  public data?: T;
  public errorMessage?: string;
  public isSuccess: boolean;

  constructor(statusCode: number, data?: T, errorMessage?: string) {
    this.statusCode = statusCode;
    this.data = data;
    this.errorMessage = errorMessage;
    this.isSuccess = statusCode >= 200 && statusCode < 300; // Check if status code is in the 200 range
  }
}
