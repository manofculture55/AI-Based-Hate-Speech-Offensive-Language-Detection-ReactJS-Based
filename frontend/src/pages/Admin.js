import { useState } from "react";

const ADMIN_KEY = "KRIXION_ADMIN_2026";

export default function Admin() {
  const [authorized, setAuthorized] = useState(
    sessionStorage.getItem("admin_auth") === "true"
  );
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("");

  function login() {
    if (password === "admin123") {
      sessionStorage.setItem("admin_auth", "true");
      window.dispatchEvent(new Event("admin-auth-change"));
      setAuthorized(true);
      setPassword("");
    } else {
      alert("Wrong password");
    }
  }




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

        <h1 className="admin-title">
          Control Center
        </h1>

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
            <input
              type="file"
              accept=".csv"
              hidden
              onChange={uploadCSV}
            />
          </label>
        </div>

        {/* Retrain Model */}
        <div className="admin-card admin-card-danger">
          <div className="admin-card-icon">🧠</div>

          <h3 className="admin-card-title">Retrain Model</h3>
          <p className="admin-card-desc">
            Rebuild all models using the latest datasets. This may take time.
          </p>

          <button
            className="admin-card-btn danger"
            onClick={retrain}
          >
            Start Training
          </button>
        </div>

      </div>



      <pre className="admin-status">{status}</pre>
    </div>
  );
}
