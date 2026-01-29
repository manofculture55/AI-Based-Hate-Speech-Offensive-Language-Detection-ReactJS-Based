import { useEffect, useState } from "react";

export default function History() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);


  useEffect(() => {
    setLoading(true);

    fetch(`http://127.0.0.1:5000/history?page=${page}&limit=20`)
      .then(res => res.json())
      .then(data => {
        setRows(data.data);
        setTotalPages(data.pages);   // ⬅️ important
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [page]);



  return (
    <div className="history-card">
      <h1 className="history-title">Prediction History</h1>

      {loading && <p className="history-loading">Loading...</p>}

      {!loading && rows.length === 0 && (
        <p className="history-empty">No history found.</p>
      )}

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
                    title={row.text}   // ⬅️ native tooltip (full text)
                  >
                    {row.text.length > 60
                      ? row.text.slice(0, 60) + "..."
                      : row.text}
                  </td>
                  <td>
                    <span
                      className={`history-badge ${
                        row.result === "Normal"
                          ? "badge-normal"
                          : row.result === "Offensive"
                          ? "badge-offensive"
                          : "badge-hate"
                      }`}
                    >
                      {row.result}
                    </span>
                  </td>
                  <td>{row.score}</td>
                  <td>{row.latency_ms}</td>
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
