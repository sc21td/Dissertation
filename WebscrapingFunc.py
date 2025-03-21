import requests
import csv
import time
import os
import pandas as pd
from bs4 import BeautifulSoup
import logging
import streamlit as st

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#############################
# WEBSCRAPER FUNCTIONS
#############################

# CSV file for storing irrelevant headlines
IGNORE_CSV = "irrelevant_headlines.csv"

# Load existing ignored headlines from CSV
def load_ignored_headlines():
    logger.info("Attempting to load ignored headlines from CSV")
    
    if os.path.exists(IGNORE_CSV):
        headlines = set(pd.read_csv(IGNORE_CSV)["Headline"])
        logger.info(f"Loaded {len(headlines)} ignored headlines from CSV")
        return headlines
    
    logger.info(f"Ignored headlines file {IGNORE_CSV} not found")
    return set()

# Function to save new irrelevant headlines to CSV
def save_ignored_headlines(new_ignored):
    logger.info(f"Attempting to save {len(new_ignored) if new_ignored else 0} new ignored headlines")
    
    if not new_ignored:
        logger.info("No new headlines to save")
        return

    # Append to CSV file
    with open(IGNORE_CSV, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for headline in new_ignored:
            writer.writerow([headline])
    
    logger.info(f"Saved {len(new_ignored)} new ignored headlines")

# Function to scrape BBC Sport headlines with URLs
def scrape_bbc_sport(player, tournament, year, max_pages, ignored_headlines):
    # For more efficient searching on BBC news split the player name
    # Only append the surname to the URL
    player_surname = player.split()[-1] 
    search_query = f"{player_surname} {tournament} {year}".replace(" ", "+")
    base_url = "https://www.bbc.co.uk/search?q="
    headlines_data = []
    all_headlines = []

    logger.info(f"Starting scrape with query: {search_query}, max_pages: {max_pages}")

    for page in range(1, max_pages + 1):
        url = f"{base_url}{search_query}&page={page}"
        
        logger.info(f"Fetching page {page} from URL: {url}")
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")

            if response.status_code != 200:
                st.warning(f"Failed to fetch page {page} (Status {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            
            logger.info(f"HTML retrieved, length: {len(response.text)} characters")
            
            # Directly search for span tags with aria-hidden="false"
            headline_tags = soup.find_all("span", attrs={"aria-hidden": "false"})
            logger.info(f"Found {len(headline_tags)} headline tags on page {page}")

            headlines_found_on_page = 0
            
            # Process each headline
            for headline_tag in headline_tags:
                headline = headline_tag.get_text(strip=True)
                all_headlines.append(headline)  
                
                logger.info(f"Found headline: {headline}")
                
                # Try to find associated link
                link_tag = None
                parent = headline_tag.parent
                for _ in range(3):  
                    if parent and parent.name == 'a' and parent.has_attr('href'):
                        link_tag = parent
                        break
                    elif parent:
                        link_tag = parent.find('a', href=True)
                        if link_tag:
                            break
                        parent = parent.parent
                    else:
                        break
                
                if link_tag:
                    article_url = link_tag["href"]
                    if not article_url.startswith("http"):
                        article_url = "https://www.bbc.co.uk" + article_url
                    logger.info(f"Found link for headline: {article_url}")
                else:
                    article_url = ""
                    logger.info("No link found for this headline")
                
                headlines_data.append({
                    "Headline": headline,
                    "Source": "BBC",
                    "URL": article_url,
                    "Sentiment": ""  # Empty for now
                })
                headlines_found_on_page += 1
            
            logger.info(f"Added {headlines_found_on_page} headlines from page {page}")
            
            if headlines_found_on_page == 0:
                logger.info("No headlines found on this page. Checking HTML structure:")
                page_title = soup.find('title')
                logger.info(f"Page title: {page_title.text if page_title else 'No title found'}")
                
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
            logger.error(f"Error scraping page {page}: {str(e)}")
        
        logger.info(f"Sleeping for 1 second before next page")
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
    
    logger.info(f"Scraping complete. Found {len(unique_filtered_data)} unique relevant headlines after filtering")
    
    return pd.DataFrame(unique_filtered_data)