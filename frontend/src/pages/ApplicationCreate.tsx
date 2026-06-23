import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import styles from "./ApplicationCreate.module.css";

export function ApplicationCreate() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [teamSize, setTeamSize] = useState<number | "">("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError("Title is required");
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        title: title.trim(),
        content: {
          description: description.trim(),
          team_size: teamSize === "" ? undefined : teamSize,
        },
      };

      const res = await apiClient.post("/applications/", payload);
      const id = res.data.id;
      navigate(`/applications/${id}`);
    } catch (err: any) {
      const msg =
        err.response?.data?.error?.message || "Failed to create application";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1>Create Application</h1>
        {error && <div className={styles.error}>{error}</div>}
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="title">Title</label>
            <input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="teamSize">Team size</label>
            <input
              id="teamSize"
              type="number"
              min={0}
              value={teamSize === "" ? "" : teamSize}
              onChange={(e) =>
                setTeamSize(e.target.value === "" ? "" : Number(e.target.value))
              }
            />
          </div>

          <div className={styles.actions}>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Creating..." : "Create"}
            </button>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={() => navigate("/applications")}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
