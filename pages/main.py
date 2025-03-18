import streamlit as st
import pandas as pd
import numpy as np
import pickle
import requests
import os
import csv
import time
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer

# Configure page
st.set_page_config(layout="wide", page_title="Tennis Analysis Dashboard")

# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialise session state
if 'scraped_headlines' not in st.session_state:
    st.session_state.scraped_headlines = None
if 'sentiment_results' not in st.session_state:
    st.session_state.sentiment_results = {"Positive": [], "Neutral": [], "Negative": []}
if 'player_stats' not in st.session_state:
    st.session_state.player_stats = None
if 'current_step' not in st.session_state:
    # 1: Input, 2: Scraping, 3: Sentiment, 4: Stats
    st.session_state.current_step = 1  

# CSV file for storing irrelevant headlines
IGNORE_CSV = "irrelevant_headlines.csv"

#############################
# WEBSCRAPER FUNCTIONS
#############################

# Load existing ignored headlines from CSV
def load_ignored_headlines():
    logger.info("Attempting to load ignored headlines from CSV")
    
    if os.path.exists(IGNORE_CSV):
        headlines = set(pd.read_csv(IGNORE_CSV)["Headline"])
        logger.info(f"Loaded {len(headlines)} ignored headlines from CSV")
        return headlines
    
    logger.info(f"Ignored headlines file {IGNORE_CSV} not found")
    return set()

ignored_headlines = load_ignored_headlines()

