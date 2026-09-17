import { Navigate, Route, Routes } from "react-router-dom";
import { DriverTracker } from "./pages/DriverTracker";
import { EmergencyRequest } from "./pages/EmergencyRequest";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<EmergencyRequest />} />
      <Route path="/driver/:dispatchId" element={<DriverTracker />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
