# For HTTP requests
import requests  
# To parse HTML and scrape info
from bs4 import BeautifulSoup  

# import time
import csv

#List of irrelevant headlines on the BBC website - shows on each page
irrelevant_headlines = [
    "Dive into Asia's deep waters",
    "The new sequel to Magpie Murders",
    "A Tudor epic's thrilling final chapters",
    "Behind the singing, smiles and denim"
]

def scrape_bbc_sport_headlines(playerName,max_pages ,outputFile):
    # Initialise an empty list to store the results
    articles = []  

    # Loop through the specified number of pages
    for page in range(1, max_pages + 1):
        # Format the URL with the query and page number
        url = f"https://www.bbc.co.uk/search?q={playerName}&page={page}"
        response = requests.get(url)
        
        # Check if the request was successful (HTTP status code 200)
        if response.status_code != 200:
            print(f"Failed to fetch data from page {page}. Status code: {response.status_code}")
             # Skip to the next page if there's an error
            continue 

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
                # Write the header row
                writer.writeheader()  
                # Write the articles
                writer.writerows(articles)  

            print(f"Scraped articles have been saved to {outputFile}")
        else:
            print("No articles were found to save.")
    
    return articles  

# Edit the parameters of the scraping
# Player's name
playerName = input("Enter a players name to scrape information for: ")
# Number of pages to scrape
max_pages = 10
# Function calls 
outputFile = playerName + " - bbc headlines"
#bbc_headlines = scrape_bbc_sport_headlines(playerName, max_pages, outputFile) 

# if bbc_headlines:
#      # Enumerate the list to add numbering
#     for i, article in enumerate(bbc_headlines, 1): 
#         # Print each headline with in numbered order
#         print(f"{i}. {article['headline']}") 
# else:
#     print("No articles found.") 