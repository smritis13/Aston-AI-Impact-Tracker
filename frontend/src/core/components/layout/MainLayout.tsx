import React from 'react'
import Header from './Header'
import MainMenu from './MainMenu'
import Footer from './Footer'

function MainLayout({children}:any) {
  return (
    <>
        <div className="page">
            <Header />
            <MainMenu  />
            <div className="main-content app-content">
                <div className="container-fluid">
                    {children}
                </div>
            </div>
            {/* <Footer /> */}
        </div>
    </>
  )
}

export default MainLayout