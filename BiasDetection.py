import math
import pandas as pd
import streamlit as st

#############################
# BIAS DETECTION #
#############################

def bias_detection(tournament_stats, tour_averages, sentiment_results):
   
    # Step 1: Calculate performance score based on comparison with tour averages
    # Performance score also takes into account how far player progressed in tournament
    performance_points = 0
    performance_factors = []
    
    # Aces comparison
    player_aces = tournament_stats.get("Tournament Aces", 0)
    if player_aces > tour_averages["aces"]:
        performance_points += 1
        performance_factors.append({"metric": "Aces", "value": player_aces, 
                                   "tour_avg": tour_averages["aces"], "score": 1})
    else:
        performance_points -= 1
        performance_factors.append({"metric": "Aces", "value": player_aces, 
                                   "tour_avg": tour_averages["aces"], "score": -1})
    
    # Double faults comparison 
    player_dfs = tournament_stats.get("Tournament Double Faults", 0)
    if player_dfs < tour_averages["double_faults"]:
        performance_points += 1
        performance_factors.append({"metric": "Double Faults", "value": player_dfs, 
                                   "tour_avg": tour_averages["double_faults"], "score": 1})
    else:
        performance_points -= 1
        performance_factors.append({"metric": "Double Faults", "value": player_dfs, 
                                   "tour_avg": tour_averages["double_faults"], "score": -1})
    
    # Break points saved percentage
    player_bp_saved_pct = tournament_stats.get("Break Points Saved Percentage", 0)
    if player_bp_saved_pct > tour_averages["break_points_saved_pct"]:
        performance_points += 1
        performance_factors.append({"metric": "Break Points Saved %", "value": player_bp_saved_pct, 
                                   "tour_avg": tour_averages["break_points_saved_pct"], "score": 1})
    else:
        performance_points -= 1
        performance_factors.append({"metric": "Break Points Saved %", "value": player_bp_saved_pct, 
                                   "tour_avg": tour_averages["break_points_saved_pct"], "score": -1})
        
    # Progression in tournament compared to seed
    player_seed = tournament_stats.get("Seed", None)
    print("Debugging: Player seed is:", player_seed)
    tournament_round = tournament_stats.get("Round Reached", None)

    # Only evaluate if theres is both seed and round information
    if player_seed is not None and tournament_round is not None:
        # Convert tournament round to a numeric value
        print("DEBUGGING: converting tournament round to numbers")
        round_values = {
            "R128": 1, "R64": 2, "R32": 3, "R16": 4,
            "QF": 5, "SF": 6, "F": 7, "W": 8
        }
        
        round_numeric = round_values.get(tournament_round, 0)
        
        # Calculate expected round based on seed
        # log2(seed) gives roughly the round a player should reach
        # E.g., seed 2 should reach finals (round 7)
        # Log2(2) = 1 , expected round = 8-1 = 7
        # Therefore expected round is 7 or finals
        if player_seed > 0:
            print("Debugging: Player seed is above 0")
            expected_round = max(1, 8 - math.floor(math.log2(player_seed)))
        else:
            # Unseeded players (below 32 seed, qualifiers, wildcards)
            # Expected to reach R64
            # Could change to lose first round?
            print("Debugging: Player is unseeded")
            expected_round = 2  
        
        # Compare actual vs expected performance
        if round_numeric >= expected_round:
            print("Debugging: Player exceeded their expected round")
            performance_points += 1
            performance_factors.append({"metric": "Seed Performance", "value": f"Seed {player_seed} reached {tournament_round}", 
                                "tour_avg": f"Expected round {expected_round}", "score": 1})
        elif round_numeric == expected_round:
            print("Debugging: Player reached their expected round")
            performance_points += 0.5
            performance_factors.append({"metric": "Seed Performance", "value": f"Seed {player_seed} reached {tournament_round}", 
                                "tour_avg": f"Expected round {expected_round}", "score": 1})
        else:
            print("Player did not reach their expected round")
            performance_points -= 1
            performance_factors.append({"metric": "Seed Performance", "value": f"Seed {player_seed} reached {tournament_round}", 
                                "tour_avg": f"Expected round {expected_round}", "score": -1})

    # Normalise performance score between -1 and 1
    # 4 metrics to rank players off
    max_points = 4 
    #max_points = 3 
    normalised_performance_score = performance_points / max_points
    
    # Step 2: Calculate sentiment score as difference of positive sum and negative sum over sum of headlines
    positive_count = len(sentiment_results["Positive"])
    negative_count = len(sentiment_results["Negative"])
    total_sentiment = positive_count + negative_count
    
    if total_sentiment > 0:
        sentiment_score = (positive_count - negative_count) / total_sentiment
    else:
        sentiment_score = 0
    
    # Step 3: Detect bias by comparing performance and sentiment scores
    bias_score = sentiment_score - normalised_performance_score
    bias_magnitude = abs(bias_score)
    
    # Determine bias level based on magnitude
    if bias_magnitude < 0.3:
        bias_level = "Low"
        bias_description = "Media sentiment generally aligns with player performance."
    elif bias_magnitude < 0.7:
        bias_level = "Moderate"
        if bias_score > 0:
            bias_description = "Media sentiment is somewhat more positive than performance suggests."
        else:
            bias_description = "Media sentiment is somewhat more negative than performance suggests."
    else:
        bias_level = "High"
        if bias_score > 0:
            bias_description = "Media sentiment is significantly more positive than performance suggests."
        else:
            bias_description = "Media sentiment is significantly more negative than performance suggests."
    
    # Prepare sentiment details for each headline
    sentiment_details = []
    
    # Add positive headlines
    for headline in sentiment_results["Positive"]:
        # Extract actual headline text from format "Headline text (XX.XX% confidence)"
        headline_text = headline.split(" (")[0]
        # agrees_with_stats = "Yes" if normalised_performance_score > 0 else "No"
        sentiment_details.append({
            "Headline": headline_text,
            "Sentiment": "Positive",
            # "Agrees with Stats": agrees_with_stats
        })
    
    # Add negative headlines
    for headline in sentiment_results["Negative"]:
        headline_text = headline.split(" (")[0]
        # agrees_with_stats = "Yes" if normalised_performance_score < 0 else "No"
        sentiment_details.append({
            "Headline": headline_text,
            "Sentiment": "Negative",
            # "Agrees with Stats": agrees_with_stats
        })
    
    return {
        "performance_score": normalised_performance_score,
        "performance_factors": performance_factors,
        "sentiment_score": sentiment_score,
        "bias_score": bias_score,
        "bias_level": bias_level,
        "bias_description": bias_description,
        "sentiment_details": sentiment_details
    }

