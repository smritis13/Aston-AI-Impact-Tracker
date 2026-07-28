import React, { useState } from "react";
import UseDocumentsList from "../hooks/UseDocumentsList";
import Utils from "core/utils";
import DeleteDialog from "core/components/shared/DeleteDialog";
import { DocumentHttpService } from "../services";
import Loading from "core/components/Loading";
import Error from "core/components/Error";

interface DocumentsListProps {
  categoryId?: number;
  searchQuery?: string;
}

const DocumentsList: React.FC<DocumentsListProps> = ({ categoryId, searchQuery }) => {
  const defaultPageSize = 15;
  const [pageNumber, setPageNumber] = useState(1);
  const { data, isLoading, error, refetch } = UseDocumentsList({
    category: categoryId,
    searchQuery,
    page: pageNumber,
    pageSize: defaultPageSize,
  });

  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [documents, setDocuments] = useState<any[]>(data?.results || []);

  React.useEffect(() => {
    if (data?.results) {
      setDocuments(data.results);
    }
  }, [data]);

  if (isLoading) return <Loading isLoading={isLoading} />;
  if (error) return <Error error={error+''}  />;

  const totalPages = Math.ceil((data?.count || 0) / defaultPageSize);

  const handlePageClick = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setPageNumber(page);
    }
  };

  const handleDeleteClick = (docId: number) => {
    setSelectedDocumentId(docId);
    setIsDeleteOpen(true);
  };

  const removeDocumentFromList = (docId: number) => {
    setDocuments((prevDocuments) => prevDocuments.filter((doc) => doc.id !== docId));
  };

  const renderPagination = () => {
    const paginationButtons = [];
    const maxButtonsToShow = 5;

    if (totalPages <= maxButtonsToShow) {
      for (let i = 1; i <= totalPages; i++) {
        paginationButtons.push(
          <button
            key={i}
            className={`btn ${pageNumber === i ? "btn-primary" : "btn-outline-secondary"}`}
            onClick={() => handlePageClick(i)}
          >
            {i}
          </button>
        );
      }
    } else {
      paginationButtons.push(
        <button
          key={1}
          className={`btn ${pageNumber === 1 ? "btn-primary" : "btn-outline-secondary"}`}
          onClick={() => handlePageClick(1)}
        >
          1
        </button>
      );

      if (pageNumber > 3) {
        paginationButtons.push(<span key="dots-start">...</span>);
      }

      for (let i = Math.max(2, pageNumber - 1); i <= Math.min(totalPages - 1, pageNumber + 1); i++) {
        paginationButtons.push(
          <button
            key={i}
            className={`btn ${pageNumber === i ? "btn-primary" : "btn-outline-secondary"}`}
            onClick={() => handlePageClick(i)}
          >
            {i}
          </button>
        );
      }

      if (pageNumber < totalPages - 2) {
        paginationButtons.push(<span key="dots-end">...</span>);
      }

      paginationButtons.push(
        <button
          key={totalPages}
          className={`btn ${pageNumber === totalPages ? "btn-primary" : "btn-outline-secondary"}`}
          onClick={() => handlePageClick(totalPages)}
        >
          {totalPages}
        </button>
      );
    }

    return paginationButtons;
  };

  return (
    <>
      <div className="table-responsive">
        <table className="table text-nowrap table-hover">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Name</th>
              <th scope="col">Size</th>
              <th scope="col">Type</th>
              <th scope="col">Category</th>
              <th scope="col"></th>
            </tr>
          </thead>
          <tbody>
            {documents.length > 0 ? (
              documents.map((doc: any) => (
                <tr key={doc.id}>
                  <td>{doc.id}</td>
                  <td>
                    <div className="d-flex align-items-center">
                      <div className="avatar avatar-sm me-2 avatar-rounded">
                        <img src="/assets/images/user.jpg" alt="img" />
                      </div>
                      <div>
                        <div className="lh-1">
                          <span>{doc.name}</span>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>{Utils.formatFileSize(doc.size) || ""}</td>
                  <td>{doc.file_type}</td>
                  <td>{doc.category?.name || ""}</td>
                  <td>
                    <div className="hstack gap-2 flex-wrap">
                      <a href="#" className="text-info fs-14 lh-1">
                        <i className="ri-edit-line"></i>
                      </a>
                      <a
                        href="#"
                        className="text-danger fs-14 lh-1"
                        onClick={(e) => {
                          e.preventDefault();
                          handleDeleteClick(doc.id);
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
                <td colSpan={6} className="text-center">
                  No documents found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="p-2">
        {totalPages > 1 && (
          <div className="d-flex justify-content-center align-items-center mt-3 gap-2">
            <button
              className="btn btn-outline-secondary"
              onClick={() => handlePageClick(pageNumber - 1)}
              disabled={pageNumber === 1}
            >
              Previous
            </button>

            {renderPagination()}

            <button
              className="btn btn-outline-secondary"
              onClick={() => handlePageClick(pageNumber + 1)}
              disabled={pageNumber === totalPages}
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Delete Dialog */}
      {selectedDocumentId !== null && (
        <DeleteDialog
          deleteFunction={DocumentHttpService.deleteDocument}
          itemId={selectedDocumentId}
          isOpen={isDeleteOpen}
          setOpen={setIsDeleteOpen}
          notifyDone={() => {
            removeDocumentFromList(selectedDocumentId);
          }}
        />
      )}
    </>
  );
};

export default DocumentsList;
