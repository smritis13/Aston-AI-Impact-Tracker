import { useState } from 'react';
import { useQuery } from 'react-query';
import { ContentHttpService } from '../services';

interface RetailUseCase {
  id: number;
  company: string;
  use_case: string;
  description: string;
  technology_used: string;
  impact: string;
  source: string | null;
  date: string;
  created_at: string;
}

interface UseRetailUseCasesParams {
  report_id?: number;
  page?: number;
  pageSize?: number;
  searchQuery?: string;
}

export const useRetailUseCases = ({ report_id, page = 1, pageSize = 10, searchQuery }: UseRetailUseCasesParams = {}) => {
  const [selectedUseCase, setSelectedUseCase] = useState<RetailUseCase | null>(null);

  const { data, isLoading } = useQuery<{ results: RetailUseCase[]; count: number }>(
    ['retailUseCases', report_id, page, pageSize, searchQuery],
    async () => {
      const response = await ContentHttpService.loadRetailUseCases(report_id, searchQuery, page, pageSize) as any;
      return {
        results: response.results || [],
        count: response.count || 0
      };
    },
    {
      enabled: true,
    }
  );

  return {
    useCases: data?.results || [],
    totalCount: data?.count || 0,
    isLoading,
    selectedUseCase,
    setSelectedUseCase,
  };
}; 