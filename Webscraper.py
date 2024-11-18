# For HTTP requests
import requests  
# To parse HTML and scrape info
from bs4 import BeautifulSoup  

def scrape_bbc_sport_headlines(query, max_pages=1):
    """
    Scrapes BBC Sport search results for headlines matching a query.
    
    Args:
    query (str): The search term (e.g., a player's name like "Nadal").
    max_pages (int): The number of pages to scrape.

    Returns:
    list: A list of dictionaries containing scraped headlines.
    """
    articles = []  # Initialize an empty list to store the results

    # Loop through the specified number of pages
    for page in range(1, max_pages + 1):
        # Format the URL with the query and page number
        url = f"https://www.bbc.co.uk/search?q={query}&page={page}"
        
        # Set headers to mimic a browser (prevents being blocked by the server)
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        # }
        
        # Make a GET request to the URL with code to mimic a browser
        # response = requests.get(url, headers=headers)
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
            
            # Append the headline as a dictionary to the articles list
            articles.append({'headline': headline})
        
        # Print a message indicating the page was successfully scraped
        print(f"Page {page} scraped successfully. Found {len(articles)} articles so far.")
    
    return articles  # Return the list of articles

# Edit the parameters of the scraping
# Player's name
query = "Nadal"  
# Number of pages to scrape
max_pages = 4 
# Call scraping function 
headlines = scrape_bbc_sport_headlines(query, max_pages)  

# Check if any headlines were found and display them
if headlines:
     # Enumerate the list to add numbering
    for i, article in enumerate(headlines, 1): 
        # Print each headline with in numbered order
        print(f"{i}. {article['headline']}") 
else:
    print("No articles found.")  # Print a message if no headlines were scraped
