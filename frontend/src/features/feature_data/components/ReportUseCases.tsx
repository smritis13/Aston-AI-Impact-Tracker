import React from 'react'
import RetailUseCaseListView from './RetailUseCaseListView'
import SDLCUseCaseListView from './SDLCUseCaseListView'
import AISDLCUseCaseListView from './AISDLCUseCaseListView'
type Props = {
    report: any
}

const ReportUseCases = ({report}: Props) => {
  return (
    <div>
        {report && report.type === "retail_ai" && (
            <RetailUseCaseListView report_id={report.id} />
        )}

        {report && report.type === "SDLC" && (
            <SDLCUseCaseListView report_id={report.id} />
        )}

        {report && report.type === "ai_sdlc" && (
            <AISDLCUseCaseListView report_id={report.id} />
        )}

        {/* {report && report.type === "" && (
        )} */}
    </div>
  )
}

export default ReportUseCases