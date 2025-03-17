import os
import csv
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import time

# CSV file for storing irrelevant headlines
IGNORE_CSV = "irrelevant_headlines.csv"

# Load existing ignored headlines from CSV
def load_ignored_headlines():
    if os.path.exists(IGNORE_CSV):
        return set(pd.read_csv(IGNORE_CSV)["Headline"])
    return set()

ignored_headlines = load_ignored_headlines()

# Function to save new irrelevant headlines to CSV
def save_ignored_headlines(new_ignored):
    if not new_ignored:
        return

    # Append to CSV file
    with open(IGNORE_CSV, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for headline in new_ignored:
            writer.writerow([headline])

# Function to scrape BBC Sport headlines
def scrape_bbc_sport(player, tournament, year, max_pages=3):
    search_query = f"{player} {tournament} {year}".replace(" ", "+")
    base_url = "https://www.bbc.co.uk/search?q="
    headlines = []
    all_headlines = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}{search_query}&page={page}"
        response = requests.get(url)

        if response.status_code != 200:
            st.warning(f"Failed to fetch page {page} (Status {response.status_code})")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for item in soup.find_all("span", attrs={"aria-hidden": "false"}):
            headline = item.get_text(strip=True)
            all_headlines.append(headline)  # Store all headlines for duplicate checking

        time.sleep(1)  # To avoid being blocked

    # Identify duplicate headlines (if they appear more than once, they are irrelevant)
    duplicate_headlines = {h for h in all_headlines if all_headlines.count(h) > 1}

    # Update ignore list and remove duplicates
    ignored_headlines.update(duplicate_headlines)
    save_ignored_headlines(duplicate_headlines)

    # Remove ignored and duplicate headlines
    filtered_headlines = [h for h in set(all_headlines) if h not in ignored_headlines]

    return filtered_headlines

# Main function for Streamlit
def main():
    st.title("📰 BBC Sport Tennis Headline Scraper")

    # User input fields
    player = st.text_input("Enter Player Name (e.g., Jannik Sinner)")
    tournament = st.text_input("Enter Tournament Name (e.g., Wimbledon)")
    year = st.text_input("Enter Year (e.g., 2024)")
    max_pages = st.slider("Select Number of Pages to Scrape", 1, 5, 3)

    if st.button("Scrape BBC Headlines"):
        if player and tournament and year:
            scraped_headlines = scrape_bbc_sport(player, tournament, year, max_pages)

            if scraped_headlines:
                st.write(f"### Scraped Headlines for {player} at {tournament} {year}")
                df = pd.DataFrame(scraped_headlines, columns=["Headline"])
                st.dataframe(df)  # Display results in table format
            else:
                st.warning("No headlines found.")
        else:
            st.error("Please enter all fields (Player, Tournament, Year).")

if __name__ == "__main__":
    main()
