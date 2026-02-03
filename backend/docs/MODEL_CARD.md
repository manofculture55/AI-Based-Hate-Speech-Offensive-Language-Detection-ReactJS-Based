# Model Card: AI-Based Hate Speech & Offensive Language Detection

**Project:** KRIXION Internship Challenge  
**Developer:** [Your Name]  
**Year:** 2025–2026  
**Model Version:** 1.0 (Final Submission)  

**Input:** Multilingual Social Media Text (English, Hindi, Hinglish)  
**Output:** Multi-class Classification  
- 0 → Normal  
- 1 → Offensive  
- 2 → Hate Speech  

**Execution Mode:** Fully Offline (CPU-only, No Internet, No External APIs)

---

## 1. Model Overview

This project implements a **multi-stage AI-based hate speech detection pipeline** designed specifically for **multilingual and code-mixed Indian social media content**.

The system classifies text into **Normal**, **Offensive**, or **Hate Speech** categories while operating **entirely offline**.  
It is optimized for **low latency**, **privacy**, and **real-world deployment** on CPU-only environments.

Instead of relying on a single model, the system follows a **layered architecture**, allowing multiple models to be trained, evaluated, and compared.

---

## 2. Model Architecture (Multi-Stage Pipeline)

The system uses a **progressive model architecture**, where complexity increases at each stage.

### Stage 1 — Baseline Models (Classical ML)
Used for fast inference and baseline comparison.

- TF-IDF + Naïve Bayes  
- TF-IDF + Logistic Regression  
- TF-IDF + Support Vector Machine (SVM)

These models provide explainability and serve as fallback classifiers.

---

### Stage 2 — Deep Learning Models (Primary Stage)
Used for production inference due to best accuracy–latency tradeoff.

- **Bidirectional LSTM (BiLSTM)**  
- CNN-based Text Classifier (1D Convolution)

The BiLSTM model was selected as the **champion model**.

---

### Stage 3 — Transformer Models (Inference-Only)
Used for benchmarking and high-context understanding.

- DistilBERT (pre-trained, inference-only)

Transformer models are not fine-tuned due to offline and CPU constraints.

---

## 3. Training Data & Dataset Sources

### Datasets Used

| Dataset | Description |
|------|------------|
| **Bohra et al. (2018)** | Hindi–English code-mixed hate speech dataset |
| **Indo-HateSpeech (2024)** | Modern multilingual Indian social media data |
| **HASOC (2019)** | Multi-class hate and offensive content dataset |

These datasets were chosen because they contain:
- Code-mixed text
- Transliteration
- Region-specific linguistic patterns

---

### Dataset Split

- **Training:** 70%  
- **Validation:** 15%  
- **Testing:** 15%  

Splits were stratified to maintain class balance.

---

## 4. Text Preprocessing Pipeline

The following preprocessing steps are applied consistently across all models:

1. Removal of URLs, mentions, and special symbols  
2. Lowercasing and text normalization  
3. Emoji normalization or removal  
4. Language detection (English / Hindi / Hinglish)  
5. Tokenization  
6. Padding and truncation for deep learning models  

This pipeline is optimized to handle **noisy, real-world social media text**.

---

## 5. Performance Evaluation

All models were evaluated on a held-out test set using standard metrics.

### 5.1 Model Comparison

| Stage | Model | Accuracy | F1-Score | Status |
|------|------|---------|----------|--------|
| Stage 1 | Naïve Bayes | 79.8% | 0.78 | Passed |
| Stage 1 | Logistic Regression | 76.7% | 0.76 | Passed |
| Stage 2 | **BiLSTM (Champion)** | **88.2%** | **0.87** | **Selected** |
| Stage 2 | CNN (TextCNN) | 86.5% | 0.85 | Passed |
| Stage 3 | DistilBERT | 86.9% | 0.85 | Passed |

### Champion Model Selection

The **BiLSTM** model was selected for production because it:
- Achieved the highest accuracy
- Maintained very low CPU latency
- Balanced performance across all three classes

---

## 6. Latency Benchmarks (CPU Only)

**Target:** p95 latency < 2 seconds  

| Model | Avg Latency | p95 Latency |
|-----|------------|-------------|
| Naïve Bayes | ~0.002 s | ~0.005 s |
| **BiLSTM** | **~0.045 s** | **~0.062 s** |
| DistilBERT | ~0.180 s | ~0.310 s |

All models meet the latency requirement for offline deployment.

---

## 7. Champion Model Architecture Details

**Model Type:** Bidirectional LSTM (BiLSTM)

- Embedding Dimension: 100  
- LSTM Units: 64 (bidirectional)  
- Dropout: 0.3  
- Optimizer: Adam  
- Loss Function: Sparse Categorical Crossentropy  
- Activation: Softmax  

The architecture is intentionally lightweight to ensure fast inference on CPU.

---

## 8. Human-in-the-Loop Learning

This system incorporates **human feedback** to improve accuracy over time:

- **Feedback Feature:** Users correct wrong predictions  
- **Survey Feature:** Users label random text samples  
- **Flag-Word Intelligence:** Harmful words are identified and stored  

These inputs are logged in a local SQLite database and used for:
- Error analysis
- Dataset improvement
- Future retraining

---

## 9. Intended Use Cases

- Social media content moderation  
- Gaming chat moderation  
- Educational research projects  
- Offline moderation tools  
- Privacy-sensitive deployments  

The model is **not designed** for real-time law enforcement or automated punitive systems.

---

## 10. Known Limitations

- Sarcasm and irony are difficult to detect without context  
- Extremely short text (< 3 words) may produce low confidence  
- Creative spellings and censored words can reduce accuracy  
- Cultural context may vary across regions  

These limitations are partially mitigated using human feedback.

---

## 11. Ethical Considerations

- No personal data is collected or transmitted  
- Fully offline execution ensures privacy  
- Human review is encouraged for critical decisions  
- The model is designed to **assist**, not replace, moderation teams  

---

## 12. Future Improvements

- Support for more Indian languages  
- Improved explainability (token-level highlighting)  
- Lightweight transformer optimization  
- Continuous retraining pipeline  

---

## 13. Disclaimer

This model is developed strictly for **educational and evaluation purposes** under the KRIXION Internship Challenge.

Predictions should not be treated as absolute truth and should be reviewed when used in sensitive environments.
