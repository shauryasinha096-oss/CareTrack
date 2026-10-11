import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./services/auth";
import { Spinner, Empty } from "./components/ui";
import Workspace from "./layouts/Workspace";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Records from "./pages/Records";
import CaseTaking from "./pages/CaseTaking";
import PatientProfile from "./pages/PatientProfile";
import {
  NewPatient,
  CaseDetails,
  VisitDetails,
  PrescriptionDetails,
  NewPrescription,
} from "./pages/ClinicalDetails";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
function Clinical() {
  const { user } = useAuth();
  return user?.role === "RECEPTIONIST" ? (
    <Navigate to="/" replace />
  ) : (
    <Outlet />
  );
}
function Admin() {
  const { user } = useAuth();
  return user?.role === "ADMIN" ? <Outlet /> : <Navigate to="/" replace />;
}
export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Login />;
  return (
    <Routes>
      <Route element={<Workspace />}>
        <Route index element={<Dashboard />} />
        <Route
          path="patients"
          element={<Records key="patients" resource="patients" />}
        />
        <Route path="patients/new" element={<NewPatient />} />
        <Route path="patients/:id" element={<PatientProfile />} />
        <Route
          path="appointments"
          element={<Records key="appointments" resource="appointments" />}
        />
        <Route
          path="followups"
          element={<Records key="followups" resource="followups" />}
        />
        <Route
          path="doctors"
          element={<Records key="doctors" resource="doctors" />}
        />
        <Route path="reports" element={<Reports />} />
        <Route path="settings" element={<Settings />} />
        <Route element={<Clinical />}>
          <Route
            path="cases"
            element={<Records key="cases" resource="cases" />}
          />
          <Route path="cases/new" element={<CaseTaking />} />
          <Route path="cases/:id" element={<CaseDetails />} />
          <Route
            path="visits"
            element={<Records key="visits" resource="visits" />}
          />
          <Route path="visits/:id" element={<VisitDetails />} />
          <Route
            path="prescriptions"
            element={<Records key="prescriptions" resource="prescriptions" />}
          />
          <Route path="prescriptions/new" element={<NewPrescription />} />
          <Route path="prescriptions/:id" element={<PrescriptionDetails />} />
          <Route
            path="diagnoses"
            element={<Records key="diagnoses" resource="diagnoses" />}
          />
          <Route
            path="medicines"
            element={<Records key="medicines" resource="medicines" />}
          />
          <Route
            path="symptoms"
            element={<Records key="symptoms" resource="symptoms" />}
          />
        </Route>
        <Route element={<Admin />}>
          <Route
            path="audit-logs"
            element={<Records key="audit" resource="audit-logs" />}
          />
          <Route
            path="users"
            element={<Records key="users" resource="users" />}
          />
        </Route>
        <Route
          path="*"
          element={
            <Empty
              title="Page not found"
              description="Choose a page from the workspace navigation."
            />
          }
        />
      </Route>
    </Routes>
  );
}
