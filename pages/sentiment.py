import streamlit as st
import pickle
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer

# Load trained model and components
# Cached in streamlit to load quicker
@st.cache_resource
def load_model():
    with open("final_model.pkl", "rb") as model_file:
        model = pickle.load(model_file)
    with open("tfidf_vectoriser.pkl", "rb") as vectorizer_file:
        vectoriser = pickle.load(vectorizer_file)
    with open("label_encoder.pkl", "rb") as encoder_file:
        label_encoder = pickle.load(encoder_file)
    return model, vectoriser, label_encoder

model, vectoriser, label_encoder = load_model()

# Function to extract VADER sentiment scores
def extract_vader_scores(text):
    # Initialise a vader analyser
    analyser = SentimentIntensityAnalyzer()
    scores = analyser.polarity_scores(text)
    return pd.DataFrame([scores])

# Page title
st.title("📊 Tennis Headline Sentiment Classifier")

# Upload an Excel file for classification
uploaded_file = st.file_uploader("Upload an Excel file with a column 'Headline'", type=["xlsx"])

if uploaded_file:
    # Read Excel file into a DataFrame
    df = pd.read_excel(uploaded_file)

    # Check if 'Headline' column exists within Excel
    if 'Headline' not in df.columns:
        st.error("The uploaded file must contain a column named 'Headline'.")
    else:
        # Process each headline in the file
        results = {"Positive": [], "Neutral": [], "Negative": []}

        # Drop any empty rows
        for headline in df["Headline"].dropna():  
            # Extract VADER scores
            vader_scores = extract_vader_scores(headline)

            # Extract TF-IDF features
            tfidf_features = vectoriser.transform([headline]).toarray()
            feature_names = vectoriser.get_feature_names_out()
            tfidf_df = pd.DataFrame(tfidf_features, columns=feature_names)

            # Ensure TF-IDF features match training order
            expected_features = list(vectoriser.get_feature_names_out())
            tfidf_df = tfidf_df.reindex(columns=expected_features, fill_value=0)

            # Combine VADER sentiment scores and TF-IDF features
            features = pd.concat([vader_scores, tfidf_df], axis=1)

            # Ensure the final feature order matches training
            trained_feature_order = list(pd.read_excel("Train_Dataset_FinalV2.xlsx").drop(columns=["Labelled Rating"]).columns)
            features = features.reindex(columns=trained_feature_order, fill_value=0)

            # # Predict sentiment
            # prediction = model.predict(features)[0]
            # sentiment = label_encoder.inverse_transform([prediction])[0]

            # # Append to corresponding category
            # results[sentiment].append(headline)

            # Adding confidence
            # Process each headline in the file
            # Predict sentiment and get confidence score
            # Get probability scores for each class
            probs = model.predict_proba(features)  
            # Get index of highest probability class
            prediction = np.argmax(probs)  
            sentiment = label_encoder.inverse_transform([prediction])[0]
            # Get confidence score for the chosen class
            confidence = probs[0][prediction]  

            # Append to corresponding category with confidence percentage
            results[sentiment].append(f"{headline} ({confidence:.2%} confidence)")

        # Display results in three columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Positive")
            for headline in results["Positive"]:
                st.write("✅", headline)

        with col2:
            st.subheader("Neutral")
            for headline in results["Neutral"]:
                st.write("➖", headline)

        with col3:
            st.subheader("Negative")
            for headline in results["Negative"]:
                st.write("❌", headline)