import MainLayout from 'core/components/layout/MainLayout'
import React from 'react'
import DashboardBox from 'core/components/shared/DashboardBox';
import { Link } from 'react-router-dom';
import { useThemes } from 'features/feature_data/hooks/useThemes';



const dashboardItems = [
  {
    to: '/themes',
    icon: <i className="bi bi-server"></i>,
    title: 'Use Case Themes',
    description: 'Browse and manage use case themes.'
  },
  {
    to: '/reports/generate',
    icon: <i className="bi bi-search"></i>,
    title: 'Search Use Case',
    description: 'Generate and search for use cases.'
  },
];

const useCaseLibraryItem = {
  to: '/usecases',
  icon: <i className="bi bi-book"></i>,
  title: 'Use Case Library',
  description: 'Explore all use cases.',
};

type Props = {}

const DashboardPage = (props: Props) => {
  // Fetch featured themes for sub-menu
  const { themes: featuredThemes, loading } = useThemes({ page: 1, pageSize: 8, featured: true });

  return (
    <MainLayout>
      <div className="d-md-flex d-block align-items-center justify-content-between my-4 page-header-breadcrumb">
        <h1 className="page-title fw-semibold fs-18 mb-0">Dashboard</h1>
        <div className="ms-md-1 ms-0">
          <nav>
            <ol className="breadcrumb mb-0">
              <li className="breadcrumb-item"><a href="/dashboard">Dashboard</a></li>
              <li className="breadcrumb-item active" aria-current="page">Dashboard</li>
            </ol>
          </nav>
        </div>
      </div>
      {/* Main dashboard items */}
      <div className="row g-4">
        {dashboardItems.map((item) => (
          <div className="col-12 col-sm-6 col-lg-4 col-xl-3" key={item.to}>
            <Link to={item.to} style={{ textDecoration: 'none' }}>
              <DashboardBox
                icon={item.icon}
                title={item.title}
                description={item.description}
                className="h-100 hover-shadow"
              />
            </Link>
          </div>
        ))}
      </div>
      {/* Use Case Library and Featured Themes */}
      <h4 className="mt-5 mb-3">Use Case Library & Featured Themes</h4>
      <div className="row g-4">
        {/* Use Case Library main box */}
        <div className="col-12 col-sm-6 col-lg-4 col-xl-3">
          <Link to={useCaseLibraryItem.to} style={{ textDecoration: 'none' }}>
            <DashboardBox
              icon={useCaseLibraryItem.icon}
              title={useCaseLibraryItem.title}
              description={useCaseLibraryItem.description}
              className="h-100 hover-shadow"
            />
          </Link>
          {/* Render subItems */}
          
        </div>
        {/* Featured Themes as dashboard boxes */}
        {!loading && featuredThemes && featuredThemes.length > 0 && featuredThemes.map((theme) => (
          <div className="col-12 col-sm-6 col-lg-4 col-xl-3" key={theme.id}>
            <Link to={`/usecases/${theme.id}/${theme.title.toLowerCase().replace(/\s+/g, '-')}`} style={{ textDecoration: 'none' }}>
              <DashboardBox
                icon={<i className="bi bi-star-fill text-warning"></i>}
                title={theme.title}
                description={theme.description || 'Featured use case theme.'}
                className="h-100 hover-shadow border border-warning"
              />
            </Link>
          </div>
        ))}
      </div>
    </MainLayout>
  )
}

export default DashboardPage