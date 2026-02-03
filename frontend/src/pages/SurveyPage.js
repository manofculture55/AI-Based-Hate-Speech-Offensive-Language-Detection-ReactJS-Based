import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "../styles/SurveyPage.css";

const SurveyPage = () => {
  const [text, setText] = useState("");
  const [selectedLabel, setSelectedLabel] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const [questionCount, setQuestionCount] = useState(0);
  const MAX_QUESTIONS = 3;

  const API_BASE = "http://127.0.0.1:5000";
  const navigate = useNavigate();

  // Fetch next survey text
  const fetchNext = async () => {
    if (questionCount >= MAX_QUESTIONS) {
      setText("");
      setMessage("🎉 Thank you for completing the survey!");
      setLoading(false);
      return;
    }

    setLoading(true);
    setSelectedLabel(null);
    setMessage("");

    try {
      const res = await axios.get(`${API_BASE}/survey/next`);
      if (res.data.text) {
        setText(res.data.text);
      } else {
        setText("");
        setMessage("🎉 No more texts available for survey");
      }
    } catch (err) {
      setMessage("❌ Error loading survey text");
    }

    setLoading(false);
  };

  useEffect(() => {
    fetchNext();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submitVote = async () => {
    if (selectedLabel === null) {
      setMessage("Please select a label before submitting.");
      return;
    }

    try {
      await axios.post(`${API_BASE}/survey/submit`, {
        text: text,
        user_label: selectedLabel
      });

      const nextCount = questionCount + 1;
      setQuestionCount(nextCount);

      if (nextCount >= MAX_QUESTIONS) {
        setText("");
        setMessage("🎉 Thank you for completing the survey!");
        return;
      }

      setMessage("✅ Response recorded. Loading next...");
      setTimeout(fetchNext, 900);
    } catch (err) {
      setMessage("❌ Error submitting survey");
    }
  };


  return (
    <div className="survey-page">
      <div className="survey-box">
        <h2 className="survey-heading">
          Community Labeling Survey ({questionCount}/{MAX_QUESTIONS})
        </h2>

        <p className="survey-desc">
          Help improve our dataset by labeling real-world text samples.
        </p>

        {loading ? (
          <p className="survey-status">Loading...</p>
        ) : message && !text ? (
          <>
            <p className="survey-status">{message}</p>

            <button
              className="survey-submit-btn"
              style={{ marginTop: "18px" }}
              onClick={() => navigate("/")}
            >
              ⬅ Back to Home
            </button>
          </>
        ) : (
          <>
            <div className="survey-text-box">{text}</div>

            <div className="survey-options">
                <label className="option-normal">
                    <input
                        type="radio"
                        name="label"
                        checked={selectedLabel === 0}
                        onChange={() => setSelectedLabel(0)}
                    />
                    <span>Normal</span>
                </label>

                <label className="option-offensive">
                    <input
                        type="radio"
                        name="label"
                        checked={selectedLabel === 1}
                        onChange={() => setSelectedLabel(1)}
                    />
                    <span>Offensive</span>
                </label>

                <label className="option-hate">
                    <input
                        type="radio"
                        name="label"
                        checked={selectedLabel === 2}
                        onChange={() => setSelectedLabel(2)}
                    />
                    <span>Hate</span>
                    </label>

            </div>
            <button
              className="survey-submit-btn"
              onClick={submitVote}
            >
              Submit
            </button>



            {message && <p className="survey-message">{message}</p>}
          </>
        )}
      </div>
    </div>
  );
};

export default SurveyPage;
