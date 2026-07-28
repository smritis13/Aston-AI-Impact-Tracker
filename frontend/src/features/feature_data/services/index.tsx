import { AxiosProgressEvent } from "axios";
import HttpService from "core/services/Http/HttpService";
import axios from "axios";

export interface Theme {
  id: number;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
  featured: boolean;
}

export interface ThemesResponse {
  results: Theme[];
  count: number;
}

export interface ThemeFormData {
  title: string;
  description: string;
  featured: boolean;
}

export interface FieldOptions {
  useCaseTypes: string[];
  companies: string[];
  industries: string[];
  impacts: string[];
  technologies: string[];
  countries: string[];
  tools: string[];
}

export interface SavedEntitySearchPayload {
  display_name: string;
  entity_name: string;
  entity_type: string;
  strict_matching: boolean;
  additional_filters: Record<string, any>;
}

export class ContentHttpService {
  static normalizeThemesResponse(data: Theme[] | ThemesResponse | null | undefined): ThemesResponse {
    if (Array.isArray(data)) {
      return {
        results: data,
        count: data.length,
      };
    }

    if (data && Array.isArray(data.results)) {
      return {
        results: data.results,
        count: typeof data.count === 'number' ? data.count : data.results.length,
      };
    }

    return {
      results: [],
      count: 0,
    };
  }

  static async validateUrl(url: string) {
    var service = new HttpService();
    var response;
    response = await service.get(`/content/url-validation?url=${url}`);
    return response.data;
  }

  static async loadReport(reportId: number | undefined) {
    if (!reportId) return null;
    
    var service = new HttpService();
    var response;

    response = await service.get(`/content/reports/${reportId}/`);

    if(response.isSuccess && response.data){
      return response.data;
    }

    throw new Error(response.errorMessage || `Failed to load report ${reportId}`);
  }

  static async loadReports() {
      var service = new HttpService();
      var response = await service.get(`/content/reports/?report_type=impact_case_study&size=200`);
      if(response.statusCode==200){
        return response.data;
      }
      return response
  }

  

  static async loadInsights() {

      var service = new HttpService();
      var response;


      response = await service.get(`/content/insights/`);

      if(response.statusCode==200){
        return response.data;
      }

      return response
  }


  static async deleteContent(contentId:number) {

      var service = new HttpService();
      var response;

      response = await service.delete(`/content/${contentId}`);

      return response
  }


  static async loadContents({category=null,searchQuery='/',page=1, pageSize=30}) {

      var service = new HttpService();
      var response;

      var query = `?category=${category}&page=${page}&size=${pageSize}&query=${searchQuery}`

      response = await service.get(`/content/${query}`);

      if(response.statusCode==200){
        return response.data;
      }

      return response
  }


  static async loadContent(contentId:number) {

    var service = new HttpService();
    var response;

    response = await service.get(`/content/${contentId}`);

    if(response.statusCode==200){
      return response.data;
    }

    return response
}

  static async generateReport(data: {
    query: string;
    prompt_id?: number;
    pdf_filename?: string;
    pdf_text?: string;
    theme_id?: number | null;
    report_type?: string;
    impact_sections?: any[];
    include_summary?: boolean;
    number_of_outcomes?: number | string;
    search_complexity?: string;
    max_links_to_scrape?: number | string;
    relevance_threshold?: number | string;
  }) {
    var service = new HttpService();
    var response:any;

    response = await service.post('/content/report-generation/', data);

    if(response.statusCode === 200 || response.statusCode === 201) {
      return response.data;
    }

    return response;
  }

