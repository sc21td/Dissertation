import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize Vader
sid_obj = SentimentIntensityAnalyzer()

# Get the lexicon dictionary
vader_lexicon = sid_obj.lexicon

#Print the first 20 entries to check
for word, score in list(vader_lexicon.items())[1000:1050]:  # Adjust number as needed
    print(f"{word}: {score}")


# word_to_check = "dominant"  # Change this to any word you want to inspect
# if word_to_check in vader_lexicon:
#     print(f"{word_to_check}: {vader_lexicon[word_to_check]}")
# else:
#     print(f"{word_to_check} is not in the lexicon.")


# Convert lexicon to a DataFrame
#df = pd.DataFrame(vader_lexicon.items(), columns=["Word", "Score"])

# Save to CSV
# df.to_csv("vader_lexicon.csv", index=False)

# print("Lexicon saved as vader_lexicon.csv")