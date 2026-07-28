import React from 'react'
import useToggleSidemenu from 'core/hooks/useToggleSidemenu';
import useTheme from 'core/hooks/useTheme';

function Header() {
    const { toggleMenu, isMenuClosed } = useToggleSidemenu();
    const { toggleTheme, currentTheme } = useTheme();

    return (
        <header className="app-header">
                <div className="main-header-container container-fluid">
                    <div className="header-content-left">
                        <div className="header-element">
                            <a aria-label="Hide Sidebar" onClick={toggleMenu} className="sidebar-toggle" href="#">
                                <i className={`ti ti-layout-sidebar-${isMenuClosed ? 'left' : 'right'}-expand fs-20`}></i>
                            </a>
                        </div>
                    </div>

                    <div className="header-content-right">
                        <div className="header-element header-search d-block d-lg-none">
                            <a href="#jsvoid" className="header-link" data-bs-toggle="modal" data-bs-target="#searchModal">
                                <i className="ti ti-search header-link-icon"></i>
                            </a>
                        </div>

                        <div className="header-element">
                            <a href="#" className="header-link dropdown-toggle" id="mainHeaderProfile" data-bs-toggle="dropdown" data-bs-auto-close="outside" aria-expanded="false">
                                <div className="d-flex align-items-center">
                                    <div className="me-sm-2 me-0">
                                        <img src="/assets/images/user.jpg" alt="img" width="32" height="32" className="rounded-circle" />
                                    </div>
                                </div>
                            </a>
                            <ul className="dropdown-menu dropdown-menu-end">
                                {/* <li><Link className="dropdown-item d-flex" to="/themes"><i className="ti ti-adjustments-horizontal fs-18 me-2 op-7"></i>Use Case Themes</Link></li> */}
                                <li className="dropdown-divider"></li>
                                <li>
                                    <a className="dropdown-item d-flex" href="#" onClick={toggleTheme}>
                                        {currentTheme === 'dark' ? (
                                            <i className="ti ti-sun fs-18 me-2 op-7"></i>
                                        ) : (
                                            <i className="ti ti-moon fs-18 me-2 op-7"></i>
                                        )}
                                        <span>{currentTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
                                    </a>
                                </li>
                                {/* <li><a className="dropdown-item d-flex" href="sign-up.html"><i className="ti ti-logout fs-18 me-2 op-7"></i>Log Out</a></li> */}
                            </ul>
                        </div>
                    </div>
                </div>
            </header>
    )
}

export default Header