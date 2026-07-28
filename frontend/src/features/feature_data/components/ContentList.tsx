import React, { useState, useEffect } from "react";
import DeleteDialog from "core/components/shared/DeleteDialog";
import { ContentHttpService } from "../services";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import UseContentList from "../hooks/useContentList";
import TagsWidget from "core/components/forms/TagsWidget";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import { Link } from "react-router-dom";

interface ContentListProps {
  categoryId?: number;
  searchQuery?: string;
}

const ContentList: React.FC<ContentListProps> = ({ categoryId, searchQuery }) => {
  const defaultPageSize = 15;
  const [pageNumber, setPageNumber] = useState(1);
  const { data, isLoading, error, refetch } = UseContentList({
    category: categoryId,
    searchQuery,
    page: pageNumber,
    pageSize: defaultPageSize,
  });

  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedContentId, setSelectedContentId] = useState<number | null>(null);
  const [contents, setContents] = useState<any[]>(data?.results || []);

  useEffect(() => {
    if (data?.results) {
      setContents(data.results);
    }
  }, [data]);

  if (isLoading) return <Loading isLoading={isLoading} />;
  if (error) return <Error error={error + ""} />;

  const totalPages = Math.ceil((data?.count || 0) / defaultPageSize);

  const handlePageClick = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setPageNumber(page);
    }
  };

  const handleDeleteClick = (contentId: number) => {
    setSelectedContentId(contentId);
    setIsDeleteOpen(true);
  };

  const removeContentFromList = (contentId: number) => {
    setContents((prevContents) =>
      prevContents.filter((content) => content.id !== contentId)
    );
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
              <th scope="col"></th>
              <th scope="col">Title</th>
              <th scope="col">Tags</th>
              <th scope="col">Category</th>
              <th scope="col">Scraped at</th>
              <th scope="col"></th>
            </tr>
          </thead>
          <tbody>
            {contents.length > 0 ? (
              contents.map((content: any) => (
                <tr key={content.id}>
                  <td>{content.id}</td>
                  <td>
                    {content.image ? (
                      <img
                        src={content.image}
                        alt={content.title}
                        style={{ width: "80px", height: "auto", borderRadius: "4px" }}
                      />
                    ) : (
                      ""
                    )}
                  </td>
                  <td><Link to={`/content/${content.id}`}>{content.title}</Link></td>
                  
                  <td className="text-wrap"><TagsWidget tags={content.tags} /></td>
                  <td><span className="badge bg-light me-1">{content.category?.name || ""}</span></td>
                  <td><TimeAgoWidget date={content.scraped_at} /></td>
                  
                  <td>
                    <div className="hstack gap-2 flex-wrap">
                      <a href={`/content/${content.id}/edit`} className="text-info fs-14 lh-1">
                        <i className="ri-edit-line"></i>
                      </a>
                      <a
                        href="#"
                        className="text-danger fs-14 lh-1"
                        onClick={(e) => {
                          e.preventDefault();
                          handleDeleteClick(content.id);
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
                <td colSpan={7} className="text-center">
                  No content found.
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
      {selectedContentId !== null && (
        <DeleteDialog
          deleteFunction={ContentHttpService.deleteContent}
          itemId={selectedContentId}
          isOpen={isDeleteOpen}
          setOpen={setIsDeleteOpen}
          notifyDone={() => {
            removeContentFromList(selectedContentId);
          }}
        />
      )}
    </>
  );
};

export default ContentList;
