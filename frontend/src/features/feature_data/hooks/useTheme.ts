import { useState, useEffect } from 'react';
import { useQueryClient } from 'react-query';
import { ContentHttpService, Theme } from '../services';

export const useTheme = (themeId?: number) => {
  const [theme, setTheme] = useState<Theme | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const fetchTheme = async () => {
    if (!themeId) {
      setTheme(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await ContentHttpService.getThemes();
      const themes = ContentHttpService.normalizeThemesResponse(response).results;
      const foundTheme = themes.find((t: Theme) => t.id === themeId);
      if (foundTheme) {
        setTheme(foundTheme);
        setError(null);
      } else {
        setError('Theme not found');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch theme');
    } finally {
      setLoading(false);
    }
  };

  const toggleFeatured = async () => {
    if (!theme) return;
    
    try {
      const updatedTheme = await ContentHttpService.saveTheme({
        ...theme,
        featured: !theme.featured
      }, theme.id);
      setTheme(updatedTheme);
      queryClient.invalidateQueries('themes');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update theme');
    }
  };

  useEffect(() => {
    fetchTheme();
  }, [themeId]);

  return { theme, loading, error, toggleFeatured };
}; 
