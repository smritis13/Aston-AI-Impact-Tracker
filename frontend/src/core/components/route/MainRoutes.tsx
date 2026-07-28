import React from "react";
import { Routes, Route } from "react-router-dom";
import PrivateRoute from "./PrivateRoute";
import DashboardPage from "features/feature_home/pages/DashboardPage";
import DocumentsPage from "features/feature_document/pages/DocumentsPage";
import ContentPage from "features/feature_data/pages/ContentPage";
import ContentDetailsPage from "features/feature_data/pages/ContentDetailsPage";
import InsightsListPage from "features/feature_data/pages/InsightsListPage";
import ReportListPage from "features/feature_data/pages/ReportListPage";
import ReportDetailsPage from "features/feature_data/pages/ReportDetailsPage";
import ReportGenerationPage from "features/feature_data/pages/ReportGenerationPage";
import ImpactCaseStudyPage from "features/feature_data/pages/ImpactCaseStudyPage";
import ImpactCaseStudiesHistoryPage from "features/feature_data/pages/ImpactCaseStudiesHistoryPage";
import WorkflowListPage from "features/feature_workflow/pages/WorkflowListPage";
import WorkflowDetailsPage from "features/feature_workflow/pages/WorkflowDetailsPage";
import CategoryListPage from "features/feature_data/pages/CategoryListPage";
import CategoryDetailPage from "features/feature_data/pages/CategoryDetailPage";
import RetailSDLCUseCasesPage from "features/feature_data/pages/usecases/RetailSDLCUseCasesPage";
import RetailUseCasePage from "features/feature_data/pages/usecases/RetailUseCasePage";
import AISDLCUseCasesPage from "features/feature_data/pages/usecases/AISDLCUseCasesPage";
import UseCasesPage from "features/feature_data/pages/usecases/UseCasesPage";
import ThemePage from "features/feature_data/pages/themes/ThemePage";
import PromptPage from "features/feature_data/pages/PromptPage";
import TestImpactPage from "TestImpactPage";

const MainRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      {/* <Route path="/login" element={<LoginComponent />} /> */}

      {/* Private Routes */}
      <Route element={<PrivateRoute />}>
            {/* <Route path="/" element={<DashboardPage />} /> */}
            <Route path="/" element={<ReportGenerationPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/documents/*" element={<DocumentsPage />} />
            <Route path="/content/" element={<ContentPage />} />
            <Route path="/content/:contentId" element={<ContentDetailsPage />} />
            <Route path="/insights/" element={<InsightsListPage />} />
            <Route path="/reports/" element={<ReportListPage />} />
            <Route path="/reports/generate" element={<ReportGenerationPage />} />
            <Route path="/report/:reportId" element={<ReportDetailsPage />} />
            <Route path="/impact-case-study" element={<ImpactCaseStudyPage />} />
            <Route path="/impact-case-studies" element={<ImpactCaseStudiesHistoryPage />} />
            <Route path="/impact-case-studies/:reportId" element={<ReportDetailsPage />} />
            <Route path="/workflows/" element={<WorkflowListPage />} />
            <Route path="/workflow/:workflowId" element={<WorkflowDetailsPage />} />
            <Route path="/category/" element={<CategoryListPage />} />
            <Route path="/category/:id" element={<CategoryDetailPage />} />

            {/* Usecase Library Routes */}
            <Route path="/usecases/ai-sdlc" element={<AISDLCUseCasesPage />} />
            <Route path="/usecases/retail-sdlc" element={<RetailSDLCUseCasesPage />} />
            <Route path="/usecases/retail-ai" element={<RetailUseCasePage />} />
            <Route path="/usecases/:themeId" element={<UseCasesPage />} />
            <Route path="/usecases/:themeId/:themeSlug" element={<UseCasesPage />} />
            <Route path="/usecases" element={<UseCasesPage />} />
            <Route path="/themes" element={<ThemePage />} />
            <Route path="/prompts" element={<PromptPage />} />
      </Route>

      {/* Catch-all Route */}
      {/* <Route path="*" element={<NotFoundComponent />} /> */}
    </Routes>
  );
};

export default MainRoutes;
