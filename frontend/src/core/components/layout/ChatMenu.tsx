import MenuConversations from 'features/feature_chat/components/MenuConversations'
import React from 'react'
import { Link } from 'react-router-dom'

function ChatMenu() {
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
                        <li className="slide">
                            <Link to="/chat" className="side-menu__item">
                                <i className="ti ti-brand-tabler side-menu__icon"></i>
                                <span className="side-menu__label">New Chat</span>
                            </Link>
                        </li>

                        <li className=' mb-5'></li>



                        <li className="slide__category"><span className="category-name">Today</span></li>

                        <MenuConversations />
                        

                    </ul>
                    <div className="slide-right" id="slide-right"><svg xmlns="http://www.w3.org/2000/svg" fill="#7b8191" width="24" height="24" viewBox="0 0 24 24"> <path d="M10.707 17.707 16.414 12l-5.707-5.707-1.414 1.414L13.586 12l-4.293 4.293z"></path> </svg></div>
                </nav>

            </div>

        </aside>
  )
}

export default ChatMenu