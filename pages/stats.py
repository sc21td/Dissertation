import streamlit as st
import pandas as pd
import numpy as np

def load_match_data():
    """
    Load ATP match data and catch error in case not csv not found.
    """
    try:
        return pd.read_csv("atp_matches_2024.csv")
    except FileNotFoundError:
        st.error("ATP 2024 match data file not found. Please ensure the CSV is in the correct directory.")
        return pd.DataFrame()

def get_player_tournament_stats(df, player_name, tournament, year):
    """
    Retrieve and analyse player's tournament and overall performance.
    """
    # Get player's matches in the specific tournament
    # Retrieve all matches regardless if player won or lost
    # Case insensitive so Wimbledone will match wimbledon
    player_winner_matches = df[
        (df["winner_name"] == player_name) & 
        (df["tourney_name"].str.contains(tournament, case=False, na=False))
    ]
    
    player_loser_matches = df[
        (df["loser_name"] == player_name) & 
        (df["tourney_name"].str.contains(tournament, case=False, na=False))
    ]

    # Combine winner and loser matches
    player_matches = pd.concat([player_winner_matches, player_loser_matches])

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

def main():
    st.title("🎾 Player Statistics & Match Analysis")

    # Load data
    df = load_match_data()
    if df.empty:
        return

    # Player selection currently displays all players available in dataset
    all_players = sorted(set(df["winner_name"].unique()) | set(df["loser_name"].unique()))
    player_name = st.selectbox("Choose a Player:", all_players)
    tournament = st.text_input("Enter Tournament Name (e.g., Wimbledon)")
    # Currently only year I have downloaded
    year = 2024

    if st.button("Analyse Player Performance"):
        player_matches, tournament_stats = get_player_tournament_stats(df, player_name, tournament, year)

        if player_matches is None:
            st.warning(f"No matches found for {player_name} at {tournament} {year}.")
        else:
            # Display tournament performance
            st.subheader(f"{player_name}'s Performance at {tournament} {year}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Matches", tournament_stats["Total Matches"])
            with col2:
                st.metric("Wins", tournament_stats["Wins"])
            with col3:
                st.metric("Win Rate", f"{tournament_stats['Win Rate']:.1f}%")

            # Performance Metrics
            st.subheader("Performance Metrics")
            metrics_cols = st.columns(3)
            metrics = {
                "Avg Match Duration": f"{tournament_stats['Avg Match Duration']:.1f} mins",
                "Avg Aces": f"{tournament_stats['Tournament Aces']:.1f}",
                "Avg Double Faults": f"{tournament_stats['Tournament Double Faults']:.1f}",
                "Break Points Saved": f"{tournament_stats['Break Points Saved Percentage']:.1f}%"
            }

            for i, (metric, value) in enumerate(metrics.items()):
                metrics_cols[i].metric(metric, value)

            # Display Recent Matches
            st.subheader("Recent Tournament Matches")
            # Prepare match details for display
            display_columns = [
                "Tournament", "Round", "Surface", 
                "Winner", "Loser", "Score"
            ]

            tournament_matches = player_matches.rename(columns={
                "tourney_name": "Tournament",
                "round": "Round",
                "surface": "Surface",
                "winner_name": "Winner",
                "loser_name": "Loser",
                "score": "Score"
            })
            
            st.dataframe(tournament_matches[display_columns])

# This ensures the page can be run directly
if __name__ == "__main__":
    main()