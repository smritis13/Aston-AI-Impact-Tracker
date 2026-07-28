import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { CategoryHttpService, } from "../services/CategoryHttpService";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import DeleteDialog from "core/components/shared/DeleteDialog";
import MainLayout from "core/components/layout/MainLayout";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";

const CategoryDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [category, setCategory] = useState<any | null>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedMetricId, setSelectedMetricId] = useState<number | null>(null);

  useEffect(() => {
    loadData();
  }, [id]);


  const loadData = async () => {
    try {
      setIsLoading(true);
      const [categoryData, metricsData] = await Promise.all([
        CategoryHttpService.getCategory(parseInt(id!)),
        CategoryHttpService.getCategoryMetrics(parseInt(id!)),
      ]);
      setCategory(categoryData);
      setMetrics(metricsData);
    } catch (err) {
      setError("Failed to load category data");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteClick = (metricId: number) => {
    setSelectedMetricId(metricId);
    setIsDeleteOpen(true);
  };

  const removeMetricFromList = (metricId: number) => {
    setMetrics((prevMetrics) =>
      prevMetrics.filter((metric) => metric.id !== metricId)
    );
  };


  return (
    <MainLayout>
      {isLoading && <Loading isLoading={isLoading} />}
      {error && <Error error={error} />}
      {category && (
        <div className="container-fluid">
          <BreadcrumbWidget
            mainTitle=""
            breadcrumbs={[
              { title: "Dashboard", url: "/" },
              { title: "Categories", url: "/category" },
              { title: category.name },
            ]}
          />
          <div className="row">
            <div className="col-12">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="card-title mb-0">{category.name}</h5>
              <div className="card-actions">
                <Link to={`/categories/${category.id}/edit`} className="btn btn-primary me-2">
                  Edit Category
                </Link>
                <Link to={`/categories/${category.id}/metrics/new`} className="btn btn-success">
                  Add Metric
                </Link>
              </div>
            </div>
            <div className="card-body">
              <div className="row">
                <div className="col-12">
                  <h5>Metrics</h5>
                  <div className="table-responsive">
                    <table className="table text-nowrap table-hover">
                      <thead>
                        <tr>
                          <th scope="col">#</th>
                          <th scope="col">Name</th>
                          <th scope="col">Description</th>
                          <th scope="col">Tags</th>
                          <th scope="col"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {/* {metrics.length > 0 ? (
                          metrics.map((metric) => (
                            <tr key={metric.id}>
                              <td>{metric.id}</td>
                              <td>
                                <Link to={`/categories/${category.id}/metrics/${metric.id}/edit`}>
                                  {metric.name}
                                </Link>
                              </td>
                              <td>{metric.description || "-"}</td>
                              <td>
                                <TagsWidget tags={metric.tags} />
                              </td>
                              <td>
                                <div className="hstack gap-2">
                                  <Link
                                    to={`/categories/${category.id}/metrics/${metric.id}/edit`}
                                    className="text-info fs-14 lh-1"
                                  >
                                    <i className="ri-edit-line"></i>
                                  </Link>
                                  <a
                                    href="#"
                                    className="text-danger fs-14 lh-1"
                                    onClick={(e) => {
                                      e.preventDefault();
                                      handleDeleteClick(metric.id);
                                    }}
                                  >
                                    <i className="ri-delete-bin-5-line"></i>
                                  </a>
                                </div>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={5} className="text-center">
                              No metrics found.
                            </td>
                          </tr>
                        )} */}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {selectedMetricId !== null && (
        <DeleteDialog
          deleteFunction={(id) =>
            CategoryHttpService.deleteMetric(id!, id)
          }
          itemId={selectedMetricId}
          isOpen={isDeleteOpen}
          setOpen={setIsDeleteOpen}
          notifyDone={() => {
            removeMetricFromList(selectedMetricId);
          }}
        />
      )}
        </div>
      )}
    </MainLayout>
  );
};

export default CategoryDetailPage; 