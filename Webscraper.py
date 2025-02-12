# For HTTP requests
import requests  
# To parse HTML and scrape info
from bs4 import BeautifulSoup  

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time
import csv


#List of irrelevant headlines on the BBC website - shows on each page
irrelevant_headlines = [
    "Dive into Asia's deep waters",
    "The new sequel to Magpie Murders",
    "A Tudor epic's thrilling final chapters",
    "Behind the singing, smiles and denim"
]


def scrape_bbc_sport_headlines(playerName,max_pages ,outputFile):
    articles = []  # Initialize an empty list to store the results

    # Loop through the specified number of pages
    for page in range(1, max_pages + 1):
        # Format the URL with the query and page number
        url = f"https://www.bbc.co.uk/search?q={playerName}&page={page}"
        response = requests.get(url)
        
        # Check if the request was successful (HTTP status code 200)
        if response.status_code != 200:
            print(f"Failed to fetch data from page {page}. Status code: {response.status_code}")
            continue  # Skip to the next page if there's an error

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all <span> elements with the attribute aria-hidden="false"
        for item in soup.find_all('span', attrs={'aria-hidden': 'false'}):
            # Extract the text content from the <span> tag
            headline = item.get_text(strip=True)
            # Skip irrelevant headlines
            if headline in irrelevant_headlines:
                continue
            # Append the headline as a dictionary to the articles list
            articles.append({'headline': headline})
        
        # Print a message indicating the page was successfully scraped
        print(f"BBC page {page} scraped successfully. Found {len(articles)} articles so far.")

        # Write results to a CSV file
        if articles:
            with open(outputFile, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['headline']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()  # Write the header row
                writer.writerows(articles)  # Write the articles

            print(f"Scraped articles have been saved to {outputFile}")
        else:
            print("No articles were found to save.")
    
    return articles  # Return the list of articles


def scrape_espn_headlines(playerName,outputFile):
    """
    Scrapes ESPN search results for headlines using Selenium, handling cookies popups and updated structure.
    """
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    articles = []

    try:
        # Construct the URL for the player's search results
        url = f"https://www.espn.co.uk/search/_/type/articles/q/{playerName}"
        driver.get(url)  # Navigate to the URL

        # Handle the cookies popup if it appears
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'I Accept')]"))
            )
            cookies_button = driver.find_element(By.XPATH, "//button[contains(text(), 'I Accept')]")
            cookies_button.click()  # Click to accept cookies
            print("Cookies popup closed.")
        except TimeoutException:
            print("No cookies popup detected.")

        # Wait for articles to load (adjust timeout as needed)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@class, 'contentItem__content')]"))
            )

            # Locate articles using XPath
            items = driver.find_elements(By.XPATH, "//a[contains(@class, 'contentItem__content')]")
            for item in items:
                headline_element = item.find_element(By.XPATH, ".//h2")  # Find the <h2> inside the <a>
                headline = headline_element.text.strip()  # Extract the headline
                articles.append({'headline': headline})

            print(f"Scraped {len(articles)} articles from ESPN for {playerName}.")

        except TimeoutException:
            print("No articles were found or the page took too long to load.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()  # Close the browser
   
    if articles:
        with open(outputFile, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['headline', 'link']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()  # Write the header row
            writer.writerows(articles)  # Write the articles

        print(f"Scraped articles have been saved to {outputFile}.")
    else:
        print("No articles were scraped.")

    return articles




# Edit the parameters of the scraping
# Player's name
playerName = input("Enter a players name to scrape information for: ")
# Number of pages to scrape
max_pages = 10
# Function calls 
outputFile = playerName + " - bbc headlines"
#bbc_headlines = scrape_bbc_sport_headlines(playerName, max_pages, outputFile) 
outputFile = playerName + " - espn headlines"
espn_headlines = scrape_espn_headlines(playerName,outputFile) 

# Display results
if espn_headlines:
    for i, article in enumerate(espn_headlines, 1):  # Enumerate to add numbering
        print(f"{i}. {article['headline']}")
else:
    print("No articles found.")


# if bbc_headlines:
#      # Enumerate the list to add numbering
#     for i, article in enumerate(bbc_headlines, 1): 
#         # Print each headline with in numbered order
#         print(f"{i}. {article['headline']}") 
# else:
#     print("No articles found.") 