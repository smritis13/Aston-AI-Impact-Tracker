
type Props = {}

function BlogDetailsAside({}: Props) {
  return (
    <div className="col-xl-3">
        <div className="row">
            <div className="col-xl-12">
                <div className="card custom-card">
                    <div className="card-header">
                        <div className="card-title">
                            Recent Posts
                        </div>
                    </div>
                    <div className="card-body">
                        <ul className="list-group">
                            <li className="list-group-item">
                                <div className="d-flex flex-wrap align-items-center">
                                    <span className="avatar avatar-xl me-3">
                                        <img src="../assets/images/media/media-1.jpg" className="img-fluid" alt="..." />
                                    </span>
                                    <div className="flex-fill">
                                        <a href="/animals" className="fs-14 fw-semibold mb-0">Animals</a>
                                        <p className="mb-1 popular-blog-content">
                                            There are passages of available
                                        </p>
                                        <span className="text-muted fs-11">24,Nov 2022 - 18:27</span>
                                    </div>
                                </div>
                            </li>
                            <li className="list-group-item text-center d-grid">
                                <button className="btn btn-primary-light">Load more</button>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            
        </div>
    </div>
  )
}

export default BlogDetailsAside