# Dissertation  
**Final Year Project — Tennis Media Sentiment Analysis**

This project is a Streamlit application designed to detect potential media bias in tennis journalism by comparing headline sentiment with player performance data.

To run the application, use the following command:
streamlit run .\Welcome.py

## Repository Structure

### Model Training
- **Code**: Scripts used to explore the functionality of VADER, and to train and test the custom sentiment classifier.
- **Confusion Matrices**: Contains confusion matrices from various test cases during parameter optimisation and benchmarking.
- **TrainingTestingDatasets**: Includes datasets used for training and testing the model, along with the VADER lexicon.

### Scraped Headlines
- Contains the original web scraping functionality and a collection of scraped headlines for different Top 10 ATP and WTA players to test system functionality.

### Statistics
- Includes match statistics CSV files from 2018–2024, sourced from Jeff Sackmann’s [Match Charting Project](https://github.com/JeffSackmann/tennis_atp).

### pages
- Contains the main Streamlit page (`main.py`) which brings together all components of the system.

## Key Files

- **BiasDetection.py**: Contains the functionality for performing bias detection, used within `main.py` (located in the `pages` folder).
- **SentimentModel.py**: Implements sentiment analysis on scraped headlines.
- **DataRetrievalFunc.py**: Responsible for retrieving and processing match statistics from the `Statistics` dataset.
- **WebscrapingFunc.py**: Contains the functionality for scraping tennis-related headlines.
- **Welcome.py**: The welcome page displayed when the Streamlit application is launched.
