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
        with open("C:/Users/tobyl/OneDrive/Documents/4th Year/Dissertation/Repository/Model Training/Finalised Model/final_model_improved.pkl", "rb") as model_file:
            model = pickle.load(model_file)
        with open("C:/Users/tobyl/OneDrive/Documents/4th Year/Dissertation/Repository/Model Training/Finalised Model/tfidf_vectoriser_improved.pkl", "rb") as vectorizer_file:
            vectoriser = pickle.load(vectorizer_file)
        with open("C:/Users/tobyl/OneDrive/Documents/4th Year/Dissertation/Repository/Model Training/Finalised Model/label_encoder_improved.pkl", "rb") as encoder_file:
            label_encoder = pickle.load(encoder_file)
        with open("C:/Users/tobyl/OneDrive/Documents/4th Year/Dissertation/Repository/Model Training/Finalised Model/feature_order.pkl", "rb") as feature_order:
            feature_order = pickle.load(feature_order)
            print("Loaded feature order from pickle:", feature_order)
        return model, vectoriser, label_encoder, feature_order
    except FileNotFoundError as e:
        st.error(f"Model file not found: {e}")
        return None, None, None, None

# Function to extract VADER sentiment scores
def extract_vader_scores(text):
    # Initialise a vader analyser
    analyser = SentimentIntensityAnalyzer()
    scores = analyser.polarity_scores(text)
    # Returns a dictionary mathcing the models vader extraction methodology
    return {
        'pos': scores['pos'], 
        'neg': scores['neg'], 
        'neu': scores['neu'], 
        'compound': scores['compound']
    }

# Function to analyse sentiment of headlines
def analyse_headlines_sentiment(headlines_df):
    model, vectoriser, label_encoder, feature_order = load_model()
    
    if model is None or vectoriser is None or label_encoder is None or feature_order is None:
        st.error("Failed to load sentiment analysis model. Please check if model files exist.")
        return None, headlines_df
    
    results = {"Positive": [], "Neutral": [], "Negative": []}
    
    # Process each headline
    processed_features = []
    vader_scores_list = []
    
    for headline in headlines_df["Headline"].dropna():
        # Extract VADER scores
        vader_scores = extract_vader_scores(headline)
        vader_scores_list.append(vader_scores)
        
        # Extract TF-IDF features
        tfidf_features = vectoriser.transform([headline]).toarray()[0]
        
        # Create a DataFrame for this headline's TF-IDF features
        headline_tfidf_df = pd.DataFrame([tfidf_features], columns=vectoriser.get_feature_names_out())
        
        # Reindex to match original feature order, filling missing columns with 0
        headline_tfidf_df = headline_tfidf_df.reindex(columns=feature_order, fill_value=0)
        
        processed_features.append(headline_tfidf_df)
    
    # Combine all features
    if processed_features:
        features_df = pd.concat(processed_features, ignore_index=True)
        
        # Add VADER scores to features, VADER added first to match the trained model
        vader_df = pd.DataFrame(vader_scores_list)
        final_features = pd.concat([vader_df, features_df], axis=1)
        
        # Predict sentiment and get confidence score
        probs = model.predict_proba(final_features)
        predictions = np.argmax(probs, axis=1)
        confidences = np.max(probs, axis=1)
        
        sentiments = label_encoder.inverse_transform(predictions)
        
        # Update results and headline sentiments and their confidence scores
        for headline, sentiment, confidence in zip(headlines_df["Headline"].dropna(), sentiments, confidences):
            results[sentiment].append(f"{headline} ({confidence:.2%} confidence)")
            idx = headlines_df.index[headlines_df['Headline'] == headline][0]
            headlines_df.at[idx, 'Sentiment'] = sentiment
    
    return results, headlines_df