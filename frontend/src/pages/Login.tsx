import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import styles from "./Login.module.css";

export function Login() {
  const { login, isLoading, error } = useAuth();
  const [username, setUsername] = useState("alice");
  const [password, setPassword] = useState("password123");
  const [formError, setFormError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");

    if (!username.trim()) {
      setFormError("Username is required");
      return;
    }

    if (!password.trim()) {
      setFormError("Password is required");
      return;
    }

    try {
      await login(username, password);
    } catch (err) {
      setFormError(error || "Login failed. Please check your credentials.");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1>Submission & Approval Workflow</h1>
        <p className={styles.subtitle}>Login to your account</p>

        <form onSubmit={handleSubmit} className={styles.form}>
          {(formError || error) && (
            <div className={styles.error}>{formError || error}</div>
          )}

          <div className={styles.formGroup}>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
              required
            />
            <small className={styles.hint}>Demo: alice or bob</small>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              required
            />
            <small className={styles.hint}>Demo: password123</small>
          </div>

          <button type="submit" disabled={isLoading} className={styles.button}>
            {isLoading ? "Logging in..." : "Login"}
          </button>
        </form>

        <div className={styles.info}>
          <p>
            <strong>Test Users:</strong>
          </p>
          <ul>
            <li>
              <strong>alice</strong> (Applicant) - Can create and submit
              applications
            </li>
            <li>
              <strong>bob</strong> (Reviewer) - Can approve/reject applications
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
