import { useState, useEffect } from "react";

const ADMIN_KEY = "KRIXION_ADMIN_2026";

export default function Admin() {
  const [authorized, setAuthorized] = useState(
    sessionStorage.getItem("admin_auth") === "true"
  );
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("");
  const [trends, setTrends] = useState(null);
  const [flaggedTerms, setFlaggedTerms] = useState([]);
  const [surveyOverview, setSurveyOverview] = useState(null);

  function login() {
    if (password === "admin123") {
      sessionStorage.setItem("admin_auth", "true");

      // ✅ ADD THIS LINE (CRITICAL FIX)
      window.dispatchEvent(new Event("admin-auth-change"));

      setAuthorized(true);
      setPassword("");
    } else {
      alert("Wrong password");
    }
  }


  useEffect(() => {
    if (authorized) {
      loadTrends();
      loadFlaggedTerms();
      loadSurveyOverview(); 
    }
  }, [authorized]);

  async function uploadCSV(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setStatus("Uploading...");

    const res = await fetch("http://127.0.0.1:5000/admin/upload", {
      method: "POST",
      headers: {
        "X-ADMIN-KEY": ADMIN_KEY,
      },
      body: formData,
    });

    const data = await res.json();
    setStatus(JSON.stringify(data, null, 2));
  }

  async function retrain() {
    setStatus("Training started...");

    const res = await fetch("http://127.0.0.1:5000/admin/retrain", {
      method: "POST",
      headers: {
        "X-ADMIN-KEY": ADMIN_KEY,
      },
    });

    const data = await res.json();
    setStatus(JSON.stringify(data, null, 2));
  }

  async function loadTrends() {
    const res = await fetch("http://127.0.0.1:5000/admin/trends", {
      headers: {
        "X-ADMIN-KEY": ADMIN_KEY,
      },
    });

    const data = await res.json();
    if (data.trends) {
      setTrends(data.trends);
    }
  }

  async function loadFlaggedTerms() {
    const res = await fetch("http://127.0.0.1:5000/admin/flagged-terms", {
      headers: {
        "X-ADMIN-KEY": ADMIN_KEY,
      },
    });

    const data = await res.json();
    if (data.data) {
      setFlaggedTerms(data.data);
    }
  }

  async function loadSurveyOverview() {
    const res = await fetch("http://127.0.0.1:5000/admin/survey-overview", {
      headers: {
        "X-ADMIN-KEY": ADMIN_KEY,
      },
    });

    const data = await res.json();
    setSurveyOverview(data);
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
          />

          <button onClick={login}>Login</button>
        </div>
      </div>
    );
  }



  return (
    <div className="admin-panel">

      <div className="admin-hero">
        <p className="admin-badge">KRIXION • ADMIN ACCESS</p>

        <h1 className="admin-title">Control Center</h1>

        <p className="admin-subtitle">
          Manage datasets, retrain models, and monitor system intelligence
        </p>
      </div>

      <div className="admin-actions">
        {/* Upload Dataset */}
        <div className="admin-card">
          <div className="admin-card-icon">📂</div>

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
          <div className="admin-card-icon">🧠</div>

          <h3 className="admin-card-title">Retrain Model</h3>
          <p className="admin-card-desc">
            Rebuild all models using the latest datasets. This may take time.
          </p>

          <button className="admin-card-btn danger" onClick={retrain}>
            Start Training
          </button>
        </div>
      </div>

      <pre className="admin-status">{status}</pre>

      {/* ✅ TRENDS SECTION BELOW */}
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

                    <p className={`trend-percent ${up ? "up" : down ? "down" : ""}`}>
                      {up && "▲"}
                      {down && "▼"}
                      {!up && !down && "●"} {Math.abs(data.change_percent)}%
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
                      <p className="trend-alert">⚠ Spike detected</p>
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
              <b>{surveyOverview.avg_votes.toFixed(2)}</b>
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
                {flaggedTerms.map((item, idx) => (
                  <tr key={idx}>
                    <td>{item.word}</td>
                    <td>{item.context}</td>
                    <td>{item.frequency}</td>
                    <td>
                      {new Date(item.created_at).toLocaleDateString()}
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

