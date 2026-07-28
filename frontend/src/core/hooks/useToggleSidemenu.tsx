import { useCallback, useState, useEffect } from 'react';

const useToggleSidemenu = () => {
  const [isMenuClosed, setIsMenuClosed] = useState(() => {
    const html = document.documentElement;
    return html.getAttribute('data-toggled') === 'close-menu-close';
  });

  const toggleMenu = useCallback(() => {
    const html = document.documentElement;
    const isClosed = html.getAttribute('data-toggled') === 'close-menu-close';

    if (isClosed) {
      html.setAttribute('data-toggled', '');
      setIsMenuClosed(false);
    } else {
      html.setAttribute('data-toggled', 'close-menu-close');
      html.setAttribute('data-vertical-style', 'closed');
      setIsMenuClosed(true);
    }
  }, []);

  // Optional: sync state on mount (in case menu was toggled manually)
  useEffect(() => {
    const html = document.documentElement;
    setIsMenuClosed(html.getAttribute('data-toggled') === 'close-menu-close');
  }, []);

  return { toggleMenu, isMenuClosed };
};

export default useToggleSidemenu;
