import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { ContentHttpService } from '../services';
import { useNavigate } from 'react-router-dom';
import { useToast } from './useToast';
import { HTTPResponse } from '../../../core/services/Http/HTTPResponse';

interface AISDLCUseCase {
  id: number;
  company: string | null;
  phase: string;
  use_case: string;
  description: string;
  tools: string;
  performance_improvements: string;
  source: string;
  date: string | null;
  created_at: string;
}

interface ReportGenerationResponse {
  report_id: string;
  status: string;
  message: string;
}

interface UseAISDLCReportParams {
  report_id?: number;
  page?: number;
  pageSize?: number;
  searchQuery?: string;
}

export const useAISDLCReport = ({ report_id, page = 1, pageSize = 10, searchQuery = '' }: UseAISDLCReportParams = {}) => {
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [selectedUseCase, setSelectedUseCase] = useState<AISDLCUseCase | null>(null);

  const { data, isLoading } = useQuery<{ results: AISDLCUseCase[]; count: number }>(
    ['aiSdlcUseCases', report_id, page, pageSize, searchQuery],
    async () => {
      const response = await ContentHttpService.loadAISDLCUseCases(report_id, searchQuery, page, pageSize) as any;
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
      const response = await ContentHttpService.generateAISDLCReport() as HTTPResponse<ReportGenerationResponse>;
      return response.data || { report_id: '', status: 'error', message: 'Failed to generate report' };
    },
    {
      onSuccess: (data) => {
        showToast({
          type: 'success',
          title: 'Report generation started',
          message: 'Your report is being generated. You will be notified when it is ready.'
        });
        queryClient.invalidateQueries(['aiSdlcUseCases']);
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