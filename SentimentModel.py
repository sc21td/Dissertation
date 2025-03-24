import pickle
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import streamlit as st

#############################
# SENTIMENT ANALYSIS FUNCTIONS
#############################

# Load trained model and components
@st.cache_resource
def load_model():
    try:
        with open("C:/Users/tobyl/OneDrive/Documents/4th Year/Dissertation/Repository/Model Training/Finalised Model/final_model.pkl", "rb") as model_file:
            model = pickle.load(model_file)
        with open("C:/Users/tobyl/OneDrive/Documents/4th Year/Dissertation/Repository/Model Training/Finalised Model/tfidf_vectoriser.pkl", "rb") as vectorizer_file:
            vectoriser = pickle.load(vectorizer_file)
        with open("C:/Users/tobyl/OneDrive/Documents/4th Year/Dissertation/Repository/Model Training/Finalised Model/label_encoder.pkl", "rb") as encoder_file:
            label_encoder = pickle.load(encoder_file)
        return model, vectoriser, label_encoder
    except FileNotFoundError as e:
        st.error(f"Model file not found: {e}")
        return None, None, None

# Function to extract VADER sentiment scores
def extract_vader_scores(text):
    # Initialise a vader analyser
    analyser = SentimentIntensityAnalyzer()
    scores = analyser.polarity_scores(text)
    return pd.DataFrame([scores])

# Function to analyse sentiment of headlines
def analyse_headlines_sentiment(headlines_df):
    model, vectoriser, label_encoder = load_model()
    
    if model is None or vectoriser is None or label_encoder is None:
        st.error("Failed to load sentiment analysis model. Please check if model files exist.")
        return None
    
    results = {"Positive": [], "Neutral": [], "Negative": []}
    
    # Process each headline
    for headline in headlines_df["Headline"].dropna():
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
        try:
            trained_feature_order = list(pd.read_excel("C:/Users/tobyl/OneDrive/Documents/4th Year/Dissertation/Repository/Model Training/Finalised Model/Train_Dataset_FinalV2.xlsx").drop(columns=["Labelled Rating"]).columns)
            features = features.reindex(columns=trained_feature_order, fill_value=0)
        except FileNotFoundError:
            st.warning("Training dataset file not found. Feature order may not match exactly.")
        
        # Predict sentiment and get confidence score
        probs = model.predict_proba(features)
        prediction = np.argmax(probs)
        sentiment = label_encoder.inverse_transform([prediction])[0]
        confidence = probs[0][prediction]
        
        # Append to corresponding category with confidence percentage
        results[sentiment].append(f"{headline} ({confidence:.2%} confidence)")
        
        # Update the sentiment in the original dataframe for later use
        idx = headlines_df.index[headlines_df['Headline'] == headline][0]
        headlines_df.at[idx, 'Sentiment'] = sentiment
    
    return results, headlines_df
