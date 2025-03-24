import pandas as pd
import streamlit as st

#############################
# STATS RETRIEVAL FUNCTIONS
#############################

def load_match_data(year):
    try:
        # Takes in specific year to load up
        file_path = f"C:/Users/tobyl/OneDrive/Documents/4th Year/Dissertation/Repository/Statistics/atp_matches_{year}.csv"
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"ATP {year} match data file not found. Please ensure the CSV is in the correct directory.")
        return pd.DataFrame()

def get_player_tournament_stats(df, player_name, tournament):
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
    
    # Determine player's seed in the tournament
    seed = None
    # USing iloc to select the first row of player winner matches
    if not player_winner_matches.empty and not pd.isna(player_winner_matches["winner_seed"].iloc[0]):
        seed = player_winner_matches["winner_seed"].iloc[0]
    elif not player_loser_matches.empty and not pd.isna(player_loser_matches["loser_seed"].iloc[0]):
        seed = player_loser_matches["loser_seed"].iloc[0]

    # If no seed is retrieved from the dataset then mark seed as 0
    if seed is None:
        seed = 0
    # Determine the furthest round reached by the player
    round_order = {
        "R128": 1, "R64": 2, "R32": 3, "R16": 4,
        "QF": 5, "SF": 6, "F": 7, "W": 8
    }

    # Initialise with the lowest round
    furthest_round = "R128"
    furthest_round_value = 1

    # Special check for tournament winner (reached W)
    if not player_winner_matches.empty and "F" in player_winner_matches["round"].values:
        furthest_round = "W"
        furthest_round_value = round_order["W"]
    # Otherwise, check for runner-up
    elif not player_loser_matches.empty and "F" in player_loser_matches["round"].values:
        furthest_round = "F"
        furthest_round_value = round_order["F"]
    else:
        # Check regular rounds for winners
        if not player_winner_matches.empty:
            for round_name in player_winner_matches["round"].unique():
                if round_order.get(round_name, 0) > furthest_round_value:
                    furthest_round = round_name
                    furthest_round_value = round_order.get(round_name, 0)
        
        # Check regular rounds for losers
        if not player_loser_matches.empty:
            for round_name in player_loser_matches["round"].unique():
                if round_order.get(round_name, 0) > furthest_round_value:
                    furthest_round = round_name
                    furthest_round_value = round_order.get(round_name, 0)

    print("Debugging furthest round", furthest_round)
    # Compute tournament-specific statistics
    tournament_stats = {
        "Total Matches": len(player_matches),
        "Wins": len(player_winner_matches),
        "Losses": len(player_loser_matches),
        "Win Rate": len(player_winner_matches) / len(player_matches) * 100,
        "Avg Match Duration": player_matches["minutes"].mean(),
        "Seed": seed,
        "Round Reached": furthest_round,
        
        # Both matches where teh selcted player won and lost are retrieved
        "Tournament Aces": player_matches[
            player_matches["winner_name"] == player_name]["w_ace"].mean() 
            if not player_winner_matches.empty 
            else player_matches[player_matches["loser_name"] == player_name]["l_ace"].mean(),
        
        "Tournament Double Faults": player_matches[
            player_matches["winner_name"] == player_name]["w_df"].mean()
            if not player_winner_matches.empty 
            else player_matches[player_matches["loser_name"] == player_name]["l_df"].mean(),
        
        "Break Points Faced": player_matches[
            player_matches["winner_name"] == player_name]["w_bpFaced"].mean() 
            if not player_winner_matches.empty 
            else player_matches[player_matches["loser_name"] == player_name]["l_bpFaced"].mean(),
        
        # Calculated by dividing amount of break points saved by amount of break points faced
        "Break Points Saved Percentage": (
            (player_matches[player_matches["winner_name"] == player_name]["w_bpSaved"].mean() 
            / player_matches[player_matches["winner_name"] == player_name]["w_bpFaced"].mean() * 100) 
            if not player_winner_matches.empty 
            else (player_matches[player_matches["loser_name"] == player_name]["l_bpSaved"].mean()
            / player_matches[player_matches["loser_name"] == player_name]["l_bpFaced"].mean() * 100)
        )
    }

    return player_matches, tournament_stats

def get_player_yearly_stats(df, player_name):
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
            player_matches["winner_name"] == player_name]["w_ace"].mean() 
            if not player_winner_matches.empty 
            else player_matches[player_matches["loser_name"] == player_name]["l_ace"].mean(),
        
        "Yearly Double Faults": player_matches[
            player_matches["winner_name"] == player_name]["w_df"].mean() 
            if not player_winner_matches.empty 
            else player_matches[player_matches["loser_name"] == player_name]["l_df"].mean(),
        
        "Break Points Faced": player_matches[
            player_matches["winner_name"] == player_name]["w_bpFaced"].mean()
            if not player_winner_matches.empty 
            else player_matches[player_matches["loser_name"] == player_name]["l_bpFaced"].mean(),
        
        "Break Points Saved Percentage": (
            (player_matches[player_matches["winner_name"] == player_name]["w_bpSaved"].mean()
            / player_matches[player_matches["winner_name"] == player_name]["w_bpFaced"].mean() * 100) 
            if not player_winner_matches.empty 
            else (player_matches[player_matches["loser_name"] == player_name]["l_bpSaved"].mean() 
            / player_matches[player_matches["loser_name"] == player_name]["l_bpFaced"].mean() * 100)
        )
    }

    return yearly_stats

############################
#TOURNAMENT AVERAGES COMPARISON
#############################
def calculate_tour_averages(df, tournament):

    # Filter matches for the specific tournament
    tournament_matches = df[df["tourney_name"].str.contains(tournament, case=False, na=False)]
    
    if tournament_matches.empty:
        return {}
    
    # Calculate averages for winners
    winners_aces = tournament_matches["w_ace"].mean()
    winners_double_faults = tournament_matches["w_df"].mean()
    winners_bp_faced = tournament_matches["w_bpFaced"].mean()
    winners_bp_saved = tournament_matches["w_bpSaved"].mean()
    
    # Calculate averages for losers
    losers_aces = tournament_matches["l_ace"].mean()
    losers_double_faults = tournament_matches["l_df"].mean()
    losers_bp_faced = tournament_matches["l_bpFaced"].mean()
    losers_bp_saved = tournament_matches["l_bpSaved"].mean()
    
    # Calculate overall tour averages
    tour_averages = {
        "aces": (winners_aces + losers_aces) / 2,
        "double_faults": (winners_double_faults + losers_double_faults) / 2,
        "break_points_faced": (winners_bp_faced + losers_bp_faced) / 2,
        "break_points_saved": (winners_bp_saved + losers_bp_saved) / 2,
        "break_points_saved_pct": (
            (winners_bp_saved / winners_bp_faced * 100 if winners_bp_faced > 0 else 0) + 
            (losers_bp_saved / losers_bp_faced * 100 if losers_bp_faced > 0 else 0)
        ) / 2
    }
    
    return tour_averages

