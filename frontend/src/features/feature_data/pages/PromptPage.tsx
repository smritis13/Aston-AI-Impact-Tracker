import React, { useState } from 'react';
import MainLayout from 'core/components/layout/MainLayout';
import BreadcrumbWidget from 'core/components/shared/BreadcrumbWidget';
import Loading from 'core/components/Loading';
import Error from 'core/components/Error';
import { Button, Modal } from 'react-bootstrap';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { ContentHttpService } from '../services';
import PromptForm from '../components/PromptForm';

const PromptPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<any | undefined>(undefined);

  const { data, isLoading, error } = useQuery(['prompts'], ContentHttpService.getPrompts);
  const prompts = data?.results || [];

  const deleteMutation = useMutation({
    mutationFn: (id: number) => ContentHttpService.deletePrompt(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['prompts']);
    },
  });

  const handleEdit = (prompt: any) => {
    setEditingPrompt(prompt);
    setShowModal(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this prompt?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleAdd = () => {
    setEditingPrompt(undefined);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingPrompt(undefined);
  };

  return (
    <MainLayout>
      <div className="container-fluid">
        <BreadcrumbWidget
          mainTitle={`Prompts (${prompts.length})`}
          breadcrumbs={[
            { title: 'Dashboard', url: '/' },
            { title: 'Prompts' },
          ]}
        />
        <div className="row">
          <div className="col-xl-12">
            <div className="card custom-card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0">Prompts</h5>
                <Button variant="primary" onClick={handleAdd}>
                  <i className="ri-add-line me-1"></i>
                  Add Prompt
                </Button>
              </div>
              <div className="card-body">
                {isLoading && <Loading isLoading={isLoading} />}
                {/* {error && (<Error error={error as string}) />} */}
                {!isLoading && prompts.length === 0 && (
                  <div className="alert alert-info" role="alert">
                    No prompts found. Add a prompt to get started.
                  </div>
                )}
                {prompts.length > 0 && (
                  <div className="table-responsive">
                    <table className="table table-bordered">
                      <thead className="table-light">
                        <tr>
                          <th>ID</th>
                          <th>Title</th>
                          <th>Content</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {prompts.map((prompt: any) => (
                          <tr key={prompt.id}>
                            <td>{prompt.id}</td>
                            <td>{prompt.title}</td>
                            <td style={{ maxWidth: 300, whiteSpace: 'pre-line', overflow: 'hidden', textOverflow: 'ellipsis' }}>{prompt.content}</td>
                            <td>
                              <div className="btn-group">
                                <Button variant="outline-primary" size="sm" onClick={() => handleEdit(prompt)}>
                                  <i className="ri-edit-line"></i>
                                </Button>
                                <Button variant="outline-danger" size="sm" onClick={() => handleDelete(prompt.id)}>
                                  <i className="ri-delete-bin-line"></i>
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      <Modal show={showModal} onHide={handleCloseModal} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{editingPrompt ? 'Edit Prompt' : 'Add New Prompt'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <PromptForm prompt={editingPrompt} onSuccess={handleCloseModal} />
        </Modal.Body>
      </Modal>
    </MainLayout>
  );
};

export default PromptPage; 