def display_bias_analysis(tournament_stats, tour_averages, sentiment_results, player_name, tournament, year):
    
    # Run bias detection algorithm
    bias_results = bias_detection(tournament_stats, tour_averages, sentiment_results)
    
    # Create tabs for different sections of the analysis
    bias_tabs = st.tabs(["How It Works", "Performance Score", "Sentiment Analysis", "Bias Assessment"])
    
    # Tab 1: How the Algorithm Works
    with bias_tabs[0]:
        st.markdown("### How the Bias Detection Algorithm Works")
        st.markdown("""
        The bias detection algorithm works by comparing player performance metrics with tour averages 
        and then contrasting this with media sentiment. Here's how it's calculated:
        
        **Performance Scoring:**
        - Player's aces > tour average: +1 point
        - Player's aces < tour average: -1 point
        - Player's double faults < tour average: +1 point
        - Player's double faults > tour average: -1 point
        - Player's break points saved % > tour average: +1 point
        - Player's break points saved % < tour average: -1 point
                    
        The players seed going into the tournament along with the round they reached is also taken into account. 
        For example if an unseeded player makes it into the final this is more impressive than if the 1st seed won the tournament.
        If the performance:
                    - Exceeds the expected round reached: +1 point
                    - Matches the expected round reached: +0.5 points
                    - Is worse than the expected round reached: -1 point
                    
        The total performance score is normalised to a scale from -1 (significantly below average) 
        to +1 (significantly above average), with 0 representing average performance.
        
        **Sentiment Scoring:**
        - Calculated as: (Positive headlines - Negative headlines) / Total headlines
        - Ranges from -1 (all negative) to +1 (all positive)
        
        **Bias Assessment:**
        - Bias score = Sentiment score - Performance score
        - A large positive score indicates generic media is more positive than performance warrants
        - A large negative score indicates generic media is more negative than performance warrants
        - Scores near zero suggest generic media sentiment aligns with player performance
        """)
    
    # Tab 2: Performance Score
    with bias_tabs[1]:
        st.markdown("### Player Performance Analysis")
        
        # Display normalised performance score
        perf_score = bias_results["performance_score"]
        perf_color = "green" if perf_score > 0 else "red" if perf_score < 0 else "gray"
        st.markdown(f"#### Overall Performance Score: <span style='color:{perf_color}'>{perf_score:.2f}</span>", unsafe_allow_html=True)
        
        if perf_score > 0.3:
            st.markdown(f"✅ {player_name}'s performance at {tournament} {year} was **above average** compared to tour standards.")
        elif perf_score < -0.3:
            st.markdown(f"❌ {player_name}'s performance at {tournament} {year} was **below average** compared to tour standards.")
        else:
            st.markdown(f"➖ {player_name}'s performance at {tournament} {year} was **about average** compared to tour standards.")
        
        # SEED COMPARISON to performance
        # Add seed performance insight
        for factor in bias_results["performance_factors"]:
            if factor["metric"] == "Seed Performance":
                if factor["score"] > 0:
                    st.markdown(f"🔼 Based on their seed, {player_name} **progressed further** than expected in the tournament.")
                else:
                    st.markdown(f"🔽 Based on their seed, {player_name} **progressed less far** than expected in the tournament.")
        
        # Display performance factors in a table
        st.markdown("#### Performance Metrics Breakdown")
        performance_data = {
            "Metric": [],
            f"{player_name}": [],
            "Tour Average": [],
            "Score": []
        }
        
        for factor in bias_results["performance_factors"]:
            performance_data["Metric"].append(factor["metric"])
           
           # For the player's value
           # Check if value is number/float befor applying float formatting
            if isinstance(factor['value'], (int, float)):
                performance_data[f"{player_name}"].append(f"{factor['value']:.1f}")
            else:
                performance_data[f"{player_name}"].append(f"{factor['value']}")

            # For the tour average
            if isinstance(factor['tour_avg'], (int, float)):
                performance_data["Tour Average"].append(f"{factor['tour_avg']:.1f}")
            else:
                performance_data["Tour Average"].append(f"{factor['tour_avg']}")
                        
            score_text = "+1" if factor["score"] > 0 else "-1"
            score_color = "green" if factor["score"] > 0 else "red"
            performance_data["Score"].append(f"<span style='color:{score_color}'>{score_text}</span>")
        
        # Create a DataFrame for display
        perf_df = pd.DataFrame(performance_data)
        
        # Display with HTML formatting for score column
        st.write(perf_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # Tab 3: Sentiment Analysis
    with bias_tabs[2]:
        st.markdown("### Media Sentiment Analysis")
        
        # Display sentiment score
        sentiment_score = bias_results["sentiment_score"]
        sentiment_color = "green" if sentiment_score > 0 else "red" if sentiment_score < 0 else "gray"
        st.markdown(f"#### Overall Sentiment Score: <span style='color:{sentiment_color}'>{sentiment_score:.2f}</span>", unsafe_allow_html=True)
        
        # Count positive and negative headlines
        pos_count = len(sentiment_results["Positive"])
        neg_count = len(sentiment_results["Negative"])
        total_count = pos_count + neg_count
        
        if total_count > 0:
            st.markdown(f"• Positive headlines: {pos_count} ({pos_count/total_count:.0%})")
            st.markdown(f"• Negative headlines: {neg_count} ({neg_count/total_count:.0%})")
            
            # Display sentiment summary
            if sentiment_score > 0.3:
                st.markdown(f"✅ Media coverage of {player_name} at {tournament} {year} was **predominantly positive**.")
            elif sentiment_score < -0.3:
                st.markdown(f"❌ Media coverage of {player_name} at {tournament} {year} was **predominantly negative**.")
            else:
                st.markdown(f"➖ Media coverage of {player_name} at {tournament} {year} was **relatively balanced**.")
        else:
            st.warning("No positive or negative headlines found for sentiment analysis.")
        
        # Display headlines with sentiment and agreement with stats
        if bias_results["sentiment_details"]:
            st.markdown("#### Headlines Sentiment Details")
            
            sentiment_data = {
                "Headline": [],
                "Sentiment": [],
               # "Agrees with Stats": []
            }
            
            for detail in bias_results["sentiment_details"]:
                sentiment_data["Headline"].append(detail["Headline"])
                
                # Format sentiment with colors
                sentiment_text = detail["Sentiment"]
                sentiment_color = "green" if sentiment_text == "Positive" else "red"
                sentiment_data["Sentiment"].append(f"<span style='color:{sentiment_color}'>{sentiment_text}</span>")
                
                # Format agreement with stats
                # agrees = detail["Agrees with Stats"]
                # agrees_color = "green" if agrees == "Yes" else "red"
                # sentiment_data["Agrees with Stats"].append(f"<span style='color:{agrees_color}'>{agrees}</span>")
            
            # Create DataFrame for display
            sentiment_df = pd.DataFrame(sentiment_data)
            
            # Display with HTML formatting
            st.write(sentiment_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # Tab 4: Bias Assessment
    with bias_tabs[3]:
        st.markdown("### Media Bias Assessment")
        
        # Display bias score and level
        bias_score = bias_results["bias_score"]
        bias_level = bias_results["bias_level"]
        bias_description = bias_results["bias_description"]
        
        # Determine color based on bias magnitude (not direction)
        bias_magnitude = abs(bias_score)
        bias_color = "green" if bias_magnitude < 0.3 else "orange" if bias_magnitude < 0.7 else "red"
        
        st.markdown(f"#### Bias Score: <span style='color:{bias_color}'>{bias_score:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"#### Bias Level: <span style='color:{bias_color}'>{bias_level}</span>", unsafe_allow_html=True)
        
        # Display bias description
        st.markdown(f"**Assessment**: {bias_description}")
        
        # Show interpretation
        st.markdown("#### Interpretation")
        if bias_score > 0.7:
            st.markdown("⚠️ The media coverage appears to be **significantly more positive** than the player's performance metrics would suggest, indicating potential positive bias.")
        elif bias_score < -0.7:
            st.markdown("⚠️ The media coverage appears to be **significantly more negative** than the player's performance metrics would suggest, indicating potential negative bias.")
        elif bias_score > 0.3:
            st.markdown("ℹ️ The media coverage is **somewhat more positive** than the player's performance metrics would suggest.")
        elif bias_score < -0.3:
            st.markdown("ℹ️ The media coverage is **somewhat more negative** than the player's performance metrics would suggest.")
        else:
            st.markdown("✅ The media coverage appears to be **fairly balanced** and aligns well with the player's actual performance.")
