import pandas as pd
# Importing Vader
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# Needed for tokenisation
import re
# For visualising common words
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Function to classify sentiment
def sentiment_scores(sentence):
    sid_obj = SentimentIntensityAnalyzer()

    # Adjusting the existing lexicon
    # sid_obj.lexicon.update(positive_adjustments)
    # sid_obj.lexicon.update(negative_adjustments)
    # sid_obj.lexicon.update(neutral_adjustments)

    sentiment_dict = sid_obj.polarity_scores(sentence)

    # Determine sentiment category
    # Default values are 0.05
    if sentiment_dict['compound'] >= 0.05:
        return "Positive"
    elif sentiment_dict['compound'] <= -0.05:
        return "Negative"
    else:
        return "Neutral"

def file_for_analysis(file_path):

    csv = pd.ExcelFile(file_path)
    # Dictionary of all the sheets in the excel
    sheets = {sheet: csv.parse(sheet) for sheet in csv.sheet_names}

    testSheet = sheets["Neutral"]

    # Apply sentiment analysis and store results in Updated Vader rating column
    testSheet["Updated Dictionary Vader Rating"] = testSheet["Statement"].apply(sentiment_scores)

    # Update the dictionary of sheets with updated sheet
    sheets["Neutral"] = testSheet

    with pd.ExcelWriter(file_path, engine="openpyxl", mode="w") as writer:
        for sheet_name, data in sheets.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)

    print("Sentiment classification completed and saved to", file_path)

def key_words(file_path):
    # Read in the current non matching headlines
    headlines = pd.read_excel(file_path, sheet_name="Token test")

    # Tokenise the headlines and strip the filler words
    # List of words to identify commonality 
    words = []

    # Loop through all headlines and extract the lower case version of each word
    for headline in headlines["Headlines"]:  
        tokens = re.findall(r'\b\w+\b', headline.lower()) 
        words.extend(tokens)

    print("Sample of the tokenised headlines" , words[0:50])

    # Visualise common themes on a word cloud to identify patterns

    # Convert word frequency to a string format for the word cloud
    text = " ".join(words)

    # Generate word cloud
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)

    # Display the word cloud
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off") 
    plt.show()

# Load the CSV file, currently testing negative 
file_path = "Sentiment Testing.xlsx"
key_words(file_path)