// frontend/src/pages/Api.js

export default function Api() {
  const API_KEY = "KRIXION_API_KEY_2026";
  const API_URL = "http://127.0.0.1:5000/api/classify";

  return (
    <div style={{ padding: 40, maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 10 }}>Public API Access</h1>

      <p style={{ opacity: 0.75, marginBottom: 30 }}>
        Integrate our Hate Speech & Offensive Language Detection system
        directly into your application using this API.
      </p>

      {/* API KEY */}
      <section style={{ marginBottom: 30 }}>
        <h2>Your API Key</h2>
        <p style={{ opacity: 0.7 }}>
          Use this key in every request header.
        </p>

        <div
          style={{
            background: "var(--bg-secondary)",
            padding: "14px 16px",
            borderRadius: 10,
            fontFamily: "monospace",
            wordBreak: "break-all",
          }}
        >
          {API_KEY}
        </div>
      </section>

      {/* ENDPOINT */}
      <section style={{ marginBottom: 30 }}>
        <h2>Endpoint</h2>

        <div
          style={{
            background: "var(--bg-secondary)",
            padding: "14px 16px",
            borderRadius: 10,
            fontFamily: "monospace",
          }}
        >
          POST {API_URL}
        </div>
      </section>

      {/* HEADERS */}
      <section style={{ marginBottom: 30 }}>
        <h2>Required Headers</h2>

        <pre
          style={{
            background: "var(--bg-secondary)",
            padding: 16,
            borderRadius: 10,
            fontSize: 14,
          }}
        >
{`Content-Type: application/json
X-API-KEY: ${API_KEY}`}
        </pre>
      </section>

      {/* REQUEST */}
      <section style={{ marginBottom: 30 }}>
        <h2>Request Body</h2>

        <pre
          style={{
            background: "var(--bg-secondary)",
            padding: 16,
            borderRadius: 10,
            fontSize: 14,
          }}
        >
{`{
  "text": "you are stupid"
}`}
        </pre>
      </section>

      {/* RESPONSE */}
      <section style={{ marginBottom: 30 }}>
        <h2>Response</h2>

        <pre
          style={{
            background: "var(--bg-secondary)",
            padding: 16,
            borderRadius: 10,
            fontSize: 14,
          }}
        >
{`{
  "label": 1
}`}
        </pre>
      </section>

      {/* LABEL INFO */}
      <section>
        <h2>Label Meaning</h2>
        <ul>
          <li><b>0</b> → Normal</li>
          <li><b>1</b> → Offensive</li>
          <li><b>2</b> → Hate Speech</li>
        </ul>
      </section>
    </div>
  );
}
