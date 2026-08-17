import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/SurveyPage.css";
import * as api from "../api/client";

const SurveyPage = () => {
  const [text, setText] = useState("");
  const [selectedLabel, setSelectedLabel] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [questionCount, setQuestionCount] = useState(0);
  const MAX_QUESTIONS = 3;

  const navigate = useNavigate();

  // Fetch next survey text
  const fetchNext = async () => {
    if (questionCount >= MAX_QUESTIONS) {
      setText("");
      setMessage("Thank you for completing the survey.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setSelectedLabel(null);
    setMessage("");

    try {
      // Resolves to null once the corpus is exhausted (the API answers 404
      // with code `survey_exhausted`, which the client maps to null).
      const item = await api.survey.next();

      if (item) {
        setText(item.text);
      } else {
        setText("");
        setMessage("No more texts are available for labelling.");
      }
    } catch (err) {
      setText("");
      setMessage(err.message);
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

    if (submitting) return;
    setSubmitting(true);

    try {
      await api.survey.vote({ text, label: selectedLabel });

      const nextCount = questionCount + 1;
      setQuestionCount(nextCount);

      if (nextCount >= MAX_QUESTIONS) {
        setText("");
        setMessage("Thank you for completing the survey.");
        return;
      }

      setMessage("Response recorded. Loading next...");
      setTimeout(fetchNext, 900);
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSubmitting(false);
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
              Back to Home
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
              disabled={submitting}
            >
              {submitting ? "Submitting..." : "Submit"}
            </button>



            {message && <p className="survey-message">{message}</p>}
          </>
        )}
      </div>
    </div>
  );
};

export default SurveyPage;
