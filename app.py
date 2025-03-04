# Import necessary libraries
import streamlit as st  # Streamlit for building the web app
import pickle  # Pickle for loading the pre-trained model and other components
import pandas as pd  # Pandas for handling data
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # VADER for sentiment scoring
from sklearn.feature_extraction.text import TfidfVectorizer  # TF-IDF for text vectorisation

# Load trained model and components
@st.cache_resource  # Cache the model to improve performance and prevent reloading on each interaction
def load_model():
    # Load the trained sentiment classification model
    with open("final_model.pkl", "rb") as model_file:
        model = pickle.load(model_file)
    
    # Load the trained TF-IDF vectoriser
    with open("tfidf_vectoriser.pkl", "rb") as vectorizer_file:
        vectoriser = pickle.load(vectorizer_file)
    
    # Load the label encoder to convert predictions back to sentiment labels
    with open("label_encoder.pkl", "rb") as encoder_file:
        label_encoder = pickle.load(encoder_file)
    
    return model, vectoriser, label_encoder

# Load the pre-trained model, vectoriser, and label encoder
model, vectoriser, label_encoder = load_model()

# Function to extract VADER sentiment scores from a given text
def extract_vader_scores(text):
    analyzer = SentimentIntensityAnalyzer()  # Initialise VADER sentiment analyser
    scores = analyzer.polarity_scores(text)  # Get sentiment scores
    return pd.DataFrame([scores])  # Convert to DataFrame for easier processing

# Streamlit UI setup
st.title("Tennis Headline Sentiment Classifier 🎾")

# Ensure input is stored in session state to prevent duplication
if "headline" not in st.session_state:
    st.session_state.headline = ""

st.session_state.headline = st.text_input("Enter a tennis headline:", st.session_state.headline, key="headline_input")

# Ensure session state stores predictions and explanations
if "prediction" not in st.session_state:
    st.session_state.prediction = None
if "sentiment" not in st.session_state:
    st.session_state.sentiment = None
if "vader_scores" not in st.session_state:
    st.session_state.vader_scores = None
if "top_positive_features" not in st.session_state:
    st.session_state.top_positive_features = []
if "top_negative_features" not in st.session_state:
    st.session_state.top_negative_features = []

# Classify sentiment when button is clicked
if st.button("Classify Sentiment"):
    if st.session_state.headline:
        headline = st.session_state.headline  # Retrieve stored headline

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

        # Predict sentiment
        prediction = model.predict(features)[0]
        sentiment = label_encoder.inverse_transform([prediction])[0]

        # Store prediction in session state
        st.session_state.prediction = prediction
        st.session_state.sentiment = sentiment
        st.session_state.vader_scores = vader_scores

        # Extract model coefficients (weights)
        coef = model.coef_[prediction]  
        feature_impact = dict(zip(trained_feature_order, coef))  

        # Keep only words that are actually in the input headline
        # Convert headline into a set of words
        headline_words = set(headline.lower().split())  

        # Filter for only words present in the headline
        filtered_impact = {word: weight for word, weight in feature_impact.items() if word in headline_words}

        # Identify top influential words within the headline
        st.session_state.top_positive_features = sorted(filtered_impact.items(), key=lambda x: x[1], reverse=True)[:5]
        st.session_state.top_negative_features = sorted(filtered_impact.items(), key=lambda x: x[1])[:5]


        # Display predicted sentiment
        st.write(f"**Predicted Sentiment:** {sentiment}")

# Only show the explanation button if a prediction has been made
if st.session_state.prediction is not None:
    if st.button("Explanation"):
        # Display explanation
        st.subheader("Model's Explanation")
        st.write(f"The model classified this headline as **{st.session_state.sentiment}** based on:")

        # Show VADER sentiment contributions
        st.write("🔹 **VADER Sentiment Scores:**")
        st.json(st.session_state.vader_scores.to_dict(orient="records")[0])  

        # Show top words influencing the decision
        st.write("🔹 **Top Words Influencing the Decision:**")
        st.write("📈 **Most Positive Impact:**")
        for word, weight in st.session_state.top_positive_features:
            st.write(f"- {word}: {weight:.4f}")

        st.write("📉 **Most Negative Impact:**")
        for word, weight in st.session_state.top_negative_features:
            st.write(f"- {word}: {weight:.4f}")