# Function to save new irrelevant headlines to CSV
def save_ignored_headlines(new_ignored):
    logger.info(f"Attempting to save {len(new_ignored) if new_ignored else 0} new ignored headlines")
    
    if not new_ignored:
        logger.info("No new headlines to save")
        return

    # Append to CSV file
    with open(IGNORE_CSV, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for headline in new_ignored:
            writer.writerow([headline])
    
    logger.info(f"Saved {len(new_ignored)} new ignored headlines")

# Function to scrape BBC Sport headlines with URLs
def scrape_bbc_sport(player, tournament, year, max_pages=3):
    # For more efficient searching on BBC news split the player name
    # Only append the surname to the URL
    player_surname = player.split()[-1] 
    search_query = f"{player_surname} {tournament} {year}".replace(" ", "+")
    base_url = "https://www.bbc.co.uk/search?q="
    headlines_data = []
    all_headlines = []

    logger.info(f"Starting scrape with query: {search_query}, max_pages: {max_pages}")

    for page in range(1, max_pages + 1):
        url = f"{base_url}{search_query}&page={page}"
        
        logger.info(f"Fetching page {page} from URL: {url}")
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")

            if response.status_code != 200:
                st.warning(f"Failed to fetch page {page} (Status {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            
            logger.info(f"HTML retrieved, length: {len(response.text)} characters")
            
            # Directly search for span tags with aria-hidden="false"
            headline_tags = soup.find_all("span", attrs={"aria-hidden": "false"})
            logger.info(f"Found {len(headline_tags)} headline tags on page {page}")

            headlines_found_on_page = 0
            
            # Process each headline
            for headline_tag in headline_tags:
                headline = headline_tag.get_text(strip=True)
                all_headlines.append(headline)  
                
                logger.info(f"Found headline: {headline}")
                
                # Try to find associated link
                link_tag = None
                parent = headline_tag.parent
                for _ in range(3):  
                    if parent and parent.name == 'a' and parent.has_attr('href'):
                        link_tag = parent
                        break
                    elif parent:
                        link_tag = parent.find('a', href=True)
                        if link_tag:
                            break
                        parent = parent.parent
                    else:
                        break
                
                if link_tag:
                    article_url = link_tag["href"]
                    if not article_url.startswith("http"):
                        article_url = "https://www.bbc.co.uk" + article_url
                    logger.info(f"Found link for headline: {article_url}")
                else:
                    article_url = ""
                    logger.info("No link found for this headline")
                
                headlines_data.append({
                    "Headline": headline,
                    "Source": "BBC",
                    "URL": article_url,
                    "Sentiment": ""  # Empty for now
                })
                headlines_found_on_page += 1
            
            logger.info(f"Added {headlines_found_on_page} headlines from page {page}")
            
            if headlines_found_on_page == 0:
                logger.info("No headlines found on this page. Checking HTML structure:")
                page_title = soup.find('title')
                logger.info(f"Page title: {page_title.text if page_title else 'No title found'}")
                
                possible_headline_containers = [
                    ("divs with class containing 'result'", soup.find_all("div", class_=lambda x: x and 'result' in x)),
                    ("h3 tags", soup.find_all("h3")),
                    ("spans with role=heading", soup.find_all("span", attrs={"role": "heading"}))
                ]
                
                for desc, elements in possible_headline_containers:
                    logger.info(f"Found {len(elements)} {desc}")
                    if len(elements) > 0:
                        logger.info(f"Sample {desc}: {elements[0].get_text(strip=True) if elements[0] else 'empty'}")

        except Exception as e:
            logger.error(f"Error scraping page {page}: {str(e)}")
        
        logger.info(f"Sleeping for 1 second before next page")
        time.sleep(1)  
        
    # Identify duplicate headlines (if they appear more than once, they are irrelevant)
    logger.info(f"Processing {len(all_headlines)} total headlines for duplicates")
    duplicate_headlines = {h for h in all_headlines if all_headlines.count(h) > 1}
    logger.info(f"Found {len(duplicate_headlines)} duplicate headlines")
    
    # Update ignore list and remove duplicates
    ignored_headlines.update(duplicate_headlines)
    save_ignored_headlines(duplicate_headlines)
    
    # Filter out ignored and duplicate headlines
    filtered_data = [item for item in headlines_data if item["Headline"] not in ignored_headlines]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_filtered_data = []
    for item in filtered_data:
        headline = item["Headline"]
        if headline not in seen:
            seen.add(headline)
            unique_filtered_data.append(item)
    
    logger.info(f"Scraping complete. Found {len(unique_filtered_data)} unique relevant headlines after filtering")
    
    return pd.DataFrame(unique_filtered_data)

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

#############################
# STATS RETRIEVAL FUNCTIONS
#############################

def load_match_data():
    try:
        return pd.read_csv("atp_matches_2024.csv")
    except FileNotFoundError:
        st.error("ATP 2024 match data file not found. Please ensure the CSV is in the correct directory.")
        return pd.DataFrame()

def get_player_tournament_stats(df, player_name, tournament, year):
    # Filter matches where player is winner in the tournament
    player_winner_matches = df[
        (df["winner_name"] == player_name) & 
        (df["tourney_name"].str.contains(tournament, case=False, na=False))
    ]
    
    # Filter matches where player is loser in the tournament
    player_loser_matches = df[
        (df["loser_name"] == player_name) & 
        (df["tourney_name"].str.contains(tournament, case=False, na=False))
    ]

    # Combine winner and loser matches
    player_matches = pd.concat([player_winner_matches, player_loser_matches])

    # Return None if no matches found
    if player_matches.empty:
        return None, None

    # Compute tournament-specific statistics
    tournament_stats = {
        "Total Matches": len(player_matches),
        "Wins": len(player_winner_matches),
        "Losses": len(player_loser_matches),
        "Win Rate": len(player_winner_matches) / len(player_matches) * 100,
        "Avg Match Duration": player_matches["minutes"].mean(),
        
        "Tournament Aces": player_matches[
            player_matches["winner_name"] == player_name
        ]["w_ace"].mean() if not player_winner_matches.empty else player_matches[
            player_matches["loser_name"] == player_name
        ]["l_ace"].mean(),
        
        "Tournament Double Faults": player_matches[
            player_matches["winner_name"] == player_name
        ]["w_df"].mean() if not player_winner_matches.empty else player_matches[
            player_matches["loser_name"] == player_name
        ]["l_df"].mean(),
        
        "Break Points Faced": player_matches[
            player_matches["winner_name"] == player_name
        ]["w_bpFaced"].mean() if not player_winner_matches.empty else player_matches[
            player_matches["loser_name"] == player_name
        ]["l_bpFaced"].mean(),
        
        "Break Points Saved Percentage": (
            (player_matches[
                player_matches["winner_name"] == player_name
            ]["w_bpSaved"].mean() / player_matches[
                player_matches["winner_name"] == player_name
            ]["w_bpFaced"].mean() * 100) if not player_winner_matches.empty 
            else (player_matches[
                player_matches["loser_name"] == player_name
            ]["l_bpSaved"].mean() / player_matches[
                player_matches["loser_name"] == player_name
            ]["l_bpFaced"].mean() * 100)
        )
    }

    return player_matches, tournament_stats

def get_player_yearly_stats(df, player_name, year):
    # Filter matches where player is winner
    player_winner_matches = df[df["winner_name"] == player_name]
    # Filter matches where player is loser
    player_loser_matches = df[df["loser_name"] == player_name]

    # Combine winner and loser matches
    player_matches = pd.concat([player_winner_matches, player_loser_matches])

    # Return None if no matches found
    if player_matches.empty:
        return None

    # Compute yearly statistics
    yearly_stats = {
        "Total Matches": len(player_matches),
        "Wins": len(player_winner_matches),
        "Losses": len(player_loser_matches),
        "Win Rate": len(player_winner_matches) / len(player_matches) * 100,
        "Avg Match Duration": player_matches["minutes"].mean(),
        
        "Yearly Aces": player_matches[
            player_matches["winner_name"] == player_name
        ]["w_ace"].mean() if not player_winner_matches.empty else player_matches[
            player_matches["loser_name"] == player_name
        ]["l_ace"].mean(),
        
        "Yearly Double Faults": player_matches[
            player_matches["winner_name"] == player_name
        ]["w_df"].mean() if not player_winner_matches.empty else player_matches[
            player_matches["loser_name"] == player_name
        ]["l_df"].mean(),
        
        "Break Points Faced": player_matches[
            player_matches["winner_name"] == player_name
        ]["w_bpFaced"].mean() if not player_winner_matches.empty else player_matches[
            player_matches["loser_name"] == player_name
        ]["l_bpFaced"].mean(),
        
        "Break Points Saved Percentage": (
            (player_matches[
                player_matches["winner_name"] == player_name
            ]["w_bpSaved"].mean() / player_matches[
                player_matches["winner_name"] == player_name
            ]["w_bpFaced"].mean() * 100) if not player_winner_matches.empty 
            else (player_matches[
                player_matches["loser_name"] == player_name
            ]["l_bpSaved"].mean() / player_matches[
                player_matches["loser_name"] == player_name
            ]["l_bpFaced"].mean() * 100)
        )
    }

    return yearly_stats

#############################
# MAIN APPLICATION UI
#############################

def main():
    st.title("🎾 Tennis Media & Performance Analysis")
    
    # Create progress indicator for the workflow
    progress_cols = st.columns(4)
    with progress_cols[0]:
        param_status = "✅" if st.session_state.current_step > 1 else "⏳"
        st.markdown(f"### {param_status} 1. Select Parameters")
    with progress_cols[1]:
        scrape_status = "✅" if st.session_state.current_step > 2 else "⏳" if st.session_state.current_step == 2 else "⏱️"
        st.markdown(f"### {scrape_status} 2. Scrape Headlines")
    with progress_cols[2]:
        sentiment_status = "✅" if st.session_state.current_step > 3 else "⏳" if st.session_state.current_step == 3 else "⏱️"
        st.markdown(f"### {sentiment_status} 3. Analyse Sentiment")
    with progress_cols[3]:
        stats_status = "✅" if st.session_state.current_step > 4 else "⏳" if st.session_state.current_step == 4 else "⏱️"
        st.markdown(f"### {stats_status} 4. Performance Stats")
    
    st.markdown("---")
    
    # Parameter selection section
    st.subheader("Analysis Parameters")
    param_cols = st.columns(4)
    
    with param_cols[0]:
        # Load match data to get player list
        df = load_match_data()
        if not df.empty:
            all_players = sorted(set(df["winner_name"].unique()) | set(df["loser_name"].unique()))
            player_name = st.selectbox("Select Player:", all_players)
        else:
            player_name = st.text_input("Enter Player Name:")
    
    with param_cols[1]:
        # Select specific tournament, currently limited to grand slams
        tournament = st.selectbox("Enter Tournament Name:", ['Wimbledon','US Open', 'Australian Open', 'French Open'])
    
    with param_cols[2]:
        # Will add more later
        year = st.selectbox("Select Year:", [2024])
    
    with param_cols[3]:
        max_pages = st.slider("Pages to Scrape:", 1, 5, 3)
    
    # Main action button
    if st.button("Start Analysis"):
        # Move to scraping step
        st.session_state.current_step = 2  
        st.session_state.scraped_headlines = None
        st.session_state.sentiment_results = {"Positive": [], "Neutral": [], "Negative": []}
        st.session_state.player_stats = None
        st.rerun()
    
    st.markdown("---")
    
    # Web scraping section
    if st.session_state.current_step >= 2:
        st.subheader("Headline Scraping")
        
        if st.session_state.scraped_headlines is None:
            with st.spinner(f"Scraping headlines for {player_name} at {tournament} {year}..."):
                scraped_df = scrape_bbc_sport(player_name, tournament, year, max_pages)
                st.session_state.scraped_headlines = scraped_df
        
        if not st.session_state.scraped_headlines.empty:
            st.success(f"Found {len(st.session_state.scraped_headlines)} relevant headlines")
            
            # Show headlines in an expander
            with st.expander("View Scraped Headlines", expanded=True):
                for i, row in st.session_state.scraped_headlines.iterrows():
                    col1, col2 = st.columns([4, 1])
                    headline = row["Headline"]
                    url = row["URL"]
                    
                    with col1:
                        if url:
                            st.markdown(f"[{headline}]({url})")
                        else:
                            st.write(headline)
                    
                    with col2:
                        if st.button(f"Ignore", key=f"ignore_{i}"):
                            # Add to ignored headlines
                            ignored_headlines.add(headline)
                            save_ignored_headlines([headline])
                            st.success(f"Marked '{headline}' as irrelevant")
                            
                            # Remove from current results
                            st.session_state.scraped_headlines = st.session_state.scraped_headlines[
                                st.session_state.scraped_headlines["Headline"] != headline
                            ]
                            st.rerun()
            
            # Continue to sentiment analysis
            if st.button("Proceed to Sentiment Analysis"):
                st.session_state.current_step = 3
                st.rerun()
        else:
            st.warning("No headlines found. Try adjusting your search parameters.")
            # Allow returning to parameter selection
            st.session_state.current_step = 1
    
    # Sentiment analysis section
    if st.session_state.current_step >= 3:
        st.markdown("---")
        st.subheader("Sentiment Analysis")
        
        # Only run analysis if haven't already
        if all(len(results) == 0 for results in st.session_state.sentiment_results.values()):
            with st.spinner("Analysing headline sentiment..."):
                sentiment_results, updated_headlines = analyse_headlines_sentiment(st.session_state.scraped_headlines)
                st.session_state.sentiment_results = sentiment_results
                st.session_state.scraped_headlines = updated_headlines
        
        # Display results in three columns
        sentiment_cols = st.columns(3)
        
        with sentiment_cols[0]:
            st.markdown("### Positive")
            for headline in st.session_state.sentiment_results["Positive"]:
                st.markdown(f"✅ {headline}")
        
        with sentiment_cols[1]:
            st.markdown("### Neutral")
            for headline in st.session_state.sentiment_results["Neutral"]:
                st.markdown(f"➖ {headline}")
        
        with sentiment_cols[2]:
            st.markdown("### Negative")
            for headline in st.session_state.sentiment_results["Negative"]:
                st.markdown(f"❌ {headline}")
        
        # Calculate sentiment distribution
        total_headlines = sum(len(headlines) for headlines in st.session_state.sentiment_results.values())
        
        if total_headlines > 0:
            st.markdown("### Sentiment Distribution")
            dist_cols = st.columns(3)
            
            for i, (sentiment, headlines) in enumerate(st.session_state.sentiment_results.items()):
                dist_cols[i].metric(
                    label=sentiment, 
                    value=f"{len(headlines)} headlines",
                )
            
            # Continue to stats analysis
            if st.button("Proceed to Performance Stats"):
                st.session_state.current_step = 4
                st.rerun()
    
    # Player statistics section
    if st.session_state.current_step >= 4:
        st.markdown("---")
        st.subheader("Player Performance Statistics")
        
        if st.session_state.player_stats is None:
            df = load_match_data()
            if not df.empty:
                with st.spinner(f"Retrieving statistics for {player_name} at {tournament} {year}..."):
                    player_matches, tournament_stats = get_player_tournament_stats(df, player_name, tournament, year)
                    yearly_stats = get_player_yearly_stats(df, player_name, year)
                    st.session_state.player_stats = {
                        "player_matches": player_matches,
                        "tournament_stats": tournament_stats,
                        "yearly_stats": yearly_stats
                    }
        
        if st.session_state.player_stats is not None:
            player_matches = st.session_state.player_stats["player_matches"]
            tournament_stats = st.session_state.player_stats["tournament_stats"]
            yearly_stats = st.session_state.player_stats["yearly_stats"]
            
            # Create two-column layout for side-by-side comparison
            stat_cols = st.columns([1, 1], gap="large")
            
            # Tournament Performance Column
            with stat_cols[0]:
                st.markdown(f"### {player_name}'s Performance at {tournament} {year}")
                
                # Handle case of no tournament matches
                if player_matches is None:
                    st.warning(f"No matches found for {player_name} at {tournament} {year}.")
                else:
                    # Display tournament overview metrics
                    tournament_overview_cols = st.columns(3)
                    tournament_overview = {
                        "Total Matches": tournament_stats["Total Matches"],
                        "Wins": tournament_stats["Wins"],
                        "Win Rate": f"{tournament_stats['Win Rate']:.1f}%"
                    }
                    
                    # Populate overview metrics
                    for i, (metric, value) in enumerate(tournament_overview.items()):
                        tournament_overview_cols[i].metric(metric, value)
                    
                    # Detailed tournament metrics
                    st.markdown("#### Detailed Tournament Metrics")
                    tournament_detailed_metrics = {
                        "Match Duration": f"{tournament_stats['Avg Match Duration']:.1f} mins",
                        "Aces": f"{tournament_stats['Tournament Aces']:.1f}",
                        "Double Faults": f"{tournament_stats['Tournament Double Faults']:.1f}",
                        "Break Points Saved": f"{tournament_stats['Break Points Saved Percentage']:.1f}%"
                    }
                    
                    # Create 2x2 grid for detailed metrics
                    metrics_grid = st.columns(2)
                    for i, (metric, value) in enumerate(tournament_detailed_metrics.items()):
                        metrics_grid[i % 2].metric(metric, value)
                    
                    # Tournament matches dataframe
                    st.markdown("#### Tournament Matches")
                    display_columns = [
                        "Tournament", "Round", "Surface", 
                        "Winner", "Loser", "Score"
                    ]
                    
                    # Rename columns for better readability
                    tournament_matches = player_matches.rename(columns={
                        "tourney_name": "Tournament",
                        "round": "Round",
                        "surface": "Surface",
                        "winner_name": "Winner",
                        "loser_name": "Loser",
                        "score": "Score"
                    })
                    
                    # Display matches
                    st.dataframe(tournament_matches[display_columns], use_container_width=True)
            
            # Yearly Performance Column
            with stat_cols[1]:
                st.markdown(f"### {player_name}'s Performance in {year}")
                
                # Handle case of no yearly matches
                if yearly_stats is None:
                    st.warning(f"No matches found for {player_name} in {year}.")
                else:
                    # Display yearly overview metrics
                    yearly_overview_cols = st.columns(3)
                    yearly_overview = {
                        "Total Matches": yearly_stats["Total Matches"],
                        "Wins": yearly_stats["Wins"],
                        "Win Rate": f"{yearly_stats['Win Rate']:.1f}%"
                    }
                    
                    # Populate overview metrics
                    for i, (metric, value) in enumerate(yearly_overview.items()):
                        yearly_overview_cols[i].metric(metric, value)
                    
                    # Detailed yearly metrics
                    st.markdown("#### Detailed Yearly Metrics")
                    yearly_detailed_metrics = {
                        "Match Duration": f"{yearly_stats['Avg Match Duration']:.1f} mins",
                        "Aces": f"{yearly_stats['Yearly Aces']:.1f}",
                        "Double Faults": f"{yearly_stats['Yearly Double Faults']:.1f}",
                        "Break Points Saved": f"{yearly_stats['Break Points Saved Percentage']:.1f}%"
                    }
                    
                    # Create 2x2 grid for detailed metrics
                    yearly_metrics_grid = st.columns(2)
                    for i, (metric, value) in enumerate(yearly_detailed_metrics.items()):
                        yearly_metrics_grid[i % 2].metric(metric, value)
            
            # Integrated analysis section
            st.markdown("---")
            st.markdown("### Media Sentiment vs. Performance Correlation")
            
            # Get sentiment distribution
            positive_count = len(st.session_state.sentiment_results["Positive"])
            neutral_count = len(st.session_state.sentiment_results["Neutral"]) 
            negative_count = len(st.session_state.sentiment_results["Negative"])
            total_headlines = positive_count + neutral_count + negative_count
            
            if total_headlines > 0 and player_matches is not None:
                
                correlation_cols = st.columns(2)
                
                with correlation_cols[0]:
                    st.markdown("#### Media Sentiment Overview")
                
                with correlation_cols[1]:
                    st.markdown("#### Performance Overview")

if __name__ == "__main__":
    main()