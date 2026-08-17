// frontend/src/pages/Api.js

import { API_BASE_URL } from "../api/client";

const box = {
  background: "var(--bg-secondary)",
  padding: "14px 16px",
  borderRadius: 10,
  fontFamily: "monospace",
  wordBreak: "break-all",
};

const pre = {
  background: "var(--bg-secondary)",
  padding: 16,
  borderRadius: 10,
  fontSize: 14,
  overflowX: "auto",
};

export default function Api() {
  const endpoint = `${API_BASE_URL}/predictions`;

  return (
    <div style={{ padding: 40, maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 10 }}>Public API Access</h1>

      <p style={{ opacity: 0.75, marginBottom: 30 }}>
        Integrate our Hate Speech &amp; Offensive Language Detection system
        directly into your application using this REST API.
      </p>

      {/* API KEY */}
      <section style={{ marginBottom: 30 }}>
        <h2>Your API Key</h2>
        <p style={{ opacity: 0.7 }}>
          The key is configured on the server as <code>HSD_API_KEY</code> in{" "}
          <code>.env</code>. A fresh install ships with the default below —
          change it before deploying anywhere public.
        </p>

        <div style={box}>dev-api-key-change-me</div>
      </section>

      {/* ENDPOINT */}
      <section style={{ marginBottom: 30 }}>
        <h2>Endpoint</h2>

        <div style={box}>POST {endpoint}</div>

        <p style={{ opacity: 0.7, marginTop: 10 }}>
          The older <code>POST /api/classify</code> still works but is
          deprecated; its responses carry a <code>Deprecation</code> header.
        </p>
      </section>

      {/* HEADERS */}
      <section style={{ marginBottom: 30 }}>
        <h2>Headers</h2>

        <pre style={pre}>
{`Content-Type: application/json
X-API-KEY: <your key>      # optional unless the server sets
                           # HSD_REQUIRE_API_KEY=1`}
        </pre>
      </section>

      {/* REQUEST */}
      <section style={{ marginBottom: 30 }}>
        <h2>Request Body</h2>

        <pre style={pre}>
{`{
  "text": "you are stupid"
}`}
        </pre>
      </section>

      {/* RESPONSE */}
      <section style={{ marginBottom: 30 }}>
        <h2>Response — 201 Created</h2>

        <pre style={pre}>
{`{
  "id": 42,
  "text": "you are stupid",
  "label": 1,
  "label_name": "Offensive",
  "confidence": 0.8731,
  "probabilities": {
    "Normal": 0.0712,
    "Offensive": 0.8731,
    "Hate": 0.0557
  },
  "language": "en",
  "model": "BiLSTM",
  "latency_ms": 118
}`}
        </pre>

        <p style={{ opacity: 0.7 }}>
          The <code>Location</code> header points at{" "}
          <code>{`${API_BASE_URL}/predictions/{id}`}</code>, where the stored
          prediction can be read back.
        </p>
      </section>

      {/* ERRORS */}
      <section style={{ marginBottom: 30 }}>
        <h2>Errors</h2>

        <p style={{ opacity: 0.7 }}>
          Every failure returns JSON in the same shape, never an HTML page.
        </p>

        <pre style={pre}>
{`{
  "error": {
    "code": "validation_error",
    "message": "Request body failed validation.",
    "details": { "text": ["Length must be between 1 and 500 characters."] }
  },
  "status": 422
}`}
        </pre>

        <ul>
          <li><b>400</b> — malformed or missing body</li>
          <li><b>401</b> — missing or invalid API key</li>
          <li><b>404</b> — no such resource</li>
          <li><b>405</b> — wrong HTTP method (lists what is allowed)</li>
          <li><b>415</b> — Content-Type is not application/json</li>
          <li><b>422</b> — body failed validation</li>
          <li><b>503</b> — the model is not loaded</li>
        </ul>
      </section>

      {/* EXAMPLE */}
      <section style={{ marginBottom: 30 }}>
        <h2>Example</h2>

        <pre style={pre}>
{`curl -X POST ${endpoint} \\
  -H "Content-Type: application/json" \\
  -H "X-API-KEY: dev-api-key-change-me" \\
  -d '{"text": "you are stupid"}'`}
        </pre>
      </section>

      {/* LABEL INFO */}
      <section style={{ marginBottom: 30 }}>
        <h2>Label Meaning</h2>
        <ul>
          <li><b>0</b> - Normal</li>
          <li><b>1</b> - Offensive</li>
          <li><b>2</b> - Hate Speech</li>
        </ul>
      </section>

      {/* DISCOVERY */}
      <section>
        <h2>Discovering the rest</h2>
        <p style={{ opacity: 0.7 }}>
          <code>GET {API_BASE_URL}</code> returns a machine-readable index of
          every endpoint, and <code>GET {API_BASE_URL}/health</code> reports
          whether the model is loaded.
        </p>
      </section>
    </div>
  );
}
