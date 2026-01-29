import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

/* ==============================
   LOCAL KPI CARD COMPONENT
   ============================== */
function KpiCard({ title, value, subtitle }) {
  return (
    <div className="card">
      <div className="card-content">
        <p className="card-value">{value}</p>
        <p className="card-title">{title}</p>
        {subtitle && <p className="card-para">{subtitle}</p>}
      </div>
    </div>
  );
}

/* ==============================
   ANALYTICS PAGE
   ============================== */
export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);



  useEffect(() => {
    fetch("http://127.0.0.1:5000/analytics")
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ padding: 40 }}>Loading analytics…</div>;
  }

  if (!data) {
    return <div style={{ padding: 40 }}>Failed to load analytics.</div>;
  }

  const bilstm = data.models?.BiLSTM || {};

  /* ==============================
     CLASS DISTRIBUTION DATA
     ============================== */
  const pieData = [
    { name: "Normal", value: data.class_counts.normal },
    { name: "Offensive", value: data.class_counts.offensive },
    { name: "Hate", value: data.class_counts.hate },
  ];

  const PIE_COLORS = ["#22C55E", "#F59E0B", "#EF4444"];



  /* ==============================
     TREND DATA (DATE + COUNT)
     ============================== */
  const trendData = data.trend.dates.map((date, i) => ({
    date,
    predictions: data.trend.counts[i],
  }));



  /* ==============================
   MODEL COMPARISON DATA
   ============================== */
  const modelComparisonData = Object.entries(data.models || {}).map(
    ([name, m]) => ({
      model: name,
      accuracy: Math.round((m.accuracy || 0) * 100),
      latency: m.latency || 0,
    })
  );

  /* ==============================
   LANGUAGE DISTRIBUTION
   ============================== */
  const langDist = data.language?.language_distribution || {};

  const languagePieData = [
    { name: "English", value: langDist["en"] || 0 },
    { name: "Hindi", value: langDist["hi"] || 0 },
    { name: "Hinglish", value: langDist["hi-en"] || 0 },
  ];

  const LANG_COLORS = ["#38BDF8", "#22C55E", "#F59E0B"];

  /* ==============================
   LANGUAGE × CLASS MATRIX
   ============================== */
  const langMatrix = data.language?.language_class_matrix || {};

  const languageClassData = Object.entries(langMatrix).map(
    ([lang, classes]) => ({
      lang,
      Normal: classes.Normal || 0,
      Offensive: classes.Offensive || 0,
      Hate: classes.Hate || 0,
    })
  );



  const LABEL_MAP = {
    0: "Normal",
    1: "Offensive",
    2: "Hate",
  };

  /* ==============================
   ERROR ANALYSIS DATA
   ============================== */
  const errorAnalysis = data.error_analysis || {};
  const confusion = errorAnalysis.confusion || {};
  const errorSamples = errorAnalysis.samples || [];



  return (
    <div style={{ padding: 40 }}>
      <h1 style={{ marginBottom: 30 }}>Analytics Dashboard</h1>

      {/* ================= KPI SUMMARY ================= */}
      <div className="stats-cards">
        <KpiCard
          title="Total Predictions"
          value={data.total_predictions}
          subtitle="All time"
        />

        <KpiCard
          title="Accuracy"
          value={`${Math.round((bilstm.accuracy || 0) * 100)}%`}
          subtitle="BiLSTM"
        />

        <KpiCard
          title="F1 Score"
          value={(bilstm.f1 || 0).toFixed(2)}
          subtitle="Macro Avg"
        />

        <KpiCard
          title="Latency"
          value={`${bilstm.latency || "—"} ms`}
          subtitle="p95 CPU"
        />
      </div>

      {/* ================= CLASS + TREND ================= */}
      <div className="analytics-chart-row">
        {/* Class Distribution */}
        <div className="chart-card">
          <p className="chart-title">Class Distribution</p>
          <p className="chart-subtitle">
            Normal vs Offensive vs Hate
          </p>

          <PieChart width={300} height={300}>
            <Pie
              data={pieData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={110}
              paddingAngle={4}
            >
              {pieData.map((_, index) => (
                <Cell key={index} fill={PIE_COLORS[index]} />
              ))}
            </Pie>

            <Tooltip />


            <Legend verticalAlign="bottom" height={36} />
          </PieChart>
        </div>

        {/* Prediction Trend */}
        <div className="chart-card trend-card">
          <p className="chart-title">Prediction Trend</p>
          <p className="chart-subtitle">
            Number of predictions per day
          </p>

          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="date" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="predictions"
                stroke="#00B4D8"
                strokeWidth={3}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ================= MODEL COMPARISON ================= */}
      <div className="chart-card model-compare-card">
        <p className="chart-title">Model Comparison</p>
        <p className="chart-subtitle">
          Accuracy comparison across models
        </p>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={modelComparisonData}
            layout="vertical"
            margin={{ left: 40 }}
          >
          <Bar dataKey="accuracy" barSize={25} />
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis
              type="number"
              domain={[60, 100]}
              unit="%"
            />
            <YAxis
              type="category"
              dataKey="model"
              width={100}
            />
            <Tooltip />


            <Bar
              dataKey="accuracy"
              fill="#00B4D8"
              radius={[0, 6, 6, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ================= LANGUAGE INTELLIGENCE ================= */}
      <div className="analytics-chart-row">
        {/* Language Distribution */}
        <div className="chart-card">
          <p className="chart-title">Language Distribution</p>
          <p className="chart-subtitle">
            English vs Hindi vs Hinglish
          </p>

          <PieChart width={300} height={300}>
            <Pie
              data={languagePieData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={110}
              paddingAngle={4}
            >
              {languagePieData.map((_, index) => (
                <Cell key={index} fill={LANG_COLORS[index]} />
              ))}
            </Pie>
            <Tooltip />


            <Legend verticalAlign="bottom" height={36} />
          </PieChart>
        </div>

        {/* Language × Class */}
        <div className="chart-card trend-card">
          <p className="chart-title">Language vs Class</p>
          <p className="chart-subtitle">
            How content type varies across languages
          </p>

          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={languageClassData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="lang" />
              <YAxis allowDecimals={false} />
              <Tooltip />


              <Legend />
              <Bar dataKey="Normal" stackId="a" fill="#22C55E" barSize={40} />
              <Bar dataKey="Offensive" stackId="a" fill="#F59E0B" barSize={40} />
              <Bar dataKey="Hate" stackId="a" fill="#EF4444" barSize={40} />

            </BarChart>
          </ResponsiveContainer>

        </div>
      </div>


      {/* ================= ERROR ANALYSIS ================= */}
      <div className="analytics-chart-row">

        {/* Confusion Matrix */}
        <div className="chart-card error-half">
          <p className="chart-title">Error Analysis – Confusion Matrix</p>
          <p className="chart-subtitle">
            Actual label vs Predicted label (based on user feedback)
          </p>

          <table className="confusion-table">
            <thead>
              <tr>
                <th>Actual ↓ / Predicted →</th>
                <th>Normal</th>
                <th>Offensive</th>
                <th>Hate</th>
              </tr>
            </thead>
            <tbody>
              {[0, 1, 2].map((actual) => (
                <tr key={actual}>
                  <td><b>{LABEL_MAP[actual]}</b></td>
                  {[0, 1, 2].map((pred) => (
                    <td key={pred}>
                      {confusion[pred]?.[actual] || 0}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Misclassified Samples */}
        <div className="chart-card error-half">
          <p className="chart-title">Misclassified Examples</p>
          <p className="chart-subtitle">
            Recent user-corrected predictions
          </p>

          {errorSamples.length === 0 ? (
            <p style={{ color: "#666" }}>No misclassifications yet 🎉</p>
          ) : (
            <div className="error-table-wrapper">
              <table className="error-table">
                <thead>
                  <tr>
                    <th>Text</th>
                    <th>Language</th>
                    <th>Predicted</th>
                    <th>Actual</th>
                  </tr>
                </thead>
                <tbody>
                  {errorSamples.slice(0, 3).map((row, i) => (
                    <tr key={i}>
                      <td>{row.text}</td>
                      <td>{row.language}</td>
                      <td>{LABEL_MAP[row.predicted]}</td>
                      <td>{LABEL_MAP[row.actual]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>







    </div>
  );


}
