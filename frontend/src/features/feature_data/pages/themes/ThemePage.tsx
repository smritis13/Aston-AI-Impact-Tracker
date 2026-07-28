import React, { useState } from 'react';
import { useThemes } from '../../hooks/useThemes';
import MainLayout from "core/components/layout/MainLayout";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import Pagination from 'core/components/shared/Pagination';
import { Button, Modal } from 'react-bootstrap';
import ThemeForm from '../../components/ThemeForm';
import { useMutation, useQueryClient } from 'react-query';
import { ContentHttpService, Theme } from '../../services';
import { Link } from 'react-router-dom';
import './ThemePage.css';

const ThemePage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(30);
  const [viewMode, setViewMode] = useState<'active' | 'trash'>('active');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingTheme, setEditingTheme] = useState<Theme | undefined>(undefined);
  const [expandedThemeIds, setExpandedThemeIds] = useState<Set<number>>(new Set());
  const queryClient = useQueryClient();

  const { themes, totalCount, loading, error,refetch } = useThemes({ page, pageSize, deleted: viewMode === 'trash' });


  const deleteMutation = useMutation({
    mutationFn: (themeId: number) => ContentHttpService.deleteTheme(themeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['themes'] });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (themeId: number) => ContentHttpService.restoreTheme(themeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['themes'] });
    },
  });

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleViewModeChange = (mode: 'active' | 'trash') => {
    setViewMode(mode);
    setPage(1);
  };

  const handleEdit = (theme: Theme) => {
    setEditingTheme(theme);
    setShowAddModal(true);
  };

  const handleDelete = async (themeId: number) => {
    if (window.confirm('Are you sure you want to delete this theme? It will move to Trash, and its reports/use cases will go with it until restored.')) {
      await deleteMutation.mutateAsync(themeId);
    }
  };

  const handleRestore = async (themeId: number) => {
    try {
      await restoreMutation.mutateAsync(themeId);
    } catch (err: any) {
      window.alert(err?.message || 'Failed to restore theme');
    }
  };

  const handleCloseModal = () => {
    refetch();
    setShowAddModal(false);
    setEditingTheme(undefined);
  };

  const toggleThemeExpanded = (themeId: number) => {
    const newExpanded = new Set(expandedThemeIds);
    if (newExpanded.has(themeId)) {
      newExpanded.delete(themeId);
    } else {
      newExpanded.add(themeId);
    }
    setExpandedThemeIds(newExpanded);
  };

  const shouldCollapseDescription = (description: string | undefined): boolean => {
    return Boolean(description && description.length > 120);
  };

  return (
    <MainLayout>
      <div className="container-fluid">
        <BreadcrumbWidget
          mainTitle={`Themes (${totalCount})`}
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Themes" },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            <div className="card custom-card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <div className="btn-group">
                  <Button
                    variant={viewMode === 'active' ? 'primary' : 'outline-primary'}
                    size="sm"
                    onClick={() => handleViewModeChange('active')}
                  >
                    Themes
                  </Button>
                  <Button
                    variant={viewMode === 'trash' ? 'primary' : 'outline-primary'}
                    size="sm"
                    onClick={() => handleViewModeChange('trash')}
                  >
                    <i className="ri-delete-bin-line me-1"></i>
                    Trash
                  </Button>
                </div>
                {viewMode === 'active' && (
                  <Button
                    variant="primary"
                    onClick={() => setShowAddModal(true)}
                  >
                    <i className="ri-add-line me-1"></i>
                    Add Theme
                  </Button>
                )}
              </div>

              <div className="card-body">
                {loading && <Loading isLoading={loading} />}

                {/* {error && (<Error error={error as string} />)} */}

                {!loading && (!themes || themes.length === 0) && (
                  <div className="alert alert-info" role="alert">
                    {viewMode === 'trash'
                      ? 'Trash is empty. Deleted themes will show up here and can be restored.'
                      : 'No themes found. Add a theme to get started.'}
                  </div>
                )}
                
                {themes && themes.length > 0 && (
                  <div className="table-responsive">
                    <table className="table table-bordered">
                      <thead className="table-light">
                        <tr>
                          <th>ID</th>
                          <th>Title</th>
                          <th>Description</th>
                          <th>Featured</th>
                          <th>Created</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {themes.map((theme) => {
                          const isExpanded = expandedThemeIds.has(theme.id);
                          const isCollapsible = shouldCollapseDescription(theme.description);
                          
                          return (
                            <tr key={theme.id}>
                              <td>{theme.id}</td>
                              <td>
                                <Link title="View use cases" to={`/usecases/${theme.id}/${theme.title.replace(/\s+/g, '-')}`}>
                                  {theme.title}
                                </Link>
                              </td>
                              <td style={{ maxWidth: '520px', wordWrap: 'break-word' }}>
                                <div
                                  className={!isExpanded ? "two-line-description" : undefined}
                                >
                                  {theme.description || ''}
                                </div>
                                {isCollapsible && (
                                  <Button
                                    variant="link"
                                    size="sm"
                                    className="p-0 mt-1"
                                    onClick={() => toggleThemeExpanded(theme.id)}
                                    style={{ textDecoration: 'none' }}
                                  >
                                    {isExpanded ? 'show less' : 'show more'}
                                  </Button>
                                )}
                              </td>
                              <td>
                                {theme.featured ? (
                                  <i className="ri-star-fill text-warning"></i>
                                ) : (
                                  <i className="ri-star-line text-muted"></i>
                                )}
                              </td>
                              <td>
                                <TimeAgoWidget date={theme.created_at} />
                              </td>
                              <td>
                                <div className="btn-group">
                                  {viewMode === 'trash' ? (
                                    <Button
                                      variant="outline-success"
                                      size="sm"
                                      onClick={() => handleRestore(theme.id)}
                                    >
                                      <i className="ri-arrow-go-back-line me-1"></i>
                                      Restore
                                    </Button>
                                  ) : (
                                    <>
                                      <Button
                                        variant="outline-primary"
                                        size="sm"
                                        onClick={() => handleEdit(theme)}
                                      >
                                        <i className="ri-edit-line"></i>
                                      </Button>
                                      <Button
                                        variant="outline-danger"
                                        size="sm"
                                        onClick={() => handleDelete(theme.id)}
                                      >
                                        <i className="ri-delete-bin-line"></i>
                                      </Button>
                                    </>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>

                    <div className="d-flex justify-content-between align-items-center mt-3">
                      <Pagination
                        currentPage={page}
                        totalItems={totalCount}
                        pageSize={pageSize}
                        onPageChange={handlePageChange}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <Modal show={showAddModal} onHide={handleCloseModal} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{editingTheme ? 'Edit Theme' : 'Add New Theme'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ThemeForm 
            theme={editingTheme}
            onSuccess={handleCloseModal}
          />
        </Modal.Body>
      </Modal>
    </MainLayout>
  );
};

export default ThemePage; 
