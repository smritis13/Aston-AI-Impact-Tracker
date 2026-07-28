import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "core/components/layout/MainLayout";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import ExpandableDescription from "core/components/shared/ExpandableDescription";
import useReports from "../hooks/useReports";
import { Link } from "react-router-dom";
import { ContentHttpService } from "../services";
import DeleteDialog from "core/components/shared/DeleteDialog";

const ReportListPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: reports, isLoading, error, refetch } = useReports();
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);

  const handleDeleteClick = (reportId: number) => {
    setSelectedReportId(reportId);
    setIsDeleteOpen(true);
  };

  const removeReportFromList = (reportId: number) => {
    if (reports?.results) {
      reports.results = reports.results.filter((report: any) => report.id !== reportId);
    }
  };

  return (
    <MainLayout>
      <div className="container">
        <BreadcrumbWidget
          mainTitle="Reports List"
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Reports" },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            {isLoading && <Loading isLoading={isLoading} />}
            {error && <Error error={error + ""} />}
            {reports && reports.results.length > 0 && (
            <div className="card custom-card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0">Reports</h5>
                <Link
                  to="/reports/generate"
                  className="btn btn-primary btn-sm d-flex align-items-center"
                >
                  <i className="ri-add-circle-line align-middle me-1"></i>
                  Add Report
                </Link>
              </div>
              
              <div className="card-body">
                {reports && reports.results.length > 0 ? (
                  <div className="table-responsive">
                    <table className="table table-bordered">
                      <thead className="table-light">
                        <tr>
                          <th>ID</th>
                          <th>Query</th>
                          <th>Created At</th>
                          <th style={{width: "100px"}}></th>
                        </tr>
                      </thead>
                      <tbody>
                        {reports.results.map((report : any) => (
                          <tr 
                            key={report.id}
                            onClick={() => navigate(`/report/${report.id}`)}
                            style={{ cursor: 'pointer' }}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                navigate(`/report/${report.id}`);
                              }
                            }}
                          >
                            <td><Link to={`/report/${report.id}`}>{report.id}</Link></td>
                            <td style={{maxWidth: "300px"}}>
                              <Link to={`/report/${report.id}`}>
                                <ExpandableDescription text={report.query} maxLength={50} />
                              </Link>
                            </td>
                            <td>
                              <TimeAgoWidget date={report.created_at} />
                            </td>
                            <td style={{display: "flex", gap: "5px"}}>
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteClick(report.id);
                                }} 
                                className="btn btn-danger btn-sm"
                              >
                                <i className="ri-delete-bin-line align-middle me-1"></i>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>No reports available.</p>
                )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedReportId !== null && (
        <DeleteDialog
          deleteFunction={ContentHttpService.deleteReport}
          itemId={selectedReportId}
          isOpen={isDeleteOpen}
          setOpen={setIsDeleteOpen}
          notifyDone={() => {
            removeReportFromList(selectedReportId);
            refetch();
          }}
        />
      )}
    </MainLayout>
  );
};

export default ReportListPage;