  static async generateImpactCaseStudyReport(data: {
    query: string;
    theme_id?: number | null;
    report_type?: string;
    impact_sections?: any[];
    include_summary?: boolean;
    number_of_outcomes?: number | string;
    search_complexity?: string;
    uploaded_files?: File[];
    skip_report_generation?: boolean;
    relevance_threshold?: number | string;
  }) {
    var service = new HttpService();
    const formData = new FormData();

    formData.append('query', data.query);
    if (data.relevance_threshold !== undefined && data.relevance_threshold !== '') {
      formData.append('relevance_threshold', String(data.relevance_threshold));
    }
    formData.append('report_type', data.report_type || 'impact_case_study');
    formData.append('include_summary', String(data.include_summary ?? true));
    formData.append('number_of_outcomes', String(data.number_of_outcomes ?? 10));
    formData.append('search_complexity', data.search_complexity || 'medium');
    formData.append('impact_sections', JSON.stringify(data.impact_sections || []));
    formData.append('skip_report_generation', String(data.skip_report_generation ?? false));

    if (data.theme_id) {
      formData.append('theme_id', String(data.theme_id));
    }

    data.uploaded_files?.forEach((file) => {
      formData.append('uploaded_files', file);
    });

    const response: any = await service.post('/content/report-generation/', formData);

    if(response.statusCode === 200 || response.statusCode === 201) {
      return response.data;
    }

    throw new Error(response.errorMessage || 'Failed to generate impact case study report');
  }

  static async compileImpactCaseStudyFromUseCases(data: {
    theme_id: number;
    use_case_ids?: number[];
    prompt?: string;
    report_type?: string;
    impact_sections?: any[];
    include_summary?: boolean;
  }) {
    var service = new HttpService();
    var response: any;

    response = await service.post('/content/reports/compile-from-use-cases/', {
      theme_id: data.theme_id,
      use_case_ids: data.use_case_ids,
      prompt: data.prompt,
      report_type: data.report_type || 'impact_case_study',
      impact_sections: data.impact_sections || [],
      include_summary: data.include_summary ?? true,
    });

    if (response.statusCode === 200 || response.statusCode === 201) {
      return response.data;
    }

    throw new Error(response.errorMessage || 'Failed to compile report from existing use cases');
  }

  static async getPrompts() {
    var service = new HttpService();
    var response : any;

    response = await service.get('/content/prompts/');

    if(response.statusCode==200){
      return response.data;
    }

    return response;
  }

  static async createPrompt(data: { title: string; content: string; json_structure?: string }) {
    var service = new HttpService();
    var response;

    response = await service.post('/content/prompts/', data);

    if(response.statusCode==200 || response.statusCode==201){
      return response.data;
    }

    return response;
  }

  static async deleteReport(reportId: number) {
    var service = new HttpService();
    var response;
    response = await service.delete(`/content/reports/${reportId}/`);
    return response.data;
  }

  static async loadSDLCUseCases(report_id?: number, searchQuery?: string, page: number = 1, pageSize: number = 10) {
    var service = new HttpService();
    var response;
    let endpoint = report_id 
      ? `/content/sdlc-use-cases/?report_id=${report_id}`
      : `/content/sdlc-use-cases/`;
    
    const params = new URLSearchParams();
    
    params.append('page', page.toString());
    params.append('size', pageSize.toString());
    
    endpoint += endpoint.includes('?') ? `&${params.toString()}` : `?${params.toString()}`;

    if (searchQuery) {
      endpoint += searchQuery;
    }
    
    response = await service.get(endpoint);
    if(response.statusCode==200){
      return response.data;
    }
    return response;
  }

  static async loadAISDLCUseCases(report_id?: number, searchQuery?: string, page: number = 1, pageSize: number = 10) {
    var service = new HttpService();
    var response;
    let endpoint = report_id 
      ? `/content/ai-sdlc-use-cases/?report_id=${report_id}`
      : `/content/ai-sdlc-use-cases/`;
    
    const params = new URLSearchParams();
    
    params.append('page', page.toString());
    params.append('size', pageSize.toString());
    
    endpoint += endpoint.includes('?') ? `&${params.toString()}` : `?${params.toString()}`;

    if (searchQuery) {
      endpoint += searchQuery;
    }
    
    response = await service.get(endpoint);
    if(response.statusCode==200){
      return response.data;
    }
    return response;
  }

  static async loadRetailUseCases(report_id?: number, searchQuery?: string, page: number = 1, pageSize: number = 10) {
    var service = new HttpService();
    var response;
    let endpoint = report_id 
      ? `/content/retail-use-cases/?report_id=${report_id}`
      : `/content/retail-use-cases/`;
    
    const params = new URLSearchParams();
    
    params.append('page', page.toString());
    params.append('size', pageSize.toString());
    
    endpoint += endpoint.includes('?') ? `&${params.toString()}` : `?${params.toString()}`;

    if (searchQuery) {
      endpoint += searchQuery;
    }
    
    response = await service.get(endpoint);
    if(response.statusCode==200){
      return response.data;
    }
    return response;
  }

  static async generateSDLCReport() {
    var service = new HttpService();
    var response;
    response = await service.post(`/content/sdlc-report-generation/`, {});
    if(response.statusCode==200){
      return response.data;
    }
    return response;
  }

  static async generateAISDLCReport() {
    var service = new HttpService();
    var response;
    response = await service.post(`/content/ai-sdlc-report-generation/`, {});
    if(response.statusCode==200){
      return response.data;
    }
    return response;
  }

  static async loadReportThoughts(reportId: string | undefined) {
    var service = new HttpService();
    var response;

    response = await service.get(`/content/reports/${reportId}/thoughts/`);

    if(response.statusCode==200){
      return response.data;
    }

    return response;
  }

  static async initializeStream(): Promise<any> {
    var service = new HttpService();
    var response;

    response = await service.post('/content/stream/', {});

    if(response.statusCode === 200 || response.statusCode === 201) {
      return response.data as any;
    }

    throw new Error('Failed to initialize stream');
  }

  static async loadUseCases(themeId?: number, searchQuery?: string, page: number = 1, pageSize: number = 30, sortBy: string = 'relevance_score', sortDirection: string = 'desc', reportId?: number) {
    var service = new HttpService();
    const params = new URLSearchParams();
    var query = '';
    if (themeId) {
      query = `theme_id=${themeId}`;
    }
    if (reportId) {
      query += `${query ? '&' : ''}report_id=${reportId}`;
    }
    if (searchQuery) {
      query += `${searchQuery}`;
    }

    if (query) {
      query += `&page=${page}&size=${pageSize}&sort_by=${sortBy}&sort_direction=${sortDirection}`;
    }
    else {
      query = `page=${page}&size=${pageSize}&sort_by=${sortBy}&sort_direction=${sortDirection}`;
    }



    const response = await service.get(`/content/use-cases/?${query}`);
    if(response.statusCode === 200) {
      return response.data;
    }
    throw new Error('Failed to load use cases');
  }

  static async loadSavedSearches(favoritesOnly: boolean = false, limit: number = 20) {
    var service = new HttpService();
    const response = await service.get(`/content/saved-searches/?favorites_only=${favoritesOnly}&limit=${limit}`);

    if(response.statusCode === 200) {
      return response.data;
    }

    throw new Error(response.errorMessage || 'Failed to load saved searches');
  }

  static async createSavedSearch(data: SavedEntitySearchPayload) {
    var service = new HttpService();
    const response = await service.post('/content/saved-searches/', data);

    if(response.statusCode === 200 || response.statusCode === 201) {
      return response.data;
    }

    throw new Error(response.errorMessage || 'Failed to save search');
  }

  static async trackSavedSearchUsage(searchId: number) {
    var service = new HttpService();
    const response = await service.post(`/content/saved-searches/${searchId}/track-usage/`, {});

    if(response.statusCode === 200 || response.statusCode === 201) {
      return response.data;
    }

    throw new Error(response.errorMessage || 'Failed to track saved search usage');
  }

  static async deleteUseCase(id: number) {
    var service = new HttpService();
    var response = await service.delete(`/content/use-cases/${id}/`);
    if (response.statusCode === 204 || response.statusCode === 200) {
      return true;
    }
    throw new Error(response.errorMessage || 'Failed to delete use case');
  }

