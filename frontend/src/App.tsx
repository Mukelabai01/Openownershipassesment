import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { Login } from "./pages/Login";
import { ApplicationList } from "./pages/ApplicationList";
import { ApplicationDetail } from "./pages/ApplicationDetail";
import { ApplicationCreate } from "./pages/ApplicationCreate";
import styles from "./App.module.css";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = localStorage.getItem("access_token");

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function App() {
  const isAuthenticated = localStorage.getItem("access_token");

  return (
    <Router>
      <div className={styles.app}>
        {isAuthenticated && (
          <nav className={styles.navbar}>
            <div className={styles.navContent}>
              <h2 className={styles.brand}>Submission & Approval Workflow</h2>
              <div className={styles.navLinks}>
                <a href="/applications">Applications</a>
                <button
                  className={styles.logoutButton}
                  onClick={() => {
                    localStorage.removeItem("access_token");
                    window.location.href = "/login";
                  }}
                >
                  Logout
                </button>
              </div>
            </div>
          </nav>
        )}

        <div className={styles.main}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/applications"
              element={
                <ProtectedRoute>
                  <ApplicationList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/applications/new"
              element={
                <ProtectedRoute>
                  <ApplicationCreate />
                </ProtectedRoute>
              }
            />
            <Route
              path="/applications/:id"
              element={
                <ProtectedRoute>
                  <ApplicationDetail />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/applications" replace />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
