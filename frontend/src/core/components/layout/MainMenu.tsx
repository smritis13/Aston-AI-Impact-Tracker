import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useThemes } from '../../../features/feature_data/hooks/useThemes'
import Utils from 'core/utils';

interface Theme {
  id: number;
  title: string;
}

function MainMenu() {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
    <aside className="app-sidebar sticky" id="sidebar">

            <div className="main-sidebar-header">
                <a href="/dashboard" className="header-logo">
                    <img src="/assets/images/logo-black.svg" alt="Aston University Logo" className="desktop-logo"/>
                    <img src="/assets/images/logo-black.svg" alt="Aston University Logo" className="toggle-logo"/>
                    <img src="/assets/images/logo-white.svg" alt="Aston University Logo" className="desktop-dark"/>
                    <img src="/assets/images/logo-white.svg" alt="Aston University Logo" className="toggle-dark"/>
                    <img src="/assets/images/logo-black.svg" alt="Aston University Logo" className="desktop-white"/>
                    <img src="/assets/images/logo-black.svg" alt="Aston University Logo" className="toggle-white"/>
                </a>
            </div>
            <div className="main-sidebar" id="sidebar-scroll">

                <nav className="main-menu-container nav nav-pills flex-column sub-open">
                    <div className="slide-left" id="slide-left">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="#7b8191" width="24" height="24" viewBox="0 0 24 24"> <path d="M13.293 6.293 7.586 12l5.707 5.707 1.414-1.414L10.414 12l4.293-4.293z"></path> </svg>
                    </div>
                    <ul className="main-menu">
                        <li className="slide__category"><span className="category-name">Main</span></li>

                        {/* <li className="slide">
                            <Link to="/dashboard" className="side-menu__item">
                                <i className="ti ti-device-desktop side-menu__icon"></i>
                                <span className="side-menu__label">Dashboard</span>
                            </Link>
                        </li> */}
                        
                       
                        
                        {/* <li className="slide">
                            <Link to="/filemanager" className="side-menu__item">
                                <i className="ti ti-folder side-menu__icon"></i>
                                <span className="side-menu__label">File Manager</span>
                            </Link>
                        </li> */}
                        
                        {/* <CategoriesMenu /> */}
                        {/* <DataMenu /> */}
                        {/* <WorkflowMenu /> */}
                        {/* <ReportsMenu /> */}

                        

                        <li className="slide">
                            <Link to="/reports/generate/" className="side-menu__item">
                                <i className="ti ti-search side-menu__icon"></i>
                                <span className="side-menu__label">Search Use Case</span>
                            </Link>
                        </li>

                        <li className={`slide ${currentPath.includes('/themes') ? 'active' : ''}`}>
                            <Link to="/themes" className={`side-menu__item ${currentPath.includes('/themes') ? 'active' : ''}`}>
                                <i className="ti ti-server side-menu__icon"></i>
                                <span className="side-menu__label">Use Case Themes</span>
                            </Link>
                        </li>

                        <UsecaseLibraryMenu currentPath={currentPath} />

                        <ImpactCaseStudyMenu currentPath={currentPath} />


                    </ul>
                    <div className="slide-right" id="slide-right"><svg xmlns="http://www.w3.org/2000/svg" fill="#7b8191" width="24" height="24" viewBox="0 0 24 24"> <path d="M10.707 17.707 16.414 12l-5.707-5.707-1.414 1.414L13.586 12l-4.293 4.293z"></path> </svg></div>
                </nav>

            </div>

        </aside>
  )
}


