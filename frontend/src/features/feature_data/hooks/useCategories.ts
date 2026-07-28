import { useState, useEffect } from 'react';
import { CategoryHttpService } from '../services/CategoryHttpService';

export const useCategories = () => {
  const [categories, setCategories] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setIsLoading(true);
      const data = await CategoryHttpService.getCategories();
      setCategories(data);
    } catch (err) {
      setError("Failed to load categories");
    } finally {
      setIsLoading(false);
    }
  };

  const removeCategory = (categoryId: number) => {
    setCategories((prevCategories) =>
      prevCategories.filter((category) => category.id !== categoryId)
    );
  };

  const updateCategory = (category: any) => {
    setCategories((prevCategories) =>
      prevCategories.map((c) => (c.id === category.id ? category : c))
    );
  };

  const addCategory = (category: any) => {
    setCategories((prevCategories) => [...prevCategories, category]);
  };

  return {
    categories,
    isLoading,
    error,
    loadCategories,
    removeCategory,
    updateCategory,
    addCategory
  };
}; 