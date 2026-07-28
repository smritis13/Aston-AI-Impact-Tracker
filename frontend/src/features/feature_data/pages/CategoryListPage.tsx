import React, { useState } from "react";
import { CategoryHttpService } from "../services/CategoryHttpService";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import DeleteDialog from "core/components/shared/DeleteDialog";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import CategoryForm from "../components/CategoryForm";
import MainLayout from "core/components/layout/MainLayout";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import { useCategories } from "../hooks/useCategories";
import { Link } from "react-router-dom";
const CategoryListPage: React.FC = () => {
  const { categories, isLoading, error, removeCategory, updateCategory, addCategory } = useCategories();
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCategoryId, setEditingCategoryId] = useState<number | undefined>();

  const handleDeleteClick = (categoryId: number) => {
    setSelectedCategoryId(categoryId);
    setIsDeleteOpen(true);
  };

  const handleEditClick = (categoryId: number) => {
    setEditingCategoryId(categoryId);
    setIsFormOpen(true);
  };

  const handleAddClick = () => {
    setEditingCategoryId(undefined);
    setIsFormOpen(true);
  };

  const handleFormSuccess = (category: any) => {
    if (editingCategoryId) {
      updateCategory(category);
    } else {
      addCategory(category);
    }
  };

  return (
    <MainLayout>
      <div className="container-fluid">
        <BreadcrumbWidget
          mainTitle=""
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Categories" },
          ]}
        />
        <div className="row">
          <div className="col-12">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0">Categories</h5>
                <a
                  onClick={handleAddClick}
                  className="btn btn-primary btn-sm d-flex align-items-center"
                >
                  <i className="ri-add-circle-line align-middle me-1"></i>
                  Add Category
                </a>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table text-nowrap table-hover">
                    <thead>
                      <tr>
                        <th scope="col">#</th>
                        <th scope="col">Name</th>
                        <th scope="col">Parent</th>
                        <th scope="col">Created</th>
                        <th scope="col">Updated</th>
                        <th scope="col"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {categories.length > 0 ? (
                        categories.map((category) => (
                          <tr key={category.id}>
                            <td>{category.id}</td>
                            <td>
                              <Link to={`/category/${category.id}`}>
                                {category.name}
                              </Link>
                            </td>
                            <td>
                              {category.parent ? (
                                categories.find((c) => c.id === category.parent)?.name
                              ) : (
                                "-"
                              )}
                            </td>
                            <td>
                              <TimeAgoWidget date={category.created_at} />
                            </td>
                            <td>
                              <TimeAgoWidget date={category.updated_at} />
                            </td>
                            <td>
                              <div className="hstack gap-2">
                                <button
                                  className="btn btn-sm btn-info"
                                  onClick={() => handleEditClick(category.id)}
                                >
                                  <i className="ri-edit-line"></i>
                                </button>
                                <button
                                  className="btn btn-sm btn-danger"
                                  onClick={() => handleDeleteClick(category.id)}
                                >
                                  <i className="ri-delete-bin-5-line"></i>
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={6} className="text-center">
                            No categories found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>

        {selectedCategoryId !== null && (
          <DeleteDialog
            deleteFunction={CategoryHttpService.deleteCategory}
            itemId={selectedCategoryId}
            isOpen={isDeleteOpen}
            setOpen={setIsDeleteOpen}
            notifyDone={() => {
              removeCategory(selectedCategoryId);
            }}
          />
        )}

        <CategoryForm
          isOpen={isFormOpen}
          onClose={() => {
            setIsFormOpen(false);
            setEditingCategoryId(undefined);
          }}
          categoryId={editingCategoryId}
          onSuccess={handleFormSuccess}
        />
      </div>
    </MainLayout>
  );
};

export default CategoryListPage; 