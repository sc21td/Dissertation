# For testing and showing improvements to the model without breaking current model at all

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.metrics import confusion_matrix
from lazypredict.Supervised import LazyClassifier

# Load dataset
df = pd.read_excel("DatasetTesting.xlsx", sheet_name="Dataset")

# Shuffle and split data into 70/30 split as before
train_df, test_df = train_test_split(df, test_size=0.3, random_state=42, stratify=df["Labelled Rating"])

# Extract text and labels
X_train, y_train = train_df["Statement"], train_df["Labelled Rating"]
X_test, y_test = test_df["Statement"], test_df["Labelled Rating"]

# Function to extract VADER sentiment scores
def extract_vader_scores(texts):
    analyser = SentimentIntensityAnalyzer()
    return np.array([list(analyser.polarity_scores(text).values()) for text in texts])

# Function to extract TF-IDF features
def extract_tfidf_features(train_texts, test_texts):
    # Bi-grams, remove stop words
    # Test 3
    #vectoriser = TfidfVectorizer(ngram_range=(1, 2), stop_words='english') 
    # Uni grams
    vectoriser = TfidfVectorizer(ngram_range=(1,1), max_features= 750) 
    # Adjust max features
    #vectoriser = TfidfVectorizer(max_features=max_features)
    X_train_tfidf = vectoriser.fit_transform(train_texts)
    X_test_tfidf = vectoriser.transform(test_texts)
    return X_train_tfidf, X_test_tfidf, vectoriser

def plot_confusion_matrix(y_true, y_pred, labels):
    cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.savefig("Confusion Matrix Test 8")
    plt.show()

# Test Case 1: VADER-Only Model
X_train_vader = extract_vader_scores(X_train)
X_test_vader = extract_vader_scores(X_test)
model_vader = LogisticRegression(max_iter=1000)
model_vader.fit(X_train_vader, y_train)
y_pred_vader = model_vader.predict(X_test_vader)
print("VADER-Only Model Performance:")
print(classification_report(y_test, y_pred_vader))

# Test Case 2: VADER + TF-IDF
# X_train_tfidf, X_test_tfidf, vectoriser = extract_tfidf_features(X_train, X_test)
# X_train_combined = np.hstack((X_train_vader, X_train_tfidf.toarray()))
# X_test_combined = np.hstack((X_test_vader, X_test_tfidf.toarray()))
# model = LogisticRegression()
# print("debugging," ,model.max_iter)
# model_combined = LogisticRegression(max_iter=100)
# model_combined.fit(X_train_combined, y_train)
# y_pred_combined = model_combined.predict(X_test_combined)
# print("Optimum combo, 750 max features, default iterations (100)")
# accuracy = accuracy_score(y_test, y_pred_combined)
# print(f"Model Accuracy: {accuracy:.2f}")

# Calculate F1 Score
# f1 = f1_score(y_test, y_pred_combined, average="weighted")
# print(f"F1 Score: {f1:.2f}")
# print(classification_report(y_test, y_pred_combined))

# Test Case 3: Hyperparameter Optimisation (n-grams & stop words handled in extract_tfidf_features function)
# Already applied bi-grams & stop-word removal above

# Test Case 4: LazyPredict to find the best classifier
# clf = LazyClassifier(verbose=0, ignore_warnings=True, custom_metric=None)
# models, predictions = clf.fit(X_train_combined, X_test_combined, y_train, y_test)
# print("LazyPredict Classifier Results:")
# print(models)

# unique_classes = sorted(y_test.unique())
# plot_confusion_matrix(y_test, y_pred_combined, unique_classes) 