const DataMenu = () => {
    const [isOpen, setIsOpen] = useState(false);
  
    const handleClick = (e:any) => {
      e.preventDefault(); // Prevents the "#" link from navigating
      setIsOpen((prev) => !prev);
    };
  
    return (
      <li className={`slide has-sub ${isOpen ? "open" : ""}`}>
        {/* Toggle button/anchor */}
        <a href="#" className="side-menu__item" onClick={handleClick}>
            <i className="ti ti-folder side-menu__icon"></i>
          <span className="side-menu__label">Data</span>
          <i className="fe fe-chevron-right side-menu__angle"></i>
        </a>
  
        {/* Conditionally apply the 'open' class based on state */}
        <ul className={`slide-menu child1 ${isOpen ? "open" : ""}`}>
          
          <li className="slide">
            <Link to="/documents" className="side-menu__item">
              
              <span className="side-menu__label">Documents</span>
            </Link>
          </li>
          
          <li className="slide">
            <Link to="/content" className="side-menu__item">
              <span className="side-menu__label">Content</span>
            </Link>
          </li>
          <li className="slide">
            <Link to="/insights" className="side-menu__item">
              <span className="side-menu__label">Use Cases</span>
            </Link>
          </li>
        </ul>
      </li>
    );
  };

  const CategoriesMenu = () => {
    const [isOpen, setIsOpen] = useState(false);
  
    const handleClick = (e:any) => {
      e.preventDefault(); // Prevents the "#" link from navigating
      setIsOpen((prev) => !prev);
    };
  
    return (
      <li className={`slide has-sub ${isOpen ? "open" : ""}`}>
        {/* Toggle button/anchor */}
        <a href="#" className="side-menu__item" onClick={handleClick}>
            <i className="ti ti-list side-menu__icon"></i>
          <span className="side-menu__label">Categories</span>
          <i className="fe fe-chevron-right side-menu__angle"></i>
        </a>
  
        {/* Conditionally apply the 'open' class based on state */}
        <ul className={`slide-menu child1 ${isOpen ? "open" : ""}`}>
          
          <li className="slide">
            <Link to="/category" className="side-menu__item">
              <span className="side-menu__label">All Categories</span>
            </Link>
          </li>
        </ul>
      </li>
    );
  };
  
  const WorkflowMenu = () => {
    const [isOpen, setIsOpen] = useState(false);
  
    const handleClick = (e:any) => {
      e.preventDefault(); // Prevents the "#" link from navigating
      setIsOpen((prev) => !prev);
    };

    return (
        <li className={`slide has-sub ${isOpen ? "open" : ""}`}>
            <a href="#" className="side-menu__item" onClick={handleClick}>
                <i className="ti ti-pyramid  side-menu__icon"></i>
                <span className="side-menu__label">Agentic AI</span>
                <i className="fe fe-chevron-right side-menu__angle"></i>
            </a>
            <ul className={`slide-menu child1 ${isOpen ? "open" : ""}`}>
              <li className="slide">
                <Link to="/reports" className="side-menu__item">
                  <span className="side-menu__label">Reports</span>
                </Link>
              </li>
              <li className="slide">
                <Link to="/reports/sdlc" className="side-menu__item">
                  <span className="side-menu__label">SDLC</span>
                </Link>
              </li>
                {/* <li className="slide">
                    <Link to="/workflows" className="side-menu__item">
                        <span className="side-menu__label">Workflows</span>
                    </Link>
                </li>
                <li className="slide">
                    <Link to="/workflows/agents" className="side-menu__item">
                        <span className="side-menu__label">Agents</span>
                    </Link>
                </li> */}
            </ul>
        </li>
    );
};

const ReportsMenu = () => {
    const [isOpen, setIsOpen] = useState(false);

    const handleClick = (e:any) => {
        e.preventDefault(); // Prevents the "#" link from navigating
        setIsOpen((prev) => !prev);
    };

    return (
        <li className={`slide has-sub ${isOpen ? "open" : ""}`}>
            <a href="#" className="side-menu__item" onClick={handleClick}>
                <i className="ti ti-file-report side-menu__icon"></i>
                <span className="side-menu__label">Reports</span>
                <i className="fe fe-chevron-right side-menu__angle"></i>
            </a>
            <ul className={`slide-menu child1 ${isOpen ? "open" : ""}`}>
                    <li className="slide">
                        <Link to="/reports/generate" className="side-menu__item">
                            <span className="side-menu__label">Generate Report</span>
                        </Link>
                    </li>
                    <li className="slide">
                        <Link to="/reports" className="side-menu__item">
                            <span className="side-menu__label">All Reports</span>
                        </Link>
                    </li>
            </ul>
        </li>
    );
};

