from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Function to print sentiments of the sentence.
def sentiment_scores(sentence):

    # Create a SentimentIntensityAnalyzer object.
    sid_obj = SentimentIntensityAnalyzer()

    # polarity_scores method of SentimentIntensityAnalyzer object gives a sentiment dictionary.
    # which contains pos, neg, neu, and compound scores.
    sentiment_dict = sid_obj.polarity_scores(sentence)
    
    print("Overall sentiment dictionary is : ", sentiment_dict)
    print("Sentence was rated as ", sentiment_dict['neg']*100, "% Negative")
    print("Sentence was rated as ", sentiment_dict['neu']*100, "% Neutral")
    print("Sentence was rated as ", sentiment_dict['pos']*100, "% Positive")

    print("Sentence Overall Rated As", end=" ")

    # Decide sentiment as positive, negative, or neutral
    if sentiment_dict['compound'] >= 0.05 :
        print("Positive")
    elif sentiment_dict['compound'] <= -0.05 :
        print("Negative")
    else :
        print("Neutral")

def analyse_player_sentiment(sentence, winner, loser):
    # Get sentiment score for the whole sentence
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(sentence)
    
    # Assign sentiment to winner and loser
    # Positive sentiment for the winner
    winner_score = scores['compound']  
    # Negative sentiment for the loser
    loser_score = -scores['compound'] 
    
    print(f"\nSentence: {sentence}")
    print(f"Overall Sentiment: {scores}")
    print(f"{winner}: {winner_score} (Positive)")
    print(f"{loser}: {loser_score} (Negative)")

# Example usage
# analyse_player_sentiment("Sinner makes light work of Eubanks in Paris opener", "Sinner", "Eubanks")
# analyse_player_sentiment("Djokovic thrashes Medvedev in straight sets", "Djokovic", "Medvedev")
# analyse_player_sentiment("Rafael Nadal crashes out of the US Open", "Nadal", "Unknown")

# Main
if __name__ == "__main__" :

    print("\nPositive test:")
    sentence = "Sinner makes light work of Eubanks in Paris opener"
    print("\n" + sentence)
    winner = "Sinner"
    loser = "Eubanks"
    #analyse_player_sentiment(sentence, winner, loser)
    sentiment_scores(sentence)

    print("\n Mixed test:")
    sentence = "Djokovic overcomes 'issues' to set up Sinner final"
    print("\n" + sentence)
    winner = "Djokovic"
    loser = ""
    #analyse_player_sentiment(sentence, winner, loser)
    sentiment_scores(sentence)

    print("\n Negative test:")
    sentence = "Rafael Nadal loses in first round of French Open for first time"
    print("\n" + sentence)
    winner = ""
    loser = "Rafa Nadal"
    #analyse_player_sentiment(sentence, winner, loser)
    sentiment_scores(sentence)