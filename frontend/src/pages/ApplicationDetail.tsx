import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import { Application, AuditLog } from "../types";
import styles from "./ApplicationDetail.module.css";

import { User } from "../types";

export function ApplicationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [application, setApplication] = useState<Application | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [auditLog, setAuditLog] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState("");
  const [comment, setComment] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editTeamSize, setEditTeamSize] = useState<number | "">("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [appRes, auditRes] = await Promise.all([
          apiClient.get<Application>(`/applications/${id}/`),
          apiClient.get<AuditLog[]>(`/applications/${id}/audit/`),
        ]);
        setApplication(appRes.data);
        setAuditLog(auditRes.data || []);
        try {
          const me = await apiClient.get<User>("/accounts/me/");
          setUser(me.data);
        } catch (e) {
          // ignore
        }
      } catch (err: any) {
        const message =
          err.response?.data?.error?.message || "Failed to load application";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      fetchData();
    }
  }, [id]);

  const handleTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    setTransitionError(null);

    if (!selectedTarget) {
      setTransitionError("Please select a target status");
      return;
    }

    try {
      setIsTransitioning(true);
      const response = await apiClient.post<Application>(
        `/applications/${id}/transitions/`,
        {
          target: selectedTarget,
          comment: comment || undefined,
        },
      );

      setApplication(response.data);
      setSelectedTarget("");
      setComment("");

      // Refresh audit log
      const auditRes = await apiClient.get<AuditLog[]>(
        `/applications/${id}/audit/`,
      );
      setAuditLog(auditRes.data || []);
    } catch (err: any) {
      const message = err.response?.data?.error?.message || "Transition failed";
      setTransitionError(message);
    } finally {
      setIsTransitioning(false);
    }
  };

  if (isLoading) {
    return <div className={styles.loading}>Loading application...</div>;
  }

  if (error || !application) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>{error || "Application not found"}</div>
        <button onClick={() => navigate("/applications")}>
          Back to Applications
        </button>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    DRAFT: "#999",
    SUBMITTED: "#2196F3",
    UNDER_REVIEW: "#FF9800",
    APPROVED: "#4CAF50",
    REJECTED: "#F44336",
  };

  const allowedTransitions: Record<string, string[]> = {
    DRAFT: ["SUBMITTED"],
    SUBMITTED: ["UNDER_REVIEW"],
    UNDER_REVIEW: ["APPROVED", "REJECTED", "DRAFT"],
    APPROVED: [],
    REJECTED: [],
  };

  const isOwner = user && application.owner_id === user.id;
  const isReviewer = !!(user && user.is_staff);

  const canPerformTransition = (() => {
    if (!user) return false;
    if (application.status === "DRAFT") return isOwner;
    if (application.status === "SUBMITTED") return isReviewer;
    if (application.status === "UNDER_REVIEW") return isReviewer;
    return false;
  })();

  return (
    <div className={styles.container}>
      <button
        className={styles.backButton}
        onClick={() => navigate("/applications")}
      >
        ← Back to Applications
      </button>

      <div className={styles.header}>
        <div>
          <h1>{application.title}</h1>
          <span
            className={styles.status}
            style={{
              backgroundColor: statusColors[application.status] || "#999",
            }}
          >
            {application.status}
          </span>
        </div>
        {user &&
          user.id === application.owner_id &&
          application.status === "DRAFT" && (
            <div>
              <button
                className={styles.editButton}
                onClick={() => {
                  setIsEditing(true);
                  setEditTitle(application.title);
                  setEditDescription(application.content?.description || "");
                  setEditTeamSize(application.content?.team_size ?? "");
                }}
              >
                Edit
              </button>
            </div>
          )}
      </div>

      <div className={styles.details}>
        <div className={styles.section}>
          <h2>Details</h2>
          {!isEditing ? (
            <>
              <div className={styles.field}>
                <label>Title</label>
                <p>{application.title}</p>
              </div>
              <div className={styles.field}>
                <label>Description</label>
                <p>{application.content?.description || "N/A"}</p>
              </div>
              <div className={styles.field}>
                <label>Team Size</label>
                <p>{application.content?.team_size || "N/A"}</p>
              </div>
              <div className={styles.field}>
                <label>Created</label>
                <p>{new Date(application.created_at).toLocaleString()}</p>
              </div>
            </>
          ) : (
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                try {
                  const payload: any = {
                    title: editTitle,
                    content: { description: editDescription },
                  };
                  if (editTeamSize !== "")
                    payload.content.team_size = editTeamSize;
                  const res = await apiClient.patch<Application>(
                    `/applications/${id}/`,
                    payload,
                  );
                  setApplication(res.data);
                  setIsEditing(false);
                } catch (err: any) {
                  setError(
                    err.response?.data?.error?.message || "Failed to save",
                  );
                }
              }}
            >
              <div className={styles.field}>
                <label>Title</label>
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  required
                />
              </div>
              <div className={styles.field}>
                <label>Description</label>
                <textarea
                  rows={4}
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                />
              </div>
              <div className={styles.field}>
                <label>Team Size</label>
                <input
                  type="number"
                  min={0}
                  value={editTeamSize === "" ? "" : editTeamSize}
                  onChange={(e) =>
                    setEditTeamSize(
                      e.target.value === "" ? "" : Number(e.target.value),
                    )
                  }
                />
              </div>
              <div className={styles.actions}>
                <button type="submit" className={styles.submitButton}>
                  Save
                </button>
                <button
                  type="button"
                  className={styles.cancelButton}
                  onClick={() => setIsEditing(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>

        {canPerformTransition &&
          allowedTransitions[application.status]?.length > 0 && (
            <div className={styles.section}>
              <h2>Transition Status</h2>
              {transitionError && (
                <div className={styles.error}>{transitionError}</div>
              )}
              <form onSubmit={handleTransition}>
                <div className={styles.formGroup}>
                  <label htmlFor="target-status">Move to status:</label>
                  <select
                    id="target-status"
                    value={selectedTarget}
                    onChange={(e) => setSelectedTarget(e.target.value)}
                    disabled={isTransitioning}
                  >
                    <option value="">-- Select status --</option>
                    {allowedTransitions[application.status].map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </div>

                {["REJECTED", "DRAFT"].includes(selectedTarget) && (
                  <div className={styles.formGroup}>
                    <label htmlFor="comment">Comment (required)</label>
                    <textarea
                      id="comment"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Enter your comment"
                      disabled={isTransitioning}
                      rows={4}
                    />
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isTransitioning || !selectedTarget}
                  className={styles.submitButton}
                >
                  {isTransitioning ? "Transitioning..." : "Confirm Transition"}
                </button>
              </form>
            </div>
          )}
      </div>

      {auditLog.length > 0 && (
        <div className={styles.section}>
          <h2>Audit Log</h2>
          <div className={styles.auditLog}>
            {auditLog.map((log, idx) => (
              <div key={log.id} className={styles.auditEntry}>
                <div className={styles.auditMain}>
                  <div className={styles.auditTransition}>
                    <span
                      className={styles.badge}
                      style={{
                        backgroundColor:
                          statusColors[log.from_status] || "#999",
                      }}
                    >
                      {log.from_status}
                    </span>
                    <span className={styles.arrow}>→</span>
                    <span
                      className={styles.badge}
                      style={{
                        backgroundColor: statusColors[log.to_status] || "#999",
                      }}
                    >
                      {log.to_status}
                    </span>
                  </div>
                  <div className={styles.auditMeta}>
                    <span>
                      {log.actor_id ? `User ${log.actor_id}` : "System"}
                    </span>
                    <span>{new Date(log.created_at).toLocaleString()}</span>
                  </div>
                </div>
                {log.comment && (
                  <p className={styles.auditComment}>{log.comment}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
