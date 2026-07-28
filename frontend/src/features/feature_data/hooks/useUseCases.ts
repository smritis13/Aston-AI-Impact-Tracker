import { useState, useEffect, useCallback } from 'react';
import { ContentHttpService } from "../services";
import { useToast } from './useToast';

interface UseCase {
  id: number;
  use_case_name: string;
  use_case_type: string;
  company: string;
  industry: string;
  tools: string;
  use_case_description: string;
  performance_impact: string;
  use_case_date: string;
  published_date: string | null;
  source: string;
  source_reference: string | null;
  domain: string | null;
  publisher: string | null;
  content_type: string | null;
  direct_quote: string | null;
  ref_period_status: "within_period" | "outside_period" | null;
  reference_number: number | null;
  created_at: string;
  url_validation_score: number;
  relevance_score: number;
  credibility_score: number | null;
  credibility_reasoning?: string;
  relevance_reasoning?: string;
}

interface UseCaseResponse {
  results: UseCase[];
  count: number;
}

interface UseUseCasesProps {
  page: number;
  pageSize: number;
  searchQuery: string;
  themeId?: number;
  reportId?: number;
  sortBy?: string;
  sortDirection?: 'asc' | 'desc';
}

export const useUseCases = ({ page, pageSize, searchQuery, themeId, reportId, sortBy = 'relevance_score', sortDirection = 'desc' }: UseUseCasesProps) => {
  const [useCases, setUseCases] = useState<UseCase[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const { showToast } = useToast();

  const fetchUseCases = useCallback(async () => {
    try {
      setUseCases([]);
      setIsLoading(true);
      const data = await ContentHttpService.loadUseCases(themeId, searchQuery, page, pageSize, sortBy, sortDirection, reportId) as UseCaseResponse;
      setUseCases(data.results);
      setTotalCount(data.count);
    } catch (error) {
      console.error('Error fetching use cases:', error);
      setUseCases([]);
      setTotalCount(0);
    } finally {
      setIsLoading(false);
    }
  }, [themeId, searchQuery, page, pageSize, sortBy, sortDirection, reportId]);

  // Reloads results without clearing the list first — used during active
  // generation so each new result appears without the list flashing blank.
  // Memoized with useCallback so its identity stays stable across renders;
  // it's passed to PusherListener, whose subscription effect resubscribes
  // (dropping the live connection) whenever this reference changes.
  const silentRefetch = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await ContentHttpService.loadUseCases(themeId, searchQuery, page, pageSize, sortBy, sortDirection, reportId) as UseCaseResponse;
      setUseCases(data.results);
      setTotalCount(data.count);
    } catch (error) {
      console.error('Error fetching use cases:', error);
    } finally {
      setIsLoading(false);
    }
  }, [themeId, searchQuery, page, pageSize, sortBy, sortDirection, reportId]);

  const handleGenerateReport = useCallback(async (themeId?: number) => {
    try {
      showToast({
        type: 'success',
        title: 'Use case search started',
        message: 'Use case search started. The steps and thinking process are displayed below the use case list.'
      });
      const response = await ContentHttpService.generateUseCaseReport(themeId);

      if (response) {
        await fetchUseCases();
      }
      return response;
    } catch (error) {
      console.error('Error generating report:', error);
      throw error;
    }
  }, [showToast, fetchUseCases]);

  const handleDeleteUseCase = useCallback(async (id: number) => {
    try {
      await ContentHttpService.deleteUseCase(id);
      setUseCases(prev => prev.filter(uc => uc.id !== id));
      setTotalCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error deleting use case:', error);
      showToast({ type: 'error', title: 'Delete failed', message: 'Could not delete this result.' });
    }
  }, [showToast]);

  useEffect(() => {
    setUseCases([]);
    fetchUseCases();
  }, [page, pageSize, searchQuery, themeId, reportId, sortBy, sortDirection]);

  return {
    useCases,
    totalCount,
    isLoading,
    handleGenerateReport,
    handleDeleteUseCase,
    refetch: fetchUseCases,
    silentRefetch,
  };
}; 
