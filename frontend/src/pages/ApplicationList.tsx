import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import { Application } from "../types";
import styles from "./ApplicationList.module.css";

export function ApplicationList() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<Application[]>("/applications/");
        setApplications(response.data || []);
      } catch (err: any) {
        const message =
          err.response?.data?.error?.message || "Failed to load applications";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchApplications();
  }, []);

  const filteredApplications = statusFilter
    ? applications.filter((app) => app.status === statusFilter)
    : applications;

  const applicationCount = applications.length;
  const visibleCount = filteredApplications.length;

  const statusColors: Record<string, string> = {
    DRAFT: "#999",
    SUBMITTED: "#2196F3",
    UNDER_REVIEW: "#FF9800",
    APPROVED: "#4CAF50",
    REJECTED: "#F44336",
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1>Applications</h1>
          <p className={styles.subtitle}>
            Create, submit, and manage your applications from one place.
          </p>
        </div>
      </div>

      <div className={styles.summaryBar}>
        <div>
          <h2 className={styles.summaryTitle}>My applications</h2>
          <p className={styles.summaryText}>
            {applicationCount} total · {visibleCount} showing
          </p>
        </div>
        <button
          className={styles.createButton}
          onClick={() => navigate("/applications/new")}
        >
          + New Application
        </button>
      </div>

      <div className={styles.toolbar}>
        <div className={styles.filters}>
          <label htmlFor="status-filter">Filter by status</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="UNDER_REVIEW">Under review</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {isLoading ? (
        <div className={styles.loading}>Loading applications...</div>
      ) : filteredApplications.length === 0 ? (
        <div className={styles.empty}>
          <p>No applications found</p>
          <button
            className={styles.createButton}
            onClick={() => navigate("/applications/new")}
          >
            Create your first application
          </button>
        </div>
      ) : (
        <>
          <div className={styles.list}>
            {filteredApplications.map((app) => (
              <div
                key={app.id}
                className={styles.card}
                onClick={() => navigate(`/applications/${app.id}`)}
              >
                <div className={styles.cardHeader}>
                  <h3>{app.title}</h3>
                  <span
                    className={styles.status}
                    style={{
                      backgroundColor: statusColors[app.status] || "#999",
                    }}
                  >
                    {app.status}
                  </span>
                </div>

                <p className={styles.description}>
                  {app.content?.description || "No description"}
                </p>

                <div className={styles.meta}>
                  <span>
                    Created: {new Date(app.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className={styles.cardFooter}>
                  <button
                    className={styles.viewButton}
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/applications/${app.id}`);
                    }}
                  >
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
