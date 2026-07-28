import React from "react";
import MainLayout from "core/components/layout/MainLayout";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import useWorkflows from "../hooks/useWorkflows";
import { Link } from "react-router-dom";
import { Workflow } from "../hooks/useWorkflows";

const WorkflowListPage: React.FC = () => {
  const { data: workflows, isLoading, error } = useWorkflows();

  if (isLoading) return <Loading isLoading={isLoading} />;
  if (error) return <Error error={error + ""} />;

  return (
    <MainLayout>
      <div className="container-fluid">
        <BreadcrumbWidget
          mainTitle="Workflows List"
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Workflows" },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            <div className="card custom-card">
              <div className="card-body">
                {workflows && workflows?.count > 0 ? (
                  <div className="table-responsive">
                    <table className="table table-bordered">
                      <thead className="table-light">
                        <tr>
                          <th>ID</th>
                          <th>Name</th>
                          <th>Description</th>
                          <th>Status</th>
                          <th>Created At</th>
                        </tr>
                      </thead>
                      <tbody>
                        {workflows.results.map((workflow: Workflow) => (
                          <tr key={workflow.id}>
                            <td>{workflow.id}</td>
                            <td>
                              <Link to={`/workflow/${workflow.id}`}>
                                {workflow.name}
                              </Link>
                            </td>
                            <td>{workflow.description}</td>
                            <td>{workflow.status}</td>
                            <td>
                              <TimeAgoWidget date={workflow.created_at} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>No workflows available.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default WorkflowListPage;