import { useQuery } from 'react-query';
import { ContentHttpService, Theme, ThemesResponse } from '../services';

interface UseThemesProps {
  page?: number;
  pageSize?: number;
  featured?: boolean;
  deleted?: boolean;
}

export const useThemes = ({ page = 1, pageSize = 100, featured, deleted }: UseThemesProps = {}) => {
  const { data, isLoading: loading, error, refetch } = useQuery<ThemesResponse>(
    ['themes', page, pageSize, featured, deleted],
    async () => {
      const response = await ContentHttpService.getThemes(featured, page, pageSize, deleted);
      return ContentHttpService.normalizeThemesResponse(response);
    },
    {
      staleTime: 5 * 60 * 1000, // Cache for 5 minutes
      cacheTime: 30 * 60 * 1000, // Keep in cache for 30 minutes
      retry: 1, // Retry once on failure
      retryDelay: 1000, // Wait 1 second before retrying
    }
  );

  const themes: Theme[] = data?.results ?? [];
  const totalCount = data?.count ?? 0;

  return { themes, totalCount, loading, error, refetch };
}; 
