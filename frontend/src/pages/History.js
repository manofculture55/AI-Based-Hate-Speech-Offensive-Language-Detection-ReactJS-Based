import { useEffect, useState } from "react";
import * as api from "../api/client";

export default function History() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);


  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(null);

    api.predictions
      .list({ page, perPage: 20 })
      .then(data => {
        if (cancelled) return;
        setRows(data.data);
        setTotalPages(data.pagination.pages);
        setLoading(false);
      })
      .catch(err => {
        if (cancelled) return;
        setError(err.message);
        setLoading(false);
      });

    // Avoid a slow response for an old page overwriting a newer one.
    return () => {
      cancelled = true;
    };
  }, [page]);



  return (
    <div className="history-card">
      <h1 className="history-title">Prediction History</h1>

      {loading && <p className="history-loading">Loading...</p>}

      {error && <p className="history-empty">{error}</p>}

      {!loading && !error && rows.length === 0 && (
        <p className="history-empty">No history found.</p>
      )}

      <div className="history-actions">
        <button
          className="history-export-btn"
          onClick={() => {
            window.open(api.predictions.exportUrl());
          }}
        >
          Export CSV
        </button>
      </div>


      {!loading && rows.length > 0 && (
        <div className="history-table-wrapper">
          <table className="history-table">
            <thead>
              <tr>
                <th>Text</th>
                <th>Result</th>
                <th>Confidence</th>
                <th>Latency</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={idx}>
                  <td
                    className="history-text truncate"
                    title={row.text}   // native tooltip (full text)
                  >
                    {row.text.length > 60
                      ? row.text.slice(0, 60) + "..."
                      : row.text}
                  </td>
                  <td>
                    <span
                      className={`history-badge ${
                        row.label_name === "Normal"
                          ? "badge-normal"
                          : row.label_name === "Offensive"
                          ? "badge-offensive"
                          : "badge-hate"
                      }`}
                    >
                      {row.label_name}
                    </span>
                  </td>
                  {/* The API returns raw numbers now; formatting happens here. */}
                  <td>{(row.confidence * 100).toFixed(1)}%</td>
                  <td>{row.latency_ms} ms</td>
                  <td>{row.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && totalPages > 1 && (
            <div className="history-pagination">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
              >
                Prev
              </button>

              <span>
                Page {page} of {totalPages}
              </span>

              <button
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </button>
            </div>
          )}

        </div>
      )}
    </div>

  );
}
