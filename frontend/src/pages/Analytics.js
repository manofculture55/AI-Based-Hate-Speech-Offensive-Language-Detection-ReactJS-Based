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
import * as api from "../api/client";

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



  const [error, setError] = useState(null);

  useEffect(() => {
    api.analytics
      .dashboard()
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div>Loading analytics…</div>;
  }

  if (!data) {
    return <div>Failed to load analytics. {error && `(${error})`}</div>;
  }

  /* ==============================
     TRAINED MODEL METRICS

     `models` is now {available, models: {...}} and reports availability
     honestly. The page used to read data.models.BiLSTM.f1 / .latency, which
     the backend filled with invented constants whenever it could not find the
     training report — which was always, because it looked in the wrong
     directory. Nothing is shown as a measurement unless it was measured.
     ============================== */
  const metricsAvailable = data.models?.available;
  const trainedModels = data.models?.models || {};
  const bilstm = trainedModels.bilstm || {};

  const fmtPercent = (value) =>
    typeof value === "number" ? `${Math.round(value * 100)}%` : "—";
  const fmtScore = (value) =>
    typeof value === "number" ? value.toFixed(2) : "—";

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
  const modelComparisonData = Object.entries(trainedModels)
    .filter(([, m]) => typeof m.accuracy === "number")
    .map(([name, m]) => ({
      model: name.toUpperCase(),
      accuracy: Math.round(m.accuracy * 100),
      macroF1: m.macro_f1 ? Math.round(m.macro_f1 * 100) : 0,
    }));

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
    <div>
      <h1 className="analytics-title">Analytics Dashboard</h1>

      {/* ================= KPI SUMMARY ================= */}
      <div className="stats-cards">
        <KpiCard
          title="Total Predictions"
          value={data.total_predictions}
          subtitle="All time"
        />

        <KpiCard
          title="Accuracy"
          value={fmtPercent(bilstm.accuracy)}
          subtitle={metricsAvailable ? "BiLSTM (test set)" : "No training report"}
        />

        <KpiCard
          title="F1 Score"
          value={fmtScore(bilstm.macro_f1)}
          subtitle={metricsAvailable ? "Macro Avg" : "No training report"}
        />

        <KpiCard
          title="Avg Latency"
          value={
            typeof data.avg_latency_ms === "number"
              ? `${Math.round(data.avg_latency_ms)} ms`
              : "—"
          }
          subtitle="Measured, all predictions"
        />
      </div>

      {!metricsAvailable && (
        <p className="analytics-notice">
          Model accuracy and F1 are unavailable because no training report
          exists yet. Run the training pipeline to generate
          <code> backend/reports/training_report_all.json</code>.
        </p>
      )}

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
          Test-set accuracy across trained models
        </p>

        {modelComparisonData.length === 0 ? (
          <p className="chart-empty">
            No trained model metrics yet. Run the training pipeline to populate
            this chart.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={modelComparisonData}
              layout="vertical"
              margin={{ left: 40 }}
            >
              {/* There used to be a second, style-less <Bar> for the same key
                  here, which rendered a stray duplicate series. */}
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis type="number" domain={[0, 100]} unit="%" />
              <YAxis type="category" dataKey="model" width={100} />
              <Tooltip />

              <Bar
                dataKey="accuracy"
                fill="#00B4D8"
                radius={[0, 6, 6, 0]}
                barSize={25}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
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
                <th>Actual / Predicted</th>
                <th>Normal</th>
                <th>Offensive</th>
                <th>Hate</th>
              </tr>
            </thead>
            <tbody>
              {/* The API keys this {actual: {predicted: count}} with label
                  names. It previously emitted the transposed orientation with
                  numeric keys, so this table read cell [pred][actual] — every
                  off-diagonal number was in the wrong cell. */}
              {[0, 1, 2].map((actual) => (
                <tr key={actual}>
                  <td><b>{LABEL_MAP[actual]}</b></td>
                  {[0, 1, 2].map((pred) => (
                    <td key={pred}>
                      {confusion[LABEL_MAP[actual]]?.[LABEL_MAP[pred]] || 0}
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
            <p>No misclassifications yet.</p>
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
