import React from "react";
import { useParams } from "react-router-dom";
import MainLayout from "core/components/layout/MainLayout";
import BlogDetailsAside from "../components/BlogDetailsAside";
import UseContent from "../hooks/UseContent";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import MarkdownRenderer from "core/components/shared/MarkdownRenderer";

const ContentDetailsPage: React.FC = () => {
  // Extract contentId from URL parameters.
  const { contentId } = useParams<{ contentId: string }>();

  // Convert contentId to a number and load content.
  const id = Number(contentId);
  const { data: content, isLoading, error } = UseContent(id);

  if (isLoading) return <Loading isLoading={isLoading} />;
  if (error) return <Error error={error + ""} />;

  return (
    <MainLayout>
      <div className="container-fluid">
      <BreadcrumbWidget
        mainTitle={content?.title}
        breadcrumbs={[
          { title: "Content List", url: "/content" },
          { title: "View Content" } // No URL means it's active
        ]}
      />

        <div className="row">
          <div className="col-xl-9">
            <div className="row">
              <div className="col-xl-12">
                <div className="card custom-card">
                  <a href="#">
                    <img
                      src={content?.image || "/placeholder.jpg"}
                      className="blog-details-img card-img-top"
                      alt={content?.title}
                    />
                  </a>
                  <div className="card-header d-block border-bottom border-block-end-dashed">
                    <p className="fs-22 fw-semibold mb-1">
                      {content?.title}
                    </p>
                    <div className="d-sm-flex align-items-center">
                      <div className="d-flex align-items-center flex-fill">
                        <span className="me-3 ">
                          <i className="ti ti-world text-4-5"></i>
                        </span>
                        <div>
                          <a href={content?.url} target="_blank" className="mb-0 fw-semibold fs-14">
                            {/* Assuming author name comes from content or hard-coded */}
                            {content?.url} -{" "}
                            <span className="fs-12 text-muted fw-normal">
                              <TimeAgoWidget date={content?.scraped_at} />
                            </span>
                          </a>
                        </div>
                      </div>
                      {/* <div className="mt-sm-0 mt-2">
                        <span className="badge bg-success-transparent me-3">
                          <i className="ri-thumb-up-line me-1 align-middle d-inline-block"></i>{" "}
                          32 Likes
                        </span>
                        <span className="badge bg-info-transparent me-3">
                          <i className="ri-chat-4-line me-1 align-middle d-inline-block"></i>{" "}
                          10 Comments
                        </span>
                      </div> */}
                    </div>
                  </div>
                  <div className="card-body">
                    <h6 className="fw-semibold">
                      {content?.summary}
                    </h6>
                    <p className="mb-5 text-muted">
                      <MarkdownRenderer markdownText={content?.original_content ?? content?.content} />
                    </p>
                    {/* Additional content or blockquote as needed */}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <BlogDetailsAside />
        </div>
      </div>
    </MainLayout>
  );
};

export default ContentDetailsPage;
