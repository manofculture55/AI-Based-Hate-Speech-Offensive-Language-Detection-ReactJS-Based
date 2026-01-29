import "./FeedbackModal.css";

export default function FeedbackModal({ onClose, onSubmit }) {
  return (
    <div className="feedback-overlay" onClick={onClose}>
      <div
        className="feedback-modal"
        onClick={(e) => e.stopPropagation()}
      >
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
      </div>
    </div>
  );
}
