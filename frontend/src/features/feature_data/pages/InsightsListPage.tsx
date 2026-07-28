import React from "react";
import MainLayout from "core/components/layout/MainLayout";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import UseInsights from "../hooks/useInsights";
import UrlSourceWidget from "../components/UrlSourceWidget";

const InsightsListPage: React.FC = () => {
  const { data: insights, isLoading, error } = UseInsights();

  if (isLoading) return <Loading isLoading={isLoading} />;
  if (error) return <Error error={error + ""} />;

  return (
    <MainLayout>
      <div className="container-fluid">
        <BreadcrumbWidget
          mainTitle="Insights List"
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "AI & Retail Insights" },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            <div className="card custom-card">

              <div>
                
              </div>

              <div className="card-body">
              {insights && insights.results.length > 0 ? (
                  <div className="table-responsive">
                    <table className="table table-bordered">
                      <thead className="table-light">
                        <tr>
                          <th>ID</th>
                          <th style={{width: "100px"}}>Date</th>
                          <th>Company</th>
                          <th>Tool</th>
                          <th>Methodology</th>
                          <th>Department</th>
                          <th>Performance Improvement</th>
                          <th style={{width: "400px"}}>Additional Details</th>
                          <th>Source</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {insights.results.map((insight: any) => (
                          <tr key={insight.id}>
                            <td>{insight.id}</td>
                            <td>
                              {getStructuredValue(insight.structured_data, "Date")}
                            </td>
                            <td>{getStructuredValue(insight.structured_data, "Company")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Tool")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Methodology")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Department")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Performance_Improvement")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Additional_Details")}</td>
                            <td>
                              <UrlSourceWidget source={getStructuredValue(insight.structured_data, "Source")} />
                            </td>
                            <td><TimeAgoWidget date={insight.created_at} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>No insights available.</p>
                )}
                {/* {insights && insights.results.length > 0 ? (
                  <div className="table-responsive">
                    <table className="table table-bordered">
                      <thead className="table-light">
                        <tr>
                          <th>ID</th>
                          <th>Date</th>
                          <th>Sector</th>
                          <th>Company</th>
                          <th>Function</th>
                          <th>AI Maturity</th>
                          <th>Use Case</th>
                          <th>Impact</th>
                          <th>Source</th>
                        </tr>
                      </thead>
                      <tbody>
                        {insights.results.map((insight: any) => (
                          <tr key={insight.id}>
                            <td>{insight.id}</td>
                            <td>
                              <TimeAgoWidget date={insight.created_at} />
                            </td>
                            <td>{getStructuredValue(insight.structured_data, "Sector")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Company")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Function")}</td>
                            <td>{getStructuredValue(insight.structured_data, "AI Maturity")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Use Case")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Impact")}</td>
                            <td>{getStructuredValue(insight.structured_data, "Source")}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>No insights available.</p>
                )} */}
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

// Helper function to safely extract structured values
const getStructuredValue = (data: Record<string, any>, key: string): string => {
  return data && data[key] ? data[key] : "N/A";
};

export default InsightsListPage;
