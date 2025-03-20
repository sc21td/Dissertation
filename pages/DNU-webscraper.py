import os
import csv
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import time

# DEBUGGING: Add logging imports
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CSV file for storing irrelevant headlines
IGNORE_CSV = "irrelevant_headlines.csv"

# Load existing ignored headlines from CSV
def load_ignored_headlines():
    # DEBUGGING: Log attempt to load ignored headlines
    logger.info("Attempting to load ignored headlines from CSV")
    
    if os.path.exists(IGNORE_CSV):
        headlines = set(pd.read_csv(IGNORE_CSV)["Headline"])
        # DEBUGGING: Log number of loaded headlines
        logger.info(f"Loaded {len(headlines)} ignored headlines from CSV")
        return headlines
    
    # DEBUGGING: Log when CSV doesn't exist
    logger.info(f"Ignored headlines file {IGNORE_CSV} not found")
    return set()

ignored_headlines = load_ignored_headlines()

# Function to save new irrelevant headlines to CSV
def save_ignored_headlines(new_ignored):
    # DEBUGGING: Log save attempt
    logger.info(f"Attempting to save {len(new_ignored) if new_ignored else 0} new ignored headlines")
    
    if not new_ignored:
        logger.info("No new headlines to save")
        return

    # Append to CSV file
    with open(IGNORE_CSV, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for headline in new_ignored:
            writer.writerow([headline])
    
    # DEBUGGING: Log save completion
    logger.info(f"Saved {len(new_ignored)} new ignored headlines")

# Function to scrape BBC Sport headlines with URLs
def scrape_bbc_sport(player, tournament, year, max_pages=3):
    search_query = f"{player} {tournament} {year}".replace(" ", "+")
    base_url = "https://www.bbc.co.uk/search?q="
    headlines_data = []
    all_headlines = []

    # DEBUGGING: Log search parameters
    logger.info(f"Starting scrape with query: {search_query}, max_pages: {max_pages}")

    for page in range(1, max_pages + 1):
        url = f"{base_url}{search_query}&page={page}"
        
        # DEBUGGING: Log current page being scraped
        logger.info(f"Fetching page {page} from URL: {url}")
        
        try:
            response = requests.get(url)
            # DEBUGGING: Log response status
            logger.info(f"Response status code: {response.status_code}")

            if response.status_code != 200:
                st.warning(f"Failed to fetch page {page} (Status {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            
            # DEBUGGING: Log HTML structure inspection
            logger.info(f"HTML retrieved, length: {len(response.text)} characters")
            
            # Directly search for span tags with aria-hidden="false"
            headline_tags = soup.find_all("span", attrs={"aria-hidden": "false"})
            logger.info(f"Found {len(headline_tags)} headline tags on page {page}")

            headlines_found_on_page = 0
            
            # Process each headline
            for headline_tag in headline_tags:
                # Removes whitespaces
                headline = headline_tag.get_text(strip=True)
                # Store all headlines for duplicate checking
                all_headlines.append(headline)  
                
                # DEBUGGING: Log found headline
                logger.info(f"Found headline: {headline}")
                
                # Try to find associated link by traversing up the Document Object model
                link_tag = None
                parent = headline_tag.parent
                # Check up to 3 levels up
                for _ in range(3):  
                    # Check parent element of the headline is an anchor tag with href attribute
                    # If it is then that is captured as the link and it stops looking
                    if parent and parent.name == 'a' and parent.has_attr('href'):
                        link_tag = parent
                        break
                    elif parent:
                        # Try to find an adjacent link
                        link_tag = parent.find('a', href=True)
                        if link_tag:
                            break
                        # If still not found it moves up to the parent's parent 
                        parent = parent.parent
                    else:
                        break
                
                # If link is found then the URL is extracted from href attribute
                if link_tag:
                    article_url = link_tag["href"]
                    # Check URL is relative - doesn't start with HTTP
                    if not article_url.startswith("http"):
                        # Prepend with base URL of BBC domain
                        article_url = "https://www.bbc.co.uk" + article_url
                    logger.info(f"Found link for headline: {article_url}")
                else:
                    article_url = ""
                    logger.info("No link found for this headline")
                
                # Store the headline data
                headlines_data.append({
                    "Headline": headline,
                    "Source": "BBC",
                    "URL": article_url,
                    "Sentiment": ""  # Empty for now
                })
                headlines_found_on_page += 1
            
            # DEBUGGING: Log summary for this page
            logger.info(f"Added {headlines_found_on_page} headlines from page {page}")
            
            # DEBUGGING: If no headlines found, print page structure
            if headlines_found_on_page == 0:
                logger.info("No headlines found on this page. Checking HTML structure:")
                # Print some key elements to help diagnose the issue
                page_title = soup.find('title')
                logger.info(f"Page title: {page_title.text if page_title else 'No title found'}")
                
                # Check for different element patterns
                possible_headline_containers = [
                    ("divs with class containing 'result'", soup.find_all("div", class_=lambda x: x and 'result' in x)),
                    ("h3 tags", soup.find_all("h3")),
                    ("spans with role=heading", soup.find_all("span", attrs={"role": "heading"}))
                ]
                
                for desc, elements in possible_headline_containers:
                    logger.info(f"Found {len(elements)} {desc}")
                    if len(elements) > 0:
                        logger.info(f"Sample {desc}: {elements[0].get_text(strip=True) if elements[0] else 'empty'}")

        except Exception as e:
            # DEBUGGING: Log any exceptions
            logger.error(f"Error scraping page {page}: {str(e)}")
        
        # DEBUGGING: Log sleep
        logger.info(f"Sleeping for 1 second before next page")
        # To avoid being blocked
        time.sleep(1)  
        
    # Identify duplicate headlines (if they appear more than once, they are irrelevant)
    logger.info(f"Processing {len(all_headlines)} total headlines for duplicates")
    duplicate_headlines = {h for h in all_headlines if all_headlines.count(h) > 1}
    logger.info(f"Found {len(duplicate_headlines)} duplicate headlines")
    
    # Update ignore list and remove duplicates
    ignored_headlines.update(duplicate_headlines)
    save_ignored_headlines(duplicate_headlines)
    
    # Filter out ignored and duplicate headlines
    filtered_data = [item for item in headlines_data if item["Headline"] not in ignored_headlines]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_filtered_data = []
    for item in filtered_data:
        headline = item["Headline"]
        if headline not in seen:
            seen.add(headline)
            unique_filtered_data.append(item)
    
    # DEBUGGING: Log final results
    logger.info(f"Scraping complete. Found {len(unique_filtered_data)} unique relevant headlines after filtering")
    
    return pd.DataFrame(unique_filtered_data)  # Return as a DataFrame

# Main function for Streamlit
def main():
    st.title("📰 BBC Sport Tennis Headline Scraper")

    # User input fields
    player = st.text_input("Enter Player Name (e.g., Jannik Sinner)")
    tournament = st.text_input("Enter Tournament Name (e.g., Wimbledon)")
    year = st.text_input("Enter Year (e.g., 2024)")
    max_pages = st.slider("Select Number of Pages to Scrape", 1, 5, 3)

    if st.button("Scrape BBC Headlines"):
        # DEBUGGING: Log button click
        logger.info(f"Scrape button clicked with inputs: Player={player}, Tournament={tournament}, Year={year}")
        
        if player and tournament and year:
            # DEBUGGING: Log scraping start
            logger.info("Starting scraping process")
            
            scraped_df = scrape_bbc_sport(player, tournament, year, max_pages)

            # DEBUGGING: Log scraping results
            logger.info(f"Scraping finished. DataFrame has {len(scraped_df)} rows")

            if not scraped_df.empty:
                st.write(f"### Scraped Headlines for {player} at {tournament} {year}")
                
                # Add functionality to mark headlines as irrelevant
                st.write("Click on any headline you want to mark as irrelevant:")
                
                # Display table with checkboxes
                for i, row in scraped_df.iterrows():
                    col1, col2 = st.columns([4, 1])
                    headline = row["Headline"]
                    url = row["URL"]
                    
                    with col1:
                        if url:
                            st.markdown(f"[{headline}]({url})")
                        else:
                            st.write(headline)
                    
                    with col2:
                        if st.button(f"Ignore", key=f"ignore_{i}"):
                            # Add to ignored headlines
                            ignored_headlines.add(headline)
                            save_ignored_headlines([headline])
                            st.success(f"Marked '{headline}' as irrelevant")
                            # Refresh the page to update results
                            st.rerun()  
                
                # Also provide the full dataframe view
                st.write("### Full Data Table")
                st.dataframe(scraped_df)
            else:
                st.warning("No headlines found.")
                # DEBUGGING: Log empty results
                logger.warning("No headlines were found. Check the search parameters or BBC site structure.")
        else:
            st.error("Please enter all fields (Player, Tournament, Year).")
            # DEBUGGING: Log missing inputs
            logger.error("Missing required input fields")

if __name__ == "__main__":
    # DEBUGGING: Log application start
    logger.info("Application started")
    main()