  static async generateUseCaseReport(themeId?: number) {
    var service = new HttpService();
    var response;
    response = await service.post(`/content/report-generation/`, {
      // report_type: 'structured',
      theme_id: themeId
    });
    if(response.statusCode==200){
      return response.data;
    }
    return response;
  }

  static async getThemes(in_featured?: boolean, page?: number, pageSize?: number, deleted?: boolean): Promise<Theme[] | ThemesResponse> {
    var service = new HttpService();
    var response;
    const params = new URLSearchParams();

    if (in_featured !== undefined) {
      params.append('featured', String(in_featured));
    }

    if (page !== undefined) {
      params.append('page', page.toString());
    }

    if (pageSize !== undefined) {
      params.append('page_size', pageSize.toString());
    }

    if (deleted !== undefined) {
      params.append('deleted', String(deleted));
    }

    const query = params.toString();
    response = await service.get(`/content/themes/${query ? `?${query}` : ''}`);

    if(response.statusCode==200){
      return response.data as Theme[] | ThemesResponse;
    }
    throw new Error(response.errorMessage || 'Failed to load themes');
  }

  static async loadThemes(page: number, pageSize: number): Promise<any> {
    var service = new HttpService();
    var response = await service.get(`/content/themes/?page=${page}&page_size=${pageSize}`);
    if (response.statusCode === 200) {
      return response.data;
    }
    throw new Error('Failed to load themes');
  }

  static async saveTheme(data: ThemeFormData, id?: number): Promise<any> {
    var service = new HttpService();
    var response;
    
    if (id) {
      response = await service.put(`/content/themes/${id}/`, data);
    } else {
      response = await service.post('/content/themes/', data);
    }

    if (response.statusCode === 200 || response.statusCode === 201) {
      return response.data;
    }
    throw new Error('Failed to save theme');
  }

  static async deleteTheme(id: number): Promise<void> {
    var service = new HttpService();
    var response = await service.delete(`/content/themes/${id}/`);
    if (response.statusCode !== 204) {
      throw new Error('Failed to delete theme');
    }
  }

  static async restoreTheme(id: number): Promise<Theme> {
    var service = new HttpService();
    var response = await service.post(`/content/themes/${id}/restore/`, {});
    if (response.statusCode === 200) {
      return response.data as Theme;
    }
    throw new Error(response.errorMessage || 'Failed to restore theme');
  }

  static async stopReportGeneration(themeId?: number) {
    var service = new HttpService();
    const response = await service.post(`/content/reports/${themeId}/stop/`, {});
    return response.data;
  }

  static async findReportByTheme(themeId: number) {
    var service = new HttpService();
    const response = await service.get(`/content/reports/theme/${themeId}/`);
    return response.data;
  }

  static async getFieldOptions(themeId?: number): Promise<FieldOptions> {
    var service = new HttpService();
    const query = themeId ? `?theme_id=${themeId}` : '';


    var response = await service.get(`/content/field-options/${query}`);
    
    if(response.statusCode === 200) {
      return response.data as FieldOptions;
    }
    throw new Error('Failed to load field options');
  }

  static async savePrompt(data: { title: string; content: string; json_structure?: string; id?: number }, id?: number): Promise<any> {
    var service = new HttpService();
    var response;
    if (id) {
      response = await service.put(`/content/prompts/${id}/`, data);
    } else {
      response = await service.post('/content/prompts/', data);
    }
    if (response.statusCode === 200 || response.statusCode === 201) {
      return response.data;
    }
    throw new Error('Failed to save prompt');
  }

  static async deletePrompt(id: number): Promise<void> {
    var service = new HttpService();
    var response = await service.delete(`/content/prompts/${id}/`);
    if (response.statusCode !== 204) {
      throw new Error('Failed to delete prompt');
    }
  }
}
