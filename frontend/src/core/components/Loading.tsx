import React from 'react'

type Props = {
    isLoading: boolean
}

export default function Loading({isLoading = false}: Props) {

  if(!isLoading)
    return (<></>)  
  return (
    <>
        <div className="d-flex justify-content-center mb-4">
            <div className="spinner-grow spinner-grow-sm me-4" role="status">
                <span className="visually-hidden">Loading...</span>
            </div>
        </div>
        
    </>
  )
}