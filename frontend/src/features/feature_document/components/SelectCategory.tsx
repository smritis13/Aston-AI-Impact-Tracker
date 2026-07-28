import React, { useState } from "react";
import UseCategoriesList from "../hooks/UseCategoriesList";

interface SelectCategoryProps {
  onCategorySelect: (categoryId: number | null) => void;
}

const SelectCategory: React.FC<SelectCategoryProps> = ({ onCategorySelect }) => {
  const { data, isLoading, error } = UseCategoriesList();
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);

  if (isLoading) return <p>Loading categories...</p>;
  if (error) return <p>Error loading categories</p>;

  const categories = data.data;
  /**
   * Recursive function to render categories with indentation
   */
  const renderCategories = (categoryList: any[], level = 0) => {
    return categoryList.map((category) => (
      <React.Fragment key={category.id}>
        <option value={category.id}>
          {"—".repeat(level)} {category.name}
        </option>
        {category.subcategories.length > 0 && renderCategories(category.subcategories, level + 1)}
      </React.Fragment>
    ));
  };

  return (
    <select
      className="form-select"
      value={selectedCategory || ""}
      onChange={(e) => {
        const selectedId = e.target.value ? Number(e.target.value) : null;
        setSelectedCategory(selectedId);
        onCategorySelect(selectedId);
      }}
      style={{ width: "300px", padding: "5px" }}
    >
      <option value="">Select a category</option>
      {categories && renderCategories(categories)}
    </select>
  );
};

export default SelectCategory;
