import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import FeedbackModal from "../components/FeedbackModal";


export default function Home() {
    const [text, setText] = useState("");
    const [result, setResult] = useState({
        label: null,
        confidence: null,
        language: null,
        latency_ms: null,
        expanded: false,
    });
    const [loading, setLoading] = useState(false);
    const [analytics, setAnalytics] = useState(null);
    const [showFeedbackModal, setShowFeedbackModal] = useState(false);
    const [history, setHistory] = useState([]);
    const pieData = [
    {
        name: "Normal",
        value: history.filter(h => h.result === "Normal").length,
    },
    {
        name: "Offensive",
        value: history.filter(h => h.result === "Offensive").length,
    },
    {
        name: "Hate",
        value: history.filter(h => h.result === "Hate").length,
    },
    ];


async function loadDashboardData() {
    const analytics = await fetch("http://127.0.0.1:5000/analytics")
        .then(r => r.json());

    const history = await fetch("http://127.0.0.1:5000/history?page=1&limit=10")
        .then(r => r.json());

    setAnalytics(analytics);
    setHistory(history.data);
}



    useEffect(() => {
        loadDashboardData();
    }, []);

    async function analyze() {
        if (!text.trim()) return;

        setLoading(true);

        const res = await fetch("http://127.0.0.1:5000/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });

        const data = await res.json();

        setResult({
            ...data,
            expanded: true,
        });

        setLoading(false);
        loadDashboardData();
    }


    return (
        <div style={{ padding: 40 }}>
            <div className="home-hero">
            <p className="home-subheading">
                Search HateSpeech With AI & ML
            </p>

            <h1 className="home-title">
                AI-Based Hate Speech <br />
                & Offensive Language Detection
            </h1>
            </div>


            <br /><br />
            <div className="input-container">
                <textarea
                    className="ai-input"
                    rows={4}
                    placeholder="Enter text to analyze..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                />
                <div className="input-highlight"></div>

                <button
                    className="analyze-btn"
                    onClick={analyze}
                    disabled={loading}
                >
                    {loading ? "Analyzing..." : "Analyze"}
                </button>
                </div>   {/* ✅ CLOSE input-container HERE */}


                <div
                className={`result-card ${
                    result.label === 0
                    ? "result-normal"
                    : result.label === 1
                    ? "result-offensive"
                    : result.label === 2
                    ? "result-hate"
                    : ""
                } ${result.expanded ? "expanded" : "collapsed"}`}
            >


                <p className="result-heading">
                    Result
                </p>

                {result.expanded && (
                    <>
                    <p className="result-status">
                        {result.label === 0
                        ? "Normal"
                        : result.label === 1
                        ? "Offensive"
                        : "Hate Speech"}
                    </p>

                    <p className="result-desc">
                        Confidence: {(result.confidence * 100).toFixed(1)}%
                    </p>

                    <p className="result-desc">
                        Language: {result.language}
                    </p>

                    <p className="result-desc">
                        Latency: {result.latency_ms} ms
                    </p>

                    <div className="buttonContainer">
                        <button
                            className="acceptButton"
                            onClick={() => setShowFeedbackModal(true)}
                        >
                            Feedback
                        </button>

                        <button
                        className="declineButton"
                        onClick={() =>
                            setResult((prev) => ({ ...prev, expanded: false }))
                        }
                        >
                        Close
                        </button>
                    </div>
                    </>
                )}
            </div>




            <div className="stats-cards">

            {/* Models */}
            <div className="card">
                <div className="card-content">
                <p className="card-value">5</p>
                <p className="card-title">Models</p>
                <p className="card-para">Available</p>
                </div>
            </div>

            {/* Texts Scanned — FIXED */}
            <div className="card">
                <div className="card-content">
                <p className="card-value">
                {analytics ? analytics.total_predictions : "—"}
                </p>
                <p className="card-title">Texts Scanned</p>
                <p className="card-para">All Time</p>
                </div>
            </div>

            {/* Best Model */}
            <div className="card">
                <div className="card-content">
                <p className="card-value">91%</p>
                <p className="card-title">Best Model</p>
                <p className="card-para">Accuracy</p>
                </div>
            </div>

            </div>

            {history.length > 0 && (
            <div className="chart-card">
                <p className="chart-title">Recent Predictions</p>
                <p className="chart-subtitle">Last 10 analyzed texts</p>

                <PieChart width={260} height={260}>
                <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    innerRadius={50}   // ⬅️ donut style (modern)
                    paddingAngle={4}
                >
                    <Cell fill="#22C55E" />   {/* Normal */}
                    <Cell fill="#F59E0B" />   {/* Offensive */}
                    <Cell fill="#EF4444" />   {/* Hate */}
                </Pie>

                <Tooltip />
                <Legend verticalAlign="bottom" height={36} />
                </PieChart>
            </div>
            )}


            {showFeedbackModal && (
                <FeedbackModal
                    onClose={() => setShowFeedbackModal(false)}
                    onSubmit={async (label) => {
                    await fetch("http://127.0.0.1:5000/feedback", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            text: text,
                            language: result.language,
                            correct_label: label,
                        }),
                    });

                    setShowFeedbackModal(false);
                    alert("✅ Feedback saved. Thank you!");
                    }}
                />
            )}
            {/* =========================
                API CTA (BOTTOM)
            ========================= */}
            <div
            style={{
                marginTop: 80,
                paddingTop: 30,
                borderTop: "1px solid rgba(0,0,0,0.1)",
                textAlign: "center",
                opacity: 0.85,
            }}
            >
            <p style={{ marginBottom: 12 }}>
                Want to integrate our AI into your own application?
            </p>

            <a
                href="/api"
                style={{
                display: "inline-block",
                padding: "10px 22px",
                borderRadius: 999,
                fontWeight: 700,
                fontSize: 14,
                textDecoration: "none",
                color: "#ffffff",
                background:
                    "linear-gradient(90deg, var(--deep-twilight), var(--turquoise-surf))",
                transition: "transform 0.2s ease, box-shadow 0.2s ease",
                }}
                onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow =
                    "0 10px 25px rgba(0,180,216,0.35)";
                }}
                onMouseLeave={(e) => {
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.boxShadow = "none";
                }}
            >
                Get API Key
            </a>
            </div>


        </div>
    );
}