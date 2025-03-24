import streamlit as st
import pandas as pd
from WebscrapingFunc import scrape_bbc_sport, load_ignored_headlines, save_ignored_headlines
from SentimentModel import analyse_headlines_sentiment
from DataRetrievalFunc import load_match_data, get_player_tournament_stats, get_player_yearly_stats, calculate_tour_averages
from BiasDetection import display_bias_analysis


# Configure page
st.set_page_config(layout="wide", page_title="Tennis Analysis Dashboard")

# Initialise session state
if 'scraped_headlines' not in st.session_state:
    st.session_state.scraped_headlines = None
if 'sentiment_results' not in st.session_state:
    st.session_state.sentiment_results = {"Positive": [], "Neutral": [], "Negative": []}
if 'player_stats' not in st.session_state:
    st.session_state.player_stats = None
if 'current_step' not in st.session_state:
    # 1: Inputting parameters, 2: Scraping, 3: Sentiment Analysis, 4: Stats Retrieval
    st.session_state.current_step = 1  

#############################
# MAIN APPLICATION UI
#############################

def main():
    st.title("🎾 Tennis Media & Performance Analysis")
    
    # Create progress indicator for the workflow
    progress_cols = st.columns(4)
    with progress_cols[0]:
        # Ticks are used to display progress
        # Hourglasses are used if the step is being processed
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
    # 4 columns are used for the 4 parameters required
    param_cols = st.columns(4)
    
    with param_cols[0]:
        # Will add more later but currently have data for 2018 to 2024
        year = st.selectbox("Select Year:", list(range(2018, 2025)))

    with param_cols[1]:
        # Load match data to get player list for selection
        # This way dropdown only allows selection of players who there is data on 
        df = load_match_data(year)
        if not df.empty:
            # Filter to only include Grand Slam tournaments
            # G is the code for grand slam tournament
            grand_slam_df = df[df['tourney_level'] == 'G']  
        
            # Get only players who played in Grand Slams
            gs_players = sorted(set(grand_slam_df["winner_name"].unique()) | set(grand_slam_df["loser_name"].unique()))
        
            player_name = st.selectbox("Select Player:", gs_players)
        else:
            # If there is no data for player names manual entry is allowed
            # This should never happen 
            player_name = st.text_input("Enter Player Name:")
    
    with param_cols[2]:
        # Select specific tournament, currently limited to grand slams
        tournament = st.selectbox("Enter Tournament Name:", ['Wimbledon','US Open', 'Australian Open', 'French Open'])
        # Conversion to match names within stats files
        if tournament == "French Open":
            tournament = 'Roland Garros'
        if tournament == "US Open":
            tournament = 'Us Open'
    
    with param_cols[3]:
        # Can select between 1 and 5 pages 
        max_pages = st.slider("Pages to Scrape:", 1, 5, 3)
    
    # Button to start webscraping based on selected parameters
    if st.button("Start Analysis"):
        # Move to scraping step
        # All session state data is reset
        st.session_state.current_step = 2  
        st.session_state.scraped_headlines = None
        st.session_state.sentiment_results = {"Positive": [], "Neutral": [], "Negative": []}
        st.session_state.player_stats = None
        # App is rerun to purge previous processes
        st.rerun()
    
    st.markdown("---")
    
    # Web scraping section 
    if st.session_state.current_step >= 2:
        st.subheader("Headline Scraping")
        # Previously ignored headlines are loaded to avoid rescraping them
        ignored_headlines = load_ignored_headlines()
        if st.session_state.scraped_headlines is None:
            # Spinner shown while scraping occurs
            with st.spinner(f"Scraping headlines for {player_name} at {tournament} {year}..."):
                # Data frame of scraped results are stored in session state
                scraped_df = scrape_bbc_sport(player_name, tournament, year, max_pages, ignored_headlines)
                st.session_state.scraped_headlines = scraped_df
        
        if not st.session_state.scraped_headlines.empty:
            st.success(f"Found {len(st.session_state.scraped_headlines)} relevant headlines")
            
            # Show headlines in an expander as unsure how many headlines are returned
            with st.expander("View Scraped Headlines", expanded=True):
                # Each headline is looped through and are added to a column with an ignore button next to each one
                for i, row in st.session_state.scraped_headlines.iterrows():
                    col1, col2 = st.columns([4, 1])
                    headline = row["Headline"]
                    url = row["URL"]
                    
                    with col1:
                        # If url has been scraped along with headline, make the headline a link
                        if url:
                            st.markdown(f"[{headline}]({url})")
                        else:
                            st.write(headline)
                    
                    with col2:
                        if st.button(f"Ignore", key=f"ignore_{i}"):
                            # Add to ignored headlines if click to ignore a headline
                            # Tjere are then added to ignored headlines csv
                            ignored_headlines.add(headline)
                            save_ignored_headlines([headline])
                            st.success(f"Marked '{headline}' as irrelevant")
                            
                            # Remove from current results and refresh the app
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
                # Sentiment analysis function ran and session state stores the results
                sentiment_results, updated_headlines = analyse_headlines_sentiment(st.session_state.scraped_headlines)
                st.session_state.sentiment_results = sentiment_results
                st.session_state.scraped_headlines = updated_headlines
        
        # Display results in three columns, positive (tick), neutral (dash), negative (cross)
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
            
            # Show count of positive neutral and negative headlines in 3 columns
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
        
        # Retrieve stats if not already done
        if st.session_state.player_stats is None:
            df = load_match_data(year)
            if not df.empty:
                with st.spinner(f"Retrieving statistics for {player_name} at {tournament} {year}..."):
                    player_matches, tournament_stats = get_player_tournament_stats(df, player_name, tournament)
                    yearly_stats = get_player_yearly_stats(df, player_name)
                    # All stats are stored in session state
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
            
            
            # Bias decision section
            st.markdown("---")
            st.markdown("### Media Sentiment vs. Player Performance")

            # Get sentiment distribution
            positive_count = len(st.session_state.sentiment_results["Positive"])
            neutral_count = len(st.session_state.sentiment_results["Neutral"]) 
            negative_count = len(st.session_state.sentiment_results["Negative"])
            total_headlines = positive_count + neutral_count + negative_count
            
            if total_headlines > 0 and player_matches is not None:
                
                # Get tour averages for bias detection
                tour_averages = calculate_tour_averages(df, tournament)
        
                if tour_averages:
                    # Display bias analysis
                        display_bias_analysis(
                            tournament_stats,
                            tour_averages,
                            st.session_state.sentiment_results,
                            player_name,
                            tournament,
                            year
                        )
                else:
                    st.warning(f"Cannot perform bias analysis: Tour averages not available for {tournament} {year}.")
            else:
                if total_headlines == 0:
                    st.warning("No headlines found for sentiment analysis. Cannot perform bias detection.")
                if player_matches is None or tournament_stats is None:
                    st.warning(f"No performance data available for {player_name} at {tournament} {year}. Cannot perform bias detection.")

if __name__ == "__main__":
    main()