import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Assistant from "./components/Assistant";
import Dashboard from "./components/Dashboard";
import SocialLogin from "./components/SocialLogin";
import Success from "./components/Success";

function App() {
  return (
    <Router>
      <Routes>
        {/* ✅ Default page → Login (instead of Dashboard) */}
        <Route path="/" element={<SocialLogin />} />

        {/* ✅ Login page */}
        <Route path="/login" element={<SocialLogin />} />

        {/* ✅ Assistant page */}
        <Route path="/assistant" element={<Assistant />} />

        {/* ✅ Dashboard (protected) */}
        <Route
          path="/dashboard"
          element={
            localStorage.getItem("user_id") ? (
              <Dashboard />
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        {/* ✅ Success page */}
        <Route path="/success" element={<Success />} />

        {/* ✅ Fallback route (prevents blank page errors) */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;