const UsecaseLibraryMenu = ({ currentPath }: { currentPath: string }) => {
    const [isOpen, setIsOpen] = useState(false);
    const { themes, loading, error } = useThemes({ page: 1, pageSize: 100, featured: true }); // Get featured themes

    const handleClick = (e:any) => {
        e.preventDefault();
        setIsOpen((prev) => !prev);
    };

    const isActive = currentPath.startsWith('/usecases') || currentPath === '/reports/generate';
    const hasThemes = Array.isArray(themes) && themes.length > 0;
    const getThemePath = (theme: Theme) => `/usecases/${theme.id}/${encodeURIComponent(theme.title.toLowerCase().replace(/\s+/g, '-'))}`;

    return (
        <li className={`slide has-sub ${isOpen || isActive ? "open" : ""}`}>
            <Link to="/usecases" className={`side-menu__item ${isActive ? 'active' : ''}`} onClick={handleClick}>
                <i className="ti ti-book side-menu__icon"></i>
                  <span className="side-menu__label">Featured Use Cases</span>

                <i className="fe fe-chevron-right side-menu__angle"></i>
            </Link>
            <ul className={`slide-menu child1 ${isOpen || isActive ? "open" : ""}`}>
                
                {loading ? (
                    <li className="slide">
                        <span className="side-menu__item">
                            <span className="side-menu__label">Loading themes...</span>
                        </span>
                    </li>
                ) : error ? (
                    <li className="slide">
                        <span className="side-menu__item">
                            <span className="side-menu__label" style={{ color: '#999' }}>Error loading themes</span>
                        </span>
                    </li>
                ) : hasThemes ? (
                  themes.map((theme: Theme) => (
                        <li 
                            key={theme.id} 
                            className={`slide ${currentPath.startsWith(`/usecases/${theme.id}`) ? 'active' : ''}`}
                        >
                            <Link 
                                to={getThemePath(theme)} 
                                className={`side-menu__item ${currentPath.startsWith(`/usecases/${theme.id}`) ? 'active' : ''}`}
                            >
                                <span className="side-menu__label">{theme.title.replace('-', ' ')}</span>
                            </Link>
                        </li>
                    ))
                ) : (
                    <li className="slide">
                        <span className="side-menu__item">
                            <span className="side-menu__label" style={{ color: '#999' }}>No themes available</span>
                        </span>
                    </li>
                )}
                {/* <li className={`slide ${currentPath === '/reports/generate' ? 'active' : ''}`}>
                    <Link to="/reports/generate" className={`side-menu__item ${currentPath === '/reports/generate' ? 'active' : ''}`}>
                        <span className="side-menu__label">Generate Usecase</span>
                    </Link>
                </li> */}
            </ul>
        </li>
    );
};

const ImpactCaseStudyMenu = ({ currentPath }: { currentPath: string }) => {
    const [isOpen, setIsOpen] = useState(false);

    const handleClick = (e: any) => {
        e.preventDefault();
        setIsOpen((prev) => !prev);
    };

    const isActive = currentPath.includes('/impact-case-study');

    return (
        <li className={`slide has-sub ${isOpen || isActive ? "open" : ""}`}>
            <a href="#" className={`side-menu__item ${isActive ? 'active' : ''}`} onClick={handleClick}>
                <i className="ti ti-report side-menu__icon"></i>
                <span className="side-menu__label">Impact Case Studies</span>
                <i className="fe fe-chevron-right side-menu__angle"></i>
            </a>
            <ul className={`slide-menu child1 ${isOpen || isActive ? "open" : ""}`}>
                <li className={`slide ${currentPath === '/impact-case-study' ? 'active' : ''}`}>
                    <Link to="/impact-case-study" className={`side-menu__item ${currentPath === '/impact-case-study' ? 'active' : ''}`}>
                        <span className="side-menu__label">Research</span>
                    </Link>
                </li>
                <li className="slide">
                    <Link to="/impact-case-studies" className="side-menu__item">
                        <span className="side-menu__label">History</span>
                    </Link>
                </li>
            </ul>
        </li>
    );
};

export default MainMenu
