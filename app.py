import streamlit as st

# Title
st.title("🎾 Tennis Sentiment & Performance Analysis")

st.write(
    "Welcome to the Tennis Sentiment & Performance Analysis App! "
    "Use the sidebar to navigate between different features."
)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Sentiment Analysis", "Player Statistics"])

# Load the appropriate page
if page == "Sentiment Analysis":
    from pages import sentiment
elif page == "Player Statistics":
    from pages import stats