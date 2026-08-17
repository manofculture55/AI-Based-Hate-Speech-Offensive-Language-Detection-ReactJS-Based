import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import FeedbackModal from "../components/FeedbackModal";
import { useNavigate } from "react-router-dom";
import * as api from "../api/client";

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
    const [error, setError] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    const [showFeedbackModal, setShowFeedbackModal] = useState(false);
    const [showImproveModal, setShowImproveModal] = useState(false);
    const [openStep, setOpenStep] = useState(null);
    const [history, setHistory] = useState([]);
    const [flaggedWords, setFlaggedWords] = useState([]);
    const navigate = useNavigate();
    const LABEL_COLORS = {
        Normal: "#22C55E",
        Offensive: "#F59E0B",
        Hate: "#EF4444",
    };



    const pieData = [
        {
            name: "Normal",
            value: history.filter(h => h.label_name === "Normal").length,
        },
        {
            name: "Offensive",
            value: history.filter(h => h.label_name === "Offensive").length,
        },
        {
            name: "Hate",
            value: history.filter(h => h.label_name === "Hate").length,
        },
    ];


    async function loadDashboardData() {
        try {
            const [analyticsData, historyData] = await Promise.all([
                api.analytics.dashboard(),
                api.predictions.list({ page: 1, perPage: 10 }),
            ]);

            setAnalytics(analyticsData);
            setHistory(historyData.data);
        } catch (err) {
            // The dashboard is supplementary; a failure here must not blank
            // out the analyzer.
            console.error("Failed to load dashboard data:", err.message);
        }
    }


    function highlightText(text, flaggedWords) {
        if (!text || flaggedWords.length === 0) return text;

        return text.split(/(\s+)/).map((chunk, i) => {
            const clean = chunk
                .toLowerCase()
                // same normalization as the backend and the modal
                .replace(/[^\p{L}\p{M}]/gu, "");

            if (flaggedWords.includes(clean)) {
                return (
                    <span key={i} className="flagged-word">
                    {chunk}
                    </span>
                );
            }
            return chunk;
        });
    }



    useEffect(() => {
        loadDashboardData();

        api.flaggedTerms
            .list()
            .then(data => setFlaggedWords(data.words || []))
            .catch(err =>
                console.error("Failed to load flagged terms:", err.message)
            );
    }, []);


    async function analyze() {
        if (!text.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const data = await api.predictions.create(text);

            setResult({
                ...data,
                expanded: true,
            });

            loadDashboardData();
        } catch (err) {
            // Surface the API's message instead of failing silently.
            setError(err.message);
            setResult(prev => ({ ...prev, expanded: false }));
        } finally {
            setLoading(false);
        }
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
                </div>   {/* end .input-container */}

                {error && (
                    <p className="analyze-error" role="alert">
                        {error}
                    </p>
                )}


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

                    <p className="result-desc highlighted-text">
                        {highlightText(text, flaggedWords)}
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

                    {(result.label === 1 || result.label === 2) && (
                    <div className="improve-hint">
                        Help to{" "}
                        <span
                        className="improve-btn"
                        onClick={() => setShowImproveModal(true)}
                        role="button"
                        tabIndex={0}
                        >
                        improve model
                        </span>
                    </div>
                    )}



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
                <div className="insight-card">

                    <div className="insight-card-header">
                    <h3>Recent Prediction Intelligence</h3>
                    <span className="insight-badge">Last 10</span>
                    </div>

                    <div className="insight-card-body">

                    {/* LEFT INSIGHTS */}
                    <div className="prediction-insights">
                        <div className="insight-item">
                        <span className="insight-label">Most Common</span>
                        <span className="insight-value">
                            {pieData.sort((a, b) => b.value - a.value)[0]?.name}
                        </span>
                        </div>

                        <div className="insight-item">
                        <span className="insight-label">Top Language</span>
                        <span className="insight-value">
                            {analytics?.language?.language_distribution
                            ? Object.entries(analytics.language.language_distribution)
                                .sort((a, b) => b[1] - a[1])[0]?.[0]
                            : "—"}
                        </span>
                        </div>

                        <div className="insight-item">
                        <span className="insight-label">Model</span>
                        <span className="insight-value">BiLSTM</span>
                        </div>
                    </div>

                    {/* CENTER CHART */}
                    <div className="insight-chart">
                        <PieChart width={260} height={260}>
                        <Pie
                            data={pieData}
                            dataKey="value"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            outerRadius={85}
                            innerRadius={50}
                            paddingAngle={4}
                        >
                            {pieData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={LABEL_COLORS[entry.name] || "#999"}
                                />
                            ))}
                        </Pie>
                        <Tooltip />
                        <Legend verticalAlign="bottom" height={36} />
                        </PieChart>
                    </div>

                    {/* RIGHT INSIGHTS */}
                    <div className="prediction-insights">
                        <div className="insight-item">
                        <span className="insight-label">Avg Confidence</span>
                        <span className="insight-value">
                            {/* confidence is a 0-1 float from the API; it used
                                to arrive as the string "87.3%" and was parsed
                                back into a number to average. */}
                            {Math.round(
                            (history.reduce((a, b) => a + b.confidence, 0) /
                                history.length) * 100
                            )}%
                        </span>
                        </div>

                        <div className="insight-item">
                        <span className="insight-label">Avg Latency</span>
                        <span className="insight-value">
                            {Math.round(
                            history.reduce((a, b) => a + b.latency_ms, 0) /
                                history.length
                            )} ms
                        </span>
                        </div>

                        <div className="insight-item">
                        <span className="insight-label">System Status</span>
                        <span className="insight-value success">Live</span>
                        </div>
                    </div>

                    </div>
                </div>
                )}





            {showFeedbackModal && (
                <FeedbackModal
                    onClose={() => setShowFeedbackModal(false)}
                    onSubmit={async (label) => {
                    try {
                        await api.annotations.create({
                            text,
                            label,
                            language: result.language,
                        });
                        setShowFeedbackModal(false);
                        alert("Feedback saved. Thank you!");
                    } catch (err) {
                        alert(`Could not save feedback: ${err.message}`);
                    }
                    }}
                />
            )}


            {showImproveModal && (
                <FeedbackModal
                    mode="improve"
                    text={text}
                    label={result.label}
                    onClose={() => setShowImproveModal(false)}
                />
            )}



            {/* =========================
                API ACCESS SECTION
            ========================= */}
            <div className="api-section">

            <h2 className="api-title">
                Powerful Hate Speech Detection API
            </h2>

            <p className="api-subtitle">
                Integrate multilingual hate speech & offensive language detection
                directly into your application — fast, secure, and offline-ready.
            </p>

            <div className="api-card-wrapper">

                <div className="api-card">
                <div className="api-card-border"></div>

                <div className="api-card-header">
                    <span className="api-badge">Developer API</span>
                    <h3 className="api-card-title">Why Use Our API?</h3>
                    <p className="api-card-desc">
                    Designed for real-world moderation systems, analytics platforms,
                    and privacy-first deployments.
                    </p>
                </div>

                <hr className="api-line" />

                <ul className="api-feature-list">
                    <li>Real-time hate & offensive content classification</li>
                    <li>Supports English, Hindi & Hinglish (code-mixed)</li>
                    <li>Offline inference — no third-party APIs</li>
                    <li>Low-latency, CPU-optimized predictions</li>
                    <li>Simple REST API with secure API key access</li>
                </ul>

                {/* floating CTA */}
                <a
                    href="/api"
                    className="api-glow-btn api-glow-btn-floating"
                >
                    Get API Key
                </a>

                </div>

            </div>
            </div>


            {/* =========================
                COMMUNITY SURVEY CARD
            ========================= */}
            <div className="survey-card-wrapper">
            <div className="survey-card">
                <h3 className="survey-title">Help Improve Our Dataset</h3>
                <p className="survey-subtitle">
                Review and label real-world text samples to make our AI more accurate.
                </p>

                <button
                    className="survey-btn"
                    onClick={() => navigate("/surveypage")}
                >
                    Take a Survey
                </button>
            </div>
            </div>




            {/* =========================
                PROJECT BENEFITS / FEATURES
            ========================= */}
            <div className="benefits-section">

            <h2 className="benefits-title">
                Use cases & Key features
            </h2>

            <p className="benefits-subtitle">
                Real-world impact, privacy-first AI, and multilingual intelligence
            </p>

            <div className="benefits-grid">

                {/* Card 1 */}
                <div className="benefit-card">
                <span className="benefit-badge">Use Case</span>
                <h3 className="benefit-heading">Smart Content Moderation</h3>
                <p className="benefit-text">
                    Automatically detects hate speech and offensive language in real time,
                    helping social platforms and communities stay safe and respectful.
                </p>
                </div>

                {/* Card 2 */}
                <div className="benefit-card">
                <span className="benefit-badge">Language AI</span>
                <h3 className="benefit-heading">Multilingual & Hinglish Support</h3>
                <p className="benefit-text">
                    Designed for Indian social media — accurately understands English,
                    Hindi, and Hinglish code-mixed content.
                </p>
                </div>

                {/* Card 3 */}
                <div className="benefit-card">
                <span className="benefit-badge">Privacy</span>
                <h3 className="benefit-heading">Fully Offline & Secure</h3>
                <p className="benefit-text">
                    Runs completely offline with no external APIs, ensuring data privacy,
                    compliance, and safe local deployment.
                </p>
                </div>

                {/* Card 4 */}
                <div className="benefit-card">
                <span className="benefit-badge">Insights</span>
                <h3 className="benefit-heading">Analytics & Actionable Insights</h3>
                <p className="benefit-text">
                    Provides trends, analytics, and error analysis to understand harmful
                    language patterns and improve moderation strategies.
                </p>
                </div>

            </div>
            </div>


            {/* =========================
                HOW IT WORKS / HOW TO USE
            ========================= */}
            <div className="how-section">

            <h2 className="how-title">How This Web App Works</h2>
            <p className="how-subtitle">
                Understand the workflow and try it instantly with real examples
            </p>

            <ol className="how-steps">

            {/* STEP 1 */}
            <li>
                <button
                className="step-toggle"
                onClick={() => setOpenStep(openStep === 1 ? null : 1)}
                >
                {openStep === 1 ? "-" : "+"}
                </button>

                <strong>Enter Text</strong> — Paste or type any English, Hindi, or Hinglish text.

                {openStep === 1 && (
                <div className="step-details">
                    The input text is first cleaned by removing URLs, emojis are normalized,
                    and the language (English / Hindi / Hinglish) is automatically detected.
                </div>
                )}
            </li>

            {/* STEP 2 */}
            <li>
                <button
                className="step-toggle"
                onClick={() => setOpenStep(openStep === 2 ? null : 2)}
                >
                {openStep === 2 ? "-" : "+"}
                </button>

                <strong>AI Analysis</strong> — The model processes the text.

                {openStep === 2 && (
                <div className="step-details">
                    The processed text is passed through a trained NLP pipeline
                    (TF-IDF / BiLSTM / Transformer) running fully offline on CPU.
                </div>
                )}
            </li>

            {/* STEP 3 */}
            <li>
                <button
                className="step-toggle"
                onClick={() => setOpenStep(openStep === 3 ? null : 3)}
                >
                {openStep === 3 ? "-" : "+"}
                </button>

                <strong>Instant Result</strong> — Classification is returned.

                {openStep === 3 && (
                <div className="step-details">
                    The model outputs a label (Normal, Offensive, or Hate Speech)
                    along with a confidence score and inference time.
                </div>
                )}
            </li>

            {/* STEP 4 */}
            <li>
                <button
                className="step-toggle"
                onClick={() => setOpenStep(openStep === 4 ? null : 4)}
                >
                {openStep === 4 ? "-" : "+"}
                </button>

                <strong>Insights & History</strong> — Results are stored and visualized.

                {openStep === 4 && (
                <div className="step-details">
                    Every prediction is stored locally in SQLite and later used
                    for analytics, trends, and performance visualization.
                </div>
                )}
            </li>

            </ol>


            {/* SAMPLE TEXTS */}
            <div className="sample-section">
            <h3 className="sample-title">Try These Sample Texts</h3>

            <div className="sample-alert normal">
                <div className="sample-content">
                <span className="sample-alert-title">Normal</span>
                <code>आज का दिन बहुत अच्छा है</code>
                </div>
            </div>

            <div className="sample-alert offensive">
                <div className="sample-content">
                <span className="sample-alert-title">Offensive</span>
                <code>You are so stupid and useless</code>
                </div>
            </div>

            <div className="sample-alert hate">
                <div className="sample-content">
                <span className="sample-alert-title">Hate Speech</span>
                <code>You are so stupid and useless, you should get out here fucking terrorist </code>
                </div>
            </div>
            </div>

            </div>

        </div>
    );
}