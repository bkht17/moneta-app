import { Navigate, Route, Routes } from "react-router";

import DashboardLayout from "./components/layouts/DashboardLayout";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Settings from "./pages/Settings";
import Login from "./pages/auth/Login";
import SignUp from "./pages/auth/SignUp";
import NewReview from "./pages/review/NewReview";
import ReviewOverviewPage from "./pages/review/ReviewOverviewPage";
import ReviewWizard from "./pages/review/ReviewWizard";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<SignUp />} />
      <Route element={<DashboardLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="reviews" element={<History />} />
        <Route path="reviews/new" element={<NewReview />} />
        <Route path="reviews/:id" element={<ReviewWizard />} />
        <Route path="reviews/:id/overview" element={<ReviewOverviewPage />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
