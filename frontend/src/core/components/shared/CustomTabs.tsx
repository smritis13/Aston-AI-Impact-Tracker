import React from 'react'

function CustomTabs() {
  return (
    <div>
        <ul className="nav nav-tabs mb-3 border-0" role="tablist">
            <li className="nav-item">
                <a className="nav-link active" data-bs-toggle="tab" role="tab" href="#home1"
                    aria-selected="true">Title</a>
            </li>
            
        </ul>
        <div className="tab-content">
            <div className="tab-pane show active text-muted" id="home1" role="tabpanel">
                
            </div>
        </div>
    </div>
  )
}

export default CustomTabs