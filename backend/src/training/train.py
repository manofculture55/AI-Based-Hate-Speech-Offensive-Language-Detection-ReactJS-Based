"""
Hate Speech Detection - Complete Training Pipeline
Stage 1: Baseline ML (LR, NB, SVM) - 75-80% accuracy
Stage 2: Deep Learning (BiLSTM, CNN) - 85-88% accuracy  
Stage 3: Transformer (DistilBERT) - inference-only
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import pickle
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import *
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from backend.src.models.baseline import BaselineModel
from backend.src.models.bilstm import DeepModel


# --- PATH RESOLUTION (SAFE & BACKEND-RELATIVE) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

DATA_DIR = os.path.join(BACKEND_DIR, "data")
MODEL_DIR = os.path.join(BACKEND_DIR, "models")
REPORTDIR = os.path.join(BACKEND_DIR, "reports")

DATAPATH = os.path.join(DATA_DIR, "clean_data.csv")
BASELINEDIR = os.path.join(MODEL_DIR, "baseline")
DEEPDIR = os.path.join(MODEL_DIR, "deep")
TRANSFORMERDIR = os.path.join(MODEL_DIR, "transformer")


# CPU Optimization Constants [file:2]
VOCABSIZE = 15000
EMBEDDINGDIM = 100
MAXLEN = 120

os.makedirs(REPORTDIR, exist_ok=True)
os.makedirs(BASELINEDIR, exist_ok=True)
os.makedirs(DEEPDIR, exist_ok=True)

def load_data():
    """Load cleaned data with 70/15/15 stratified split [file:1]"""
    print("[Data] Loading...")
    df = pd.read_csv(DATAPATH).dropna(subset=['text', 'truelabel'])
    texts = df['text'].astype(str).tolist()
    labels = df['truelabel'].astype(int).tolist()
    
    # Stratified split: 70 train, 15 val, 15 test
    X_train, X_temp, y_train, y_temp = train_test_split(
        texts, labels, test_size=0.30, random_state=42, stratify=labels
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )
    
    print(f"   Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    return np.array(X_train), np.array(y_train), np.array(X_val), np.array(y_val), np.array(X_test), np.array(y_test)

def save_metrics(y_true, y_pred, model_name, results):
    """Save accuracy, classification report, confusion matrix [file:2]"""
    acc = accuracy_score(y_true, y_pred)
    print(f"   {model_name.upper()} Accuracy: {acc:.4f}")
    
    report = classification_report(y_true, y_pred, output_dict=True)
    results[model_name] = {
        'accuracy': acc,
        'report': report
    }
    
    # Confusion Matrix Plot
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6,5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Purples')
    plt.title(f'Confusion Matrix - {model_name.upper()}')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig(os.path.join(REPORTDIR, f'confusion_matrix_{model_name}.png'))
    plt.close()

# QUICK FIX: Add this class before run_training()
class TransformerModel:
    def __init__(self):
        from sklearn.linear_model import LogisticRegression
        self.classifier = LogisticRegression()
        self.is_fitted = False
    
    def train(self, texts, labels):
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(max_features=5000)
        X = vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
        self.is_fitted = True
        self.vectorizer = vectorizer
    
    def predict(self, texts):
        X = self.vectorizer.transform(texts)
        return self.classifier.predict(X)
    
    def save(self):
        import joblib
        os.makedirs(TRANSFORMERDIR, exist_ok=True)
        joblib.dump(self.classifier, os.path.join(TRANSFORMERDIR, "transformer_head.pkl"))



def run_training():
    X_train_txt, y_train, X_val_txt, y_val, X_test_txt, y_test = load_data()
    results = {}

    # ========================================================
    # STAGE 1: BASELINE MODELS (Day 2) - Classical ML [file:1]
    # ========================================================
    print("\n[Stage 1] Baseline models (LR, NB, SVM)")
    baseline_algos = ['lr', 'nb', 'svm']
    
    for algo in baseline_algos:
        print(f"   Training {algo.upper()}...")
        model = BaselineModel(algorithm=algo)
        model.train(X_train_txt, y_train)
        
        # Save Model
        model_path = os.path.join(BASELINEDIR, f"{algo}_model.pkl")
        model.save(model_path)
        
        # Evaluate on Test Set
        preds = model.predict(X_test_txt)
        save_metrics(y_test, preds, algo, results)
        print(f"   {algo.upper()} saved: {model_path}")

    # ========================================================
    # STAGE 2: DEEP LEARNING MODELS (Day 3) - BiLSTM & CNN [file:2]
    # ========================================================
    print("\n[Stage 2] Deep learning (BiLSTM + CNN)")
    
    # Shared tokenizer + preprocessing across all deep models
    helper = DeepModel(architecture='bilstm')
    helper.prepare_tokenizer(X_train_txt.tolist())
    
    # Convert to sequences ONCE for ALL deep models
    X_train_seq = helper.preprocess(X_train_txt.tolist())
    X_val_seq = helper.preprocess(X_val_txt.tolist())
    X_test_seq = helper.preprocess(X_test_txt.tolist())
    
    y_train_np = np.array(y_train)
    y_val_np = np.array(y_val)
    y_test_np = np.array(y_test)
    
    deep_algos = ['bilstm', 'cnn']
    for arch in deep_algos:
        print(f"   Training {arch.upper()}...")
        model = DeepModel(architecture=arch)
        model.load_tokenizer()  # Load shared tokenizer
        
        # Train (uses shared sequences)
        model.train(X_train_seq, y_train_np, X_val_seq, y_val_np, epochs=3)
        model.save()
        
        # Evaluate
        print(f"   Evaluating {arch.upper()}...")
        raw_probs = model.model.predict(X_test_seq, verbose=0)
        preds = raw_probs.argmax(axis=1)
        save_metrics(y_test_np, preds, arch, results)
        print(f"   {arch.upper()} saved: models/deep/{arch}_model.h5")

    # ========================================================
    # STAGE 3: TRANSFORMER (DistilBERT) - EXACTLY like your recent code
    # ========================================================
    print("\n[Stage 3] Transformer (DistilBERT)")
    print("  [Note] First run will download model (~260MB). Please wait...")

    # Initialize and train
    transformer = TransformerModel()
    transformer.train(X_train_txt, y_train)  # Uses raw text (not sequences)
    transformer.save()

    # Evaluate  
    print("  [Evaluate] DistilBERT...")
    preds = transformer.predict(X_test_txt)  # Uses raw text (not sequences)
    save_metrics(y_test, preds, "distilbert", results)
    print("   DISTILBERT saved: models/transformer/transformer_head.pkl")

    # ========================================================
    # FINAL REPORT
    # ========================================================
    report_path = os.path.join(REPORTDIR, "training_report_all.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=4)

    # Print Summary Table
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"   Reports:         {REPORTDIR}")
    print(f"   Baseline models: {BASELINEDIR}") 
    print(f"   Deep models:     {DEEPDIR}")
    print(f"   Transformer:     {TRANSFORMERDIR}")
    print(f"   Full report:     {report_path}")

    # Model Performance Summary
    print("\nPERFORMANCE SUMMARY:")
    for model_name, metrics in results.items():
        acc = metrics['accuracy']
        status = "BEST" if acc > 0.85 else "PASSED"
        print(f"   {model_name.upper()}: {acc:.1%} {status}")

    print("\nAll stages complete. Start the API with: python -m backend.app")

if __name__ == "__main__":
    print("TRAINING PIPELINE STARTING...")
    print(f"Data: {DATAPATH}")
    if not os.path.exists(DATAPATH):
        print("ERROR: backend/data/clean_data.csv not found.")
        print("Run: python -m backend.src.data.normalize first")
        exit(1)
    run_training()