import { StrictMode } from "react";
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";

import "./index.css";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Landing from "./pages/Landing";
import Login   from "./pages/Login";
import Signup  from "./pages/Signup";
import App     from "./App";

// ── Protected route wrapper ───────────────────────────────
function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-soul-500 border-t-transparent
                        rounded-full animate-spin" />
      </div>
    );
  }
  // Pass user_id as key → React fully re-mounts App on every user switch.
  // This guarantees messages, prefill, sidebar state etc. are always fresh.
  return user
    ? <React.Fragment key={user.user_id}>{children}</React.Fragment>
    : <Navigate to="/login" replace />;
}

// ── Public route (redirect to /app if already logged in) ──
function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? <Navigate to="/app" replace /> : children;
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#1f2937",
              color: "#f3f4f6",
              border: "1px solid #374151",
              borderRadius: "12px",
              fontSize: "13px",
            },
          }}
        />
        <Routes>
          {/* Public */}
          <Route path="/"       element={<Landing />} />
          <Route path="/login"  element={<PublicRoute><Login  /></PublicRoute>} />
          <Route path="/signup" element={<PublicRoute><Signup /></PublicRoute>} />

          {/* Protected */}
          <Route path="/app"    element={<PrivateRoute><App /></PrivateRoute>} />

          {/* Fallback */}
          <Route path="*"       element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
