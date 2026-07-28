import React, { useState } from "react";
import MainLayout from "core/components/layout/MainLayout";
import ContentList from "../components/ContentList";

const ContentPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>("");

  return (
    <MainLayout>
      <div className="container-fluid">
        <div className="row">
          <div className="col-md-12">
            <div className="card custom-card">
              <div className="card-body">
                <div className="d-flex p-3 flex-wrap gap-2 align-items-center justify-content-between border-bottom">
                  <div>
                    <h6 className="fw-semibold mb-0">Content</h6>
                  </div>
                  <div className="d-flex gap-2 align-items-center">
                    <div className="position-relative">
                      <input
                        type="text"
                        className="form-control"
                        id="input-text"
                        placeholder="Search Content..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                      <i
                        className="ri-search-line position-absolute"
                        style={{
                          right: "10px",
                          top: "50%",
                          transform: "translateY(-50%)",
                          color: "#aaa",
                          cursor: "pointer",
                        }}
                      ></i>
                    </div>
                    <div className="position-relative d-flex gap-2 align-items-center">
                      <input
                        type="date"
                        className="form-control"
                        id="input-text"
                        placeholder="From Date..."
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                      <input
                        type="date"
                        className="form-control"
                        id="input-text"
                        placeholder="To Date..."
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </div>
                  </div>
                </div>
                <ContentList categoryId={1} searchQuery="" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default ContentPage;
