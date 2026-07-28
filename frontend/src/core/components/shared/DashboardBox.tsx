import React from 'react';

interface DashboardBoxProps {
  icon: React.ReactNode;
  title: string;
  value?: string | number;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

const DashboardBox: React.FC<DashboardBoxProps> = ({
  icon,
  title,
  value,
  description,
  action,
  className = '',
}) => {
  return (
    <div className={`dashboard-box card shadow-sm border-0 mb-4 ${className}`} style={{ minHeight: 140 }}>
      <div className="card-body d-flex align-items-center gap-3">
        <div className="dashboard-box-icon d-flex align-items-center justify-content-center rounded-circle bg-primary bg-opacity-10" style={{ width: 56, height: 56 }}>
          <span className="fs-2 text-primary">{icon}</span>
        </div>
        <div className="flex-grow-1">
          <div className="d-flex align-items-center justify-content-between">
            <h5 className="mb-1 fw-semibold">{title}</h5>
            {action && <div>{action}</div>}
          </div>
          {value !== undefined && <div className="fs-4 fw-bold text-dark mb-1">{value}</div>}
          {description && <div className="text-muted small">{description}</div>}
        </div>
      </div>
    </div>
  );
};

export default DashboardBox; 