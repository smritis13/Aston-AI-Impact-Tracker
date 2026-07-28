import React from "react";
import { Link } from "react-router-dom";

export interface BreadcrumbItem {
  title: string;
  url?: string;
}

export interface BreadcrumbWidgetProps {
  mainTitle: string;
  breadcrumbs: BreadcrumbItem[];
  titleClassName?: string;
  subTitle?: string;
}

const BreadcrumbWidget: React.FC<BreadcrumbWidgetProps> = ({ mainTitle, breadcrumbs, titleClassName, subTitle }) => {
  const breadcrumbItems = Array.isArray(breadcrumbs) ? breadcrumbs : [];

  return (
    <div className="d-md-flex d-block align-items-center justify-content-between my-4 page-header-breadcrumb">
      <h1 
        className={`page-title fw-semibold fs-18 mb-0 ${titleClassName}`} 
        onClick={(e) => {
          const target = e.currentTarget;
          if (target.style.whiteSpace === "nowrap") {
            target.style.whiteSpace = "normal";
            target.style.cursor = "default";
          } else {
            target.style.whiteSpace = "nowrap";
            target.style.cursor = "pointer";
          }
        }}
        style={{
          whiteSpace: mainTitle.split(" ").length > 20 ? "nowrap" : "normal",
          overflow: "hidden",
          textOverflow: "ellipsis",
          cursor: mainTitle.split(" ").length > 20 ? "pointer" : "default"
        }}
      >
        {mainTitle}
        {subTitle && (
          <small className="ms-md-1 ms-0 text-muted" style={{ fontSize: "12px" }}>{subTitle}</small>
        )}
      </h1>
      
      <div className="ms-md-1 ms-0">
        <nav>
          <ol className="breadcrumb mb-0">
            {breadcrumbItems.map((item, index) => {
              const isLast = index === breadcrumbItems.length - 1;
              return (
                <li
                  key={index}
                  className={`breadcrumb-item ${isLast ? "active" : ""}`}
                  aria-current={isLast ? "page" : undefined}
                >
                  {item.url && !isLast ? (
                    <Link to={item.url}>{item.title}</Link>
                  ) : (
                    item.title
                  )}
                </li>
              );
            })}
          </ol>
        </nav>
      </div>
    </div>
  );
};

export default BreadcrumbWidget;
