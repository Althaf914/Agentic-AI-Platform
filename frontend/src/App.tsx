import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import PageWrapper from "@/components/layout/PageWrapper";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import ICPBuilder from "@/pages/ICPBuilder";
import DiscoveryWizard from "@/pages/DiscoveryWizard";
import PersonaBuilder from "@/pages/PersonaBuilder";
import WorkflowLauncher from "@/pages/WorkflowLauncher";
import WorkflowViewer from "@/pages/WorkflowViewer";
import WorkflowHistory from "@/pages/WorkflowHistory";
import Prospects from "@/pages/Prospects";
import ProspectDetail from "@/pages/ProspectDetail";
import Approvals from "@/pages/Approvals";
import Memory from "@/pages/Memory";
import Settings from "@/pages/Settings";

function ProtectedRoute({
  children,
  allowedRoles,
}: {
  children: React.ReactNode;
  allowedRoles?: string[];
}) {
  const { token, user } = useAuthStore();

  if (!token) return <Navigate to="/login" replace />;
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <PageWrapper>{children}</PageWrapper>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/icp" element={<ProtectedRoute allowedRoles={["admin", "sales"]}><ICPBuilder /></ProtectedRoute>} />
      <Route path="/wizard" element={<ProtectedRoute allowedRoles={["admin", "sales"]}><DiscoveryWizard /></ProtectedRoute>} />
      <Route path="/personas" element={<ProtectedRoute allowedRoles={["admin", "sales"]}><PersonaBuilder /></ProtectedRoute>} />
      <Route path="/workflow" element={<ProtectedRoute><WorkflowLauncher /></ProtectedRoute>} />
      <Route path="/workflow/:id" element={<ProtectedRoute><WorkflowViewer /></ProtectedRoute>} />
      <Route path="/workflows" element={<ProtectedRoute><WorkflowHistory /></ProtectedRoute>} />
      <Route path="/prospects" element={<ProtectedRoute><Prospects /></ProtectedRoute>} />
      <Route path="/prospects/:id" element={<ProtectedRoute><ProspectDetail /></ProtectedRoute>} />
      <Route path="/approvals" element={<ProtectedRoute allowedRoles={["admin", "sales"]}><Approvals /></ProtectedRoute>} />
      <Route path="/memory" element={<ProtectedRoute><Memory /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute allowedRoles={["admin"]}><Settings /></ProtectedRoute>} />
    </Routes>
  );
}
