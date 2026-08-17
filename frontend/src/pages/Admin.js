import { useState, useEffect, useRef } from "react";
import * as api from "../api/client";

/**
 * The admin key used to be a constant in this file, shipped inside the JS
 * bundle for anyone to read, and the password was checked client-side
 * (`if (password === "admin123")`) so the check could be skipped entirely.
 * The password now goes to POST /api/v1/admin/sessions and the backend
 * returns the key, which the api client keeps in sessionStorage.
 */
export default function Admin() {
  const [authorized, setAuthorized] = useState(api.isAdminAuthenticated());
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState(null);
  const [status, setStatus] = useState("");
  const [trends, setTrends] = useState(null);
  const [trendsNotice, setTrendsNotice] = useState(null);
  const [flaggedTerms, setFlaggedTerms] = useState([]);
  const [surveyOverview, setSurveyOverview] = useState(null);
  const [training, setTraining] = useState(null);

  const pollRef = useRef(null);

  async function login() {
    setLoginError(null);
    try {
      await api.admin.login(password);
      setAuthorized(true);
      setPassword("");
    } catch (err) {
      setLoginError(err.message);
    }
  }

  useEffect(() => {
    if (authorized) {
      loadTrends();
      loadFlaggedTerms();
      loadSurveyOverview();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authorized]);

  // Stop polling if the admin navigates away mid-training.
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  async function uploadCSV(e) {
    const file = e.target.files[0];
    if (!file) return;

    setStatus("Uploading...");

    try {
      const data = await api.admin.uploadDataset(file);
      setStatus(JSON.stringify(data, null, 2));
    } catch (err) {
      setStatus(
        `Upload failed: ${err.message}` +
          (err.details ? `\n${JSON.stringify(err.details, null, 2)}` : "")
      );
    } finally {
      // Allow re-uploading the same file.
      e.target.value = "";
    }
  }

  /**
   * Training runs as a background job on the server. This kicks it off and
   * polls until it settles, instead of holding one request open for minutes.
   */
  async function retrain() {
    setStatus("Requesting training...");

    try {
      const job = await api.admin.startTraining();
      setTraining(job);
      setStatus(`Training job #${job.id} is ${job.status}.`);

      if (pollRef.current) clearInterval(pollRef.current);

      pollRef.current = setInterval(async () => {
        try {
          const latest = await api.admin.getTrainingJob(job.id);
          setTraining(latest);

          const finished = ["succeeded", "failed", "interrupted"].includes(
            latest.status
          );

          if (finished) {
            clearInterval(pollRef.current);
            pollRef.current = null;
            setStatus(
              `Training job #${latest.id} ${latest.status}.` +
                (latest.detail ? `\n${latest.detail}` : "")
            );
            loadTrends();
          } else {
            setStatus(`Training job #${latest.id} is ${latest.status}...`);
          }
        } catch (err) {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setStatus(`Lost track of the training job: ${err.message}`);
        }
      }, 3000);
    } catch (err) {
      setStatus(`Could not start training: ${err.message}`);
    }
  }

  async function loadTrends() {
    try {
      const data = await api.admin.trends();

      if (data.sufficient_data) {
        setTrends(data.trends);
        setTrendsNotice(null);
      } else {
        // Used to be an HTTP 400 that the page silently swallowed.
        setTrends(null);
        setTrendsNotice(
          `Not enough predictions yet for trend analysis ` +
            `(${data.window_size}/${data.minimum_required}).`
        );
      }
    } catch (err) {
      setTrendsNotice(`Could not load trends: ${err.message}`);
    }
  }

  async function loadFlaggedTerms() {
    try {
      // min_frequency 1 so admins also see words flagged only once.
      const data = await api.flaggedTerms.list({ minFrequency: 1 });
      setFlaggedTerms(data.data || []);
    } catch (err) {
      console.error("Failed to load flagged terms:", err.message);
    }
  }

  async function loadSurveyOverview() {
    try {
      const data = await api.survey.stats();
      setSurveyOverview(data.participation);
    } catch (err) {
      console.error("Failed to load survey stats:", err.message);
    }
  }

  if (!authorized) {
    return (
      <div className="admin-login-wrapper">
        <div className="admin-login">
          <h1>Admin Login</h1>

          <input
            type="password"
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && login()}
          />

          <button onClick={login}>Login</button>

          {loginError && (
            <p className="admin-login-error" role="alert">
              {loginError}
            </p>
          )}
        </div>
      </div>
    );
  }

  const trainingInFlight =
    training && ["queued", "running"].includes(training.status);

  return (
    <div className="admin-panel">

      <div className="admin-hero">
        <p className="admin-badge">ADMIN ACCESS</p>

        <h1 className="admin-title">Control Center</h1>

        <p className="admin-subtitle">
          Manage datasets, retrain models, and monitor system intelligence
        </p>
      </div>

      <div className="admin-actions">
        {/* Upload Dataset */}
        <div className="admin-card">

          <h3 className="admin-card-title">Upload Dataset</h3>
          <p className="admin-card-desc">
            Add new labeled data to improve model accuracy and language coverage.
          </p>

          <label className="admin-card-btn">
            Upload CSV
            <input type="file" accept=".csv" hidden onChange={uploadCSV} />
          </label>
        </div>

        {/* Retrain Model */}
        <div className="admin-card admin-card-danger">

          <h3 className="admin-card-title">Retrain Model</h3>
          <p className="admin-card-desc">
            Rebuild all models using the latest datasets. Runs in the background
            — you can leave this page.
          </p>

          <button
            className="admin-card-btn danger"
            onClick={retrain}
            disabled={trainingInFlight}
          >
            {trainingInFlight ? "Training in progress..." : "Start Training"}
          </button>
        </div>
      </div>

      <pre className="admin-status">{status}</pre>

      {/* Trend analysis */}
      {trendsNotice && <p className="admin-empty">{trendsNotice}</p>}

      {trends && (
        <div className="admin-trends">

          <h2 className="admin-section-title">
            Language Drift & Trend Analysis
          </h2>

          <div className="trend-grid">
            {Object.entries(trends).map(([label, data]) => {
              const up = data.change_percent > 0;
              const down = data.change_percent < 0;

              return (
                <div
                  key={label}
                  className={`trend-card-ui ${label.toLowerCase()}`}
                >
                  <div className="trend-card-header">
                    <span className="trend-dot" />
                    <p className="trend-title">{label}</p>

                    {/* Direction is carried by the sign and the up/down
                        colour class rather than a glyph. */}
                    <p className={`trend-percent ${up ? "up" : down ? "down" : ""}`}>
                      {up ? "+" : down ? "-" : ""}
                      {Math.abs(data.change_percent)}%
                    </p>
                  </div>

                  <div className="trend-card-body">
                    <p className="trend-main-value">
                      {data.current_count}
                    </p>


                    <p className="trend-main-sub">
                      texts scanned
                    </p>


                    <p className="trend-subtitle">
                      {label === "Normal" && "Clean & acceptable language usage"}
                      {label === "Offensive" && "Abusive or harmful expressions detected"}
                      {label === "Hate" && "Targeted hate speech & severe toxicity"}
                    </p>

                    {label === "Hate" && up && (
                      <p className="trend-alert">Spike detected</p>
                    )}
                  </div>
                </div>

              );
            })}
          </div>
        </div>
      )}

      {surveyOverview && (
        <div className="admin-survey-overview-card">
          <h2 className="admin-section-title">
            Survey Participation Overview
          </h2>

          <div className="survey-overview-grid">
            <div>
              <span>Total Texts</span>
              <b>{surveyOverview.total_texts}</b>
            </div>

            <div>
              <span>Total Votes</span>
              <b>{surveyOverview.total_votes}</b>
            </div>

            <div>
              <span>Resolved</span>
              <b>{surveyOverview.resolved}</b>
            </div>

            <div>
              <span>Unresolved</span>
              <b>{surveyOverview.unresolved}</b>
            </div>

            <div>
              <span>Avg Votes / Text</span>
              <b>{Number(surveyOverview.avg_votes).toFixed(2)}</b>
            </div>
          </div>
        </div>
      )}



      {flaggedTerms.length > 0 ? (
        <div className="admin-flagged-terms">
          <h2 className="admin-section-title">
            Flagged Words Intelligence
          </h2>

          <div className="flagged-table-wrapper">
            <table className="flagged-table">
              <thead>
                <tr>
                  <th>Word</th>
                  <th>Context</th>
                  <th>Times Flagged</th>
                  <th>First Seen</th>
                </tr>
              </thead>
              <tbody>
                {flaggedTerms.map((item) => (
                  <tr key={item.id}>
                    <td>{item.word}</td>
                    <td>{item.context}</td>
                    <td>{item.frequency}</td>
                    <td>
                      {item.created_at
                        ? new Date(item.created_at).toLocaleDateString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <p className="admin-empty">No flagged terms yet.</p>
      )}
    </div>
  );

}
