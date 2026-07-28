import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { ContentHttpService } from '../services';
import { useNavigate } from 'react-router-dom';
import { useToast } from './useToast';
import { HTTPResponse } from '../../../core/services/Http/HTTPResponse';

interface SDLCUseCase {
  id: number;
  phase: string;
  company: string;
  industry_segment: string;
  sdlc_tools: string;
  use_case_description: string;
  metric_impact: string;
  date: string | null;
  credibility_score: number;
  source: string;
  created_at: string;
}

interface ReportGenerationResponse {
  report_id: string;
  status: string;
  message: string;
}

interface UseSLDCReportParams {
  report_id?: number;
  page?: number;
  pageSize?: number;
  searchQuery?: string;
}

export const useSLDCReport = ({ report_id, page = 1, pageSize = 10, searchQuery = '' }: UseSLDCReportParams = {}) => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [selectedUseCase, setSelectedUseCase] = useState<SDLCUseCase | null>(null);

  const { data, isLoading } = useQuery<{ results: SDLCUseCase[]; count: number }>(
    ['sdlcUseCases', report_id, page, pageSize, searchQuery],
    async () => {
      const response = await ContentHttpService.loadSDLCUseCases(report_id, searchQuery, page, pageSize) as any;
      return {
        results: response.results || [],
        count: response.count || 0
      };
    },
    {
      enabled: true,
    }
  );

  const generateReportMutation = useMutation<ReportGenerationResponse, Error, string>(
    async () => {
      const response = await ContentHttpService.generateSDLCReport() as HTTPResponse<ReportGenerationResponse>;
      return response.data || { report_id: '', status: 'error', message: 'Failed to generate report' };
    },
    {
      onSuccess: (data) => {
        showToast({
          type: 'success',
          title: 'Report generation started',
          message: 'Your report is being generated. You will be notified when it is ready.'
        });
        queryClient.invalidateQueries(['sdlcUseCases']);
      },
      onError: (error) => {
        showToast({
          type: 'error',
          title: 'Error',
          message: 'Failed to generate report. Please try again.'
        });
      },
    }
  );

  const handleGenerateReport = (useCaseId: string) => {
    generateReportMutation.mutate(useCaseId);
  };

  return {
    useCases: data?.results || [],
    totalCount: data?.count || 0,
    isLoading,
    selectedUseCase,
    setSelectedUseCase,
    handleGenerateReport,
    isGenerating: generateReportMutation.isLoading,
  };
}; 