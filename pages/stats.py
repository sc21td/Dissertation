import streamlit as st  
import pandas as pd    
import numpy as np     

def load_match_data():
    """
    Load ATP match data from a CSV file with error handling.
    
    Returns:
    - DataFrame containing match data if successful
    - Empty DataFrame if file not found
    
    Key Considerations:
    - Uses try-except to handle potential file loading errors
    - Displays a user-friendly error message if file is missing
    - Ensures application doesn't crash due to file loading issues
    """
    try:
        # Attempt to read the CSV file containing ATP match data
        return pd.read_csv("atp_matches_2024.csv")
    except FileNotFoundError:
        # Display an error message if the file is not found
        st.error("ATP 2024 match data file not found. Please ensure the CSV is in the correct directory.")
        # Return an empty DataFrame to prevent application crash
        return pd.DataFrame() 

def get_player_tournament_stats(df, player_name, tournament, year):
    """
    Analyse a player's performance in a specific tournament.
    
    Args:
    - df: DataFrame containing match data
    - player_name: Name of the player to analyse
    - tournament: Name of the tournament
    - year: Year of the tournament
    
    Returns:
    - Tuple containing:
      1. Player's matches in the tournament
      2. Detailed tournament performance statistics
    
    Key Features:
    - Handles matches where player is winner or loser
    - Calculates comprehensive tournament-specific metrics
    - Uses case-insensitive tournament name matching
    """
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

    # Compute comprehensive tournament-specific statistics
    tournament_stats = {
        # Basic match statistics
        # Total number of matches
        "Total Matches": len(player_matches),
        # Number of wins  
        "Wins": len(player_winner_matches),  
        # Number of losses  
        "Losses": len(player_loser_matches),   
        # Win percentage
        "Win Rate": len(player_winner_matches) / len(player_matches) * 100,  

        # Performance metrics
        # Average match length
        "Avg Match Duration": player_matches["minutes"].mean(),  
        
        # Aces calculation with fallback logic
        "Tournament Aces": player_matches[
            player_matches["winner_name"] == player_name
        ]["w_ace"].mean() if not player_winner_matches.empty else player_matches[
            player_matches["loser_name"] == player_name
        ]["l_ace"].mean(),
        
        # Double faults calculation with fallback logic
        "Tournament Double Faults": player_matches[
            player_matches["winner_name"] == player_name
        ]["w_df"].mean() if not player_winner_matches.empty else player_matches[
            player_matches["loser_name"] == player_name
        ]["l_df"].mean(),
        
        # Break points faced calculation
        "Break Points Faced": player_matches[
            player_matches["winner_name"] == player_name
        ]["w_bpFaced"].mean() if not player_winner_matches.empty else player_matches[
            player_matches["loser_name"] == player_name
        ]["l_bpFaced"].mean(),
        
        # Break points saved percentage calculation
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
    """
    Analyse a player's overall performance for the entire year.
    
    Similar structure to tournament-specific stats, but calculates
    metrics across all matches in the year.
    
    Args:
    - df: DataFrame containing match data
    - player_name: Name of the player to analyse
    - year: Year to analyse
    
    Returns:
    - Dictionary of yearly performance statistics
    """
    # Filter matches where player is winner
    player_winner_matches = df[df["winner_name"] == player_name]
    # Filter matches where player is loser
    player_loser_matches = df[df["loser_name"] == player_name]

    # Combine winner and loser matches
    player_matches = pd.concat([player_winner_matches, player_loser_matches])

    # Return None if no matches found
    if player_matches.empty:
        return None

    # Compute comprehensive yearly statistics
    # (Logic is nearly identical to tournament stats, but applied to all matches)
    yearly_stats = {
        "Total Matches": len(player_matches),
        "Wins": len(player_winner_matches),
        "Losses": len(player_loser_matches),
        "Win Rate": len(player_winner_matches) / len(player_matches) * 100,
        "Avg Match Duration": player_matches["minutes"].mean(),
        
        # Metrics calculation with winner/loser fallback
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

def main():
    """
    Main application function that:
    - Configures Streamlit page layout
    - Loads match data
    - Provides user interface for player statistics
    - Displays comparative performance analysis
    
    Key UI Components:
    - Player selection dropdown
    - Tournament name input
    - Performance analysis button
    - Side-by-side performance metrics display
    
    Design Considerations:
    - Wide layout for better information display
    - Responsive column design
    - Error handling for missing data
    """
    # Set page to wide layout for maximum information display
    st.set_page_config(layout="wide")
    
    # Application title
    st.title("🎾 Player Statistics & Match Analysis")

    # Load match data
    df = load_match_data()
    if df.empty:
        # Exit if no data loaded
        return  

    # Compile list of unique players from winner and loser columns
    all_players = sorted(set(df["winner_name"].unique()) | set(df["loser_name"].unique()))
    
    # User input section
    player_name = st.selectbox("Choose a Player:", all_players)
    tournament = st.text_input("Enter Tournament Name (e.g., Wimbledon)")
    
    # Currently fixed to 2024
    year = 2024

    # Performance analysis trigger
    if st.button("Analyse Player Performance"):
        # Retrieve tournament-specific performance
        player_matches, tournament_stats = get_player_tournament_stats(df, player_name, tournament, year)
        
        # Retrieve yearly performance
        yearly_stats = get_player_yearly_stats(df, player_name, year)

        # Create two-column layout for side-by-side comparison
        col1, col2 = st.columns([1, 1], gap="large")

        # Tournament Performance Column
        with col1:
            st.subheader(f"{player_name}'s Performance at {tournament} {year}")
            
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
                st.subheader("Detailed Tournament Metrics")
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
                st.subheader("Tournament Matches")
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
                
                # Display matches, using full container width
                st.dataframe(tournament_matches[display_columns], use_container_width=True)

        # Yearly Performance Column
        with col2:
            st.subheader(f"{player_name}'s Performance in {year}")
            
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
                st.subheader("Detailed Yearly Metrics")
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

if __name__ == "__main__":
    main()