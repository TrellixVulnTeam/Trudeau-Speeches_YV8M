# Libraries for scraping
import requests
from bs4 import BeautifulSoup
from pprint import pprint

# Libraries for database setup
from pymongo import MongoClient

# Using Firefox to scrape data
headers = {
    'User-Agent':  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'
}

# Gets soup from URL and outputs a BeautifulSoup object
def make_soup(url: str) -> BeautifulSoup:
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    
    return BeautifulSoup(res.text, 'html.parser')


# Using AJAX requests to scrape speech despite hidden nature of divs
def fetch_speech_details(speech_id: str) -> str:

    # AJAX requests link. Replaced ID with speech_id collected from teaser
    url = 'https://pm.gc.ca/eng/views/ajax?view_name=news_article&view_display_id=block&view_args={id}'
    url = url.format(id = speech_id)

    # Get the speech
    res = requests.get(url, headers=headers)
    res.raise_for_status()

    # Convert to proper form using BeautifulSoup
    data = res.json()
    html = data[1]['data']
    soup = BeautifulSoup(html, 'html.parser')

    # Select the speech content
    body = soup.select_one('.views-field-body')
    speech_text = body.get_text()

    return str(speech_text)


# Function to scrape speeches one by one
def scrape_speeches(soup: BeautifulSoup) -> dict:
    speeches = []

    # Can collect all data from the teaser, so looping through all teasers
    for teaser in soup.select('.teaser'):

        # Getting title and date from speech
        title = teaser.select_one('.title').text.strip()
        date = teaser.select_one('.date-display-single').text.strip()

        # Getting ID that can be used to get speech
        speech_id = teaser['data-nid']
        speech_html = fetch_speech_details(speech_id)

        # Putting details into a dictionary and appending to initial array
        s = {
            'title': title,
            'date': date,
            'details': speech_html
        }
        speeches.append(s)
    return speeches

# Storing speeches in MongoDB database
def store_database(speeches: dict):
    
    client = MongoClient('localhost', 27017)

    # Setting up dataset and storing data
    db = client.trudeau_speeches
    db_speeches = db.db_speeches

    # Inserting speeches into database
    result = db_speeches.insert_many(speeches)

    # Writing IDs to text file
    write_id(result)

    print ("Database post success!")

    return

# Writing ID to txt file for future use
def write_id(db_result):
    # Extracting IDs for posts
    object_ids = db_result.inserted_ids

    # Opening file and writing IDs in string format
    file_object = open('../data/speech_ids.txt', mode = 'w')
    file_object.write(str(object_ids))

if __name__ == "__main__":

    # Original URL of website
    url = 'https://pm.gc.ca/eng/news/speeches'

    # Making BeautifulSoup object of the website html
    soup = make_soup(url)

    # Scraping speeches one by one
    speeches = scrape_speeches(soup)
    pprint(speeches)

    # Saving speeches in MongoDB database
    store_database(speeches)