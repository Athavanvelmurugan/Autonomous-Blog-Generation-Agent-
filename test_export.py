import requests
import os

payload = {
    "title": "Machine Learning for Beginners: An Educational Blueprint",
    "topic": "Machine Learning for Beginners",
    "target_audience": "Beginner",
    "tone": "Informative",
    "content": """
# Machine Learning for Beginners: An Educational Blueprint

Welcome to the exciting world of Machine Learning (ML)! Think of machine learning like teaching a child to recognize fruits: instead of writing a million rules describing every possible curve of an apple, you show the computer thousands of photos of apples until it learns the underlying patterns itself.

## Table of Contents
- [Introduction & Intuition](#introduction-intuition)
- [Core Paradigms of Machine Learning](#core-paradigms-of-machine-learning)
- [Hands-on Python Implementation: Training Your First Classifier](#hands-on-python-implementation)
- [Comparative Breakdown of ML Approaches](#comparative-breakdown)
- [Common Pitfalls & Best Practices](#common-pitfalls-best-practices)
- [Frequently Asked Questions (FAQs)](#frequently-asked-questions)
- [Key Takeaways & Next Steps](#key-takeaways)

---

## Introduction & Intuition {#introduction-intuition}
Traditional software engineering operates on **Rules + Data = Answers**. In contrast, Machine Learning flips this paradigm on its head: **Data + Answers = Rules**.

Modern AI systems leverage statistical optimization to minimize prediction error across vast datasets. Whether you are filtering spam emails, receiving song recommendations on Spotify, or diagnosing medical anomalies from X-rays, machine learning algorithms are the silent engines powering these decisions.

---

## Core Paradigms of Machine Learning {#core-paradigms-of-machine-learning}
Machine learning is broadly categorized into three core branches:

1. **Supervised Learning**: The algorithm learns from labeled training data consisting of input features ($X$) and ground-truth targets ($y$). Examples include linear regression and classification trees.
2. **Unsupervised Learning**: The model explores unlabeled datasets to uncover hidden clusters, groupings, or dimensionality reductions (e.g., K-Means clustering, PCA).
3. **Reinforcement Learning**: An autonomous agent interacts with an environment, learning optimal behaviors by accumulating rewards or incurring penalties over time.

---

## Hands-on Python Implementation {#hands-on-python-implementation}
Here is a complete, runnable example using Python and `scikit-learn` to classify Iris flowers:

```python
# Import foundational scientific computing and machine learning libraries
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 1. Load the canonical Iris flower dataset
iris = load_iris()
X, y = iris.data, iris.target

# 2. Partition data: 80% for training, 20% for testing to prevent data leakage
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 3. Initialize an ensemble Random Forest classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)

# 4. Train the model on historical training data
model.fit(X_train, y_train)

# 5. Evaluate inference predictions on unseen validation data
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"Model Validation Accuracy: {accuracy * 100:.2f}%")
print("Detailed Performance Report:")
print(classification_report(y_test, predictions, target_names=iris.target_names))
```

### Line-by-Line Walkthrough:
- **`train_test_split`**: Ensures the model is tested on data it has never seen before, preventing overfitting.
- **`RandomForestClassifier`**: Uses an ensemble of 100 decision trees to cast votes, providing robust and interpretable classifications.
- **`accuracy_score`**: Calculates the percentage of correct predictions out of all test samples.

---

## Comparative Breakdown of ML Approaches {#comparative-breakdown}

| Paradigm | Training Signal | Common Algorithms | Practical Application | Key Trade-off |
| :--- | :--- | :--- | :--- | :--- |
| **Supervised Learning** | Labeled target labels ($y$) | Linear Regression, Random Forest, SVM | Fraud detection, image classification | High labeling cost |
| **Unsupervised Learning** | None (finds raw distribution) | K-Means, PCA, DBSCAN | Customer segmentation, anomaly detection | Subjective evaluation |
| **Reinforcement Learning** | Environmental reward signals | Q-Learning, PPO, Deep Q-Networks | Robotics, autonomous navigation, gaming | Sample inefficient |

---

## Common Pitfalls & Best Practices {#common-pitfalls-best-practices}

> **Pro Tip**: The biggest mistake junior data scientists make is not selecting the wrong algorithm, but testing models on data they inadvertently trained on (Data Leakage).

1. **Avoid Data Leakage**: Always fit feature scalers and preprocessing transformers strictly on your training partition, never on the full dataset before splitting.
2. **Beware of Overfitting**: When a model scores 99% on training data but 60% on test data, it has memorized noise. Counter this with regularization, dropout, or cross-validation.
3. **Always Establish a Naive Baseline**: Before training a multi-million parameter neural network, test a simple logistic regression or decision tree baseline.

---

## Frequently Asked Questions (FAQs) {#frequently-asked-questions}

### Q1: What math background do I need to start learning ML?
**Answer**: Basic linear algebra (vectors and matrices), introductory calculus (derivatives and gradients), and basic statistics (mean, variance, normal distributions) are sufficient to get started effectively.

### Q2: Why is Python the dominant language for Machine Learning?
**Answer**: Python provides an unrivaled ecosystem of mature scientific libraries like NumPy, Pandas, Scikit-Learn, PyTorch, and TensorFlow, combined with an approachable, clean syntax.

### Q3: How do I know if my model is ready for production?
**Answer**: A production-ready model must demonstrate consistent latency under load, verified performance on out-of-distribution drift tests, reproducible pipelines, and thorough monitoring for data drift.

---

## Key Takeaways & Next Steps {#key-takeaways}
- Machine learning learns patterns directly from data rather than relying on hardcoded static logic.
- Start with Supervised Learning before exploring complex neural networks.
- Always use rigorous train/test separation to guarantee generalization to real-world data.
"""
}

res_html = requests.post("http://127.0.0.1:8000/api/export/html", json=payload)
print("HTML export status:", res_html.status_code, "Length:", len(res_html.text))
with open("sample_export.html", "w", encoding="utf-8") as f:
    f.write(res_html.text)
print("Saved sample_export.html")

res_pdf = requests.post("http://127.0.0.1:8000/api/export/pdf", json=payload)
print("PDF export status:", res_pdf.status_code, "Length:", len(res_pdf.content))
with open("sample_export.pdf", "wb") as f:
    f.write(res_pdf.content)
print("Saved sample_export.pdf")
