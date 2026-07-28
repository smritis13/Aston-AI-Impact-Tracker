import React from 'react'
import Header from './Header'
import ChatMenu from './ChatMenu'
import MainMenu from './MainMenu'

function ChatLayout({children}:any) {
  return (
    <>
        <div className="page">
            <Header />
            {/* <ChatMenu  /> */}
            <MainMenu />
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

export default ChatLayout