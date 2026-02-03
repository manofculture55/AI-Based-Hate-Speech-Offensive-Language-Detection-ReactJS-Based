import { useState } from "react";
import "../styles/FeedbackModal.css";

export default function FeedbackModal({
  mode = "feedback",   // "feedback" | "improve"
  text = "",
  label = null,
  onClose,
  onSubmit,
}) {
  /* =========================
     IMPROVE MODE STATE
     ========================= */
  const [selectedWords, setSelectedWords] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  /* =========================
     HELPERS
     ========================= */

  function extractWords(text) {
    if (!text) return [];

    return Array.from(
      new Set(
        text
          .toLowerCase()
          // ✅ keep English + Devanagari, remove punctuation/emojis
          .replace(/[^\p{L}\p{M}\s]/gu, "")
          .split(/\s+/)
          .filter(w => w.length > 1)
      )
    );
  }


  function labelToText(label) {
    if (label === 1) return "Offensive";
    if (label === 2) return "Hate";
    return "Normal";
  }

  /* =========================
     IMPROVE MODE SUBMIT
     ========================= */
  async function submitImproveMode() {
    if (selectedWords.length === 0 || submitting) return;

    setSubmitting(true);

    await fetch("http://127.0.0.1:5000/feedback/flag-words", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        words: selectedWords,
        label: labelToText(label),
      }),
    });

    setSubmitting(false);
    setSelectedWords([]);
    onClose();

    alert("✅ Thanks! Your input will help improve accuracy.");
  }

  return (
    <div className="feedback-overlay" onClick={onClose}>
      <div
        className="feedback-modal"
        onClick={(e) => e.stopPropagation()}
      >

        {/* =========================
           FEEDBACK MODE
           ========================= */}
        {mode === "feedback" && (
          <>
            <h3>Is the prediction correct?</h3>
            <p>Select the correct label:</p>

            <div className="feedback-buttons">
              <button onClick={() => onSubmit(0)}>Normal</button>
              <button onClick={() => onSubmit(1)}>Offensive</button>
              <button onClick={() => onSubmit(2)}>Hate</button>
            </div>

            <button className="feedback-close" onClick={onClose}>
              Cancel
            </button>
          </>
        )}

        {/* =========================
            IMPROVE MODE
        ========================= */}
        {mode === "improve" && (
          <>
            <div className="improve-card">
              <h3 className="improve-title">
                Which word(s) could be the reason this text was rated{" "}
                <b>{labelToText(label)}</b>?
              </h3>


              <div className="improve-tags">
                {extractWords(text).map(word => {
                  const selected = selectedWords.includes(word);

                  return (
                    <span
                      key={word}
                      className={`improve-tag ${selected ? "selected" : ""}`}
                      onClick={() =>
                        setSelectedWords(prev =>
                          prev.includes(word)
                            ? prev.filter(w => w !== word)
                            : [...prev, word]
                        )
                      }
                    >
                      {word}
                    </span>
                  );
                })}
              </div>

              <div className="improve-actions">
                <button
                  className="improve-cancel"
                  onClick={onClose}
                >
                  Cancel
                </button>

                <button
                  className="improve-submit"
                  disabled={selectedWords.length === 0 || submitting}
                  onClick={submitImproveMode}
                >
                  {submitting ? "Submitting..." : "Submit"}
                </button>
              </div>

            </div>
          </>
        )}


      </div>
    </div>
  );
}
