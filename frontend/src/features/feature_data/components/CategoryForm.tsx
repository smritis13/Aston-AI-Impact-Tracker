import React, { useState, useEffect } from "react";
import { CategoryHttpService, Category } from "../services/CategoryHttpService";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import CustomModal from "core/components/shared/CustomModal";

interface CategoryFormProps {
  isOpen: boolean;
  onClose: () => void;
  categoryId?: number;
  onSuccess?: (category: Category) => void;
}

const CategoryForm: React.FC<CategoryFormProps> = ({ isOpen, onClose, categoryId, onSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [formData, setFormData] = useState({
    name: "",
    parent: "",
  });

  useEffect(() => {
    if (isOpen) {
      loadCategories();
      if (categoryId) {
        loadCategory();
      } else {
        setFormData({ name: "", parent: "" });
      }
    }
  }, [isOpen, categoryId]);

  const loadCategories = async () => {
    try {
      const data = await CategoryHttpService.getCategories();
      setCategories(data);
    } catch (err) {
      setError("Failed to load categories");
    }
  };

  const loadCategory = async () => {
    try {
      setIsLoading(true);
      const category = await CategoryHttpService.getCategory(categoryId!);
      setFormData({
        name: category.name,
        parent: category.parent?.toString() || "",
      });
    } catch (err) {
      setError("Failed to load category");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsLoading(true);
      const categoryData = {
        id: categoryId,
        name: formData.name,
        parent: formData.parent ? parseInt(formData.parent) : undefined,
      };

      const category = await CategoryHttpService.saveCategory(categoryData);

      if (onSuccess) {
        onSuccess(category);
      }
      onClose();
    } catch (err) {
      setError("Failed to save category");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <CustomModal
      isOpen={isOpen}
      onClose={onClose}
      showFooter={false}
      title={categoryId ? "Edit Category" : "Create Category"}
    >
      {isLoading ? (
        <Loading isLoading={isLoading} />
      ) : error ? (
        <Error error={error} />
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="name" className="form-label">Name</label>
            <input
              type="text"
              className="form-control"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="Enter category name"
            />
          </div>

          <div className="mb-3">
            <label htmlFor="parent" className="form-label">Parent Category</label>
            <select
              className="form-select"
              id="parent"
              name="parent"
              value={formData.parent}
              onChange={handleChange}
            >
              <option value="">None</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          <div className="d-flex justify-content-end gap-2">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isLoading}>
              {categoryId ? "Update" : "Create"}
            </button>
          </div>
        </form>
      )}
    </CustomModal>
  );
};

export default CategoryForm; 