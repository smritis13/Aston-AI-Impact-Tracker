import { useCallback, useState, useEffect } from 'react';

type ThemeType = 'light' | 'dark';

const useTheme = () => {
  const [currentTheme, setCurrentTheme] = useState<ThemeType>(() => {
    // Get theme from session storage on initial load
    return (sessionStorage.getItem('theme') as ThemeType) || 'dark';
  });

  useEffect(() => {
    // Apply the theme to DOM when component mounts or theme changes
    const html = document.documentElement;
    html.setAttribute('data-menu-styles', currentTheme);
    html.setAttribute('data-theme-mode', currentTheme);
    html.setAttribute('data-header-styles', currentTheme);
  }, [currentTheme]);

  const setTheme = useCallback((theme: ThemeType) => {
    setCurrentTheme(theme);
    sessionStorage.setItem('theme', theme);
  }, []);

  const getTheme = useCallback((): ThemeType => {
    return currentTheme;
  }, [currentTheme]);

  const toggleTheme = useCallback(() => {
    const next = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(next);
  }, [currentTheme, setTheme]);

  return { setTheme, getTheme, toggleTheme, currentTheme };
};

export default useTheme;
