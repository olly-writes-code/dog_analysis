import string

import requests
from bs4 import BeautifulSoup

with open("urls_to_skip.txt", "r") as f:
    URLS_TO_SKIP = f.read().splitlines()
INPUT_URL = "https://www.akc.org/dog-breeds/?letter="
### hard coded to save time for now
NUMBER_OF_PAGES = 24

def get_breed_urls_from_page(page_number):
    html_data = requests.get(f"https://www.akc.org/dog-breeds/page/{page_number}/")
    html_soup = BeautifulSoup(html_data.content, "html5lib")
    breed_urls = set()
    for i in html_soup.find_all("a"):
        href = i.attrs.get("href")
        if href is not None:
            if "https://www.akc.org/dog-breeds/" in href and href not in URLS_TO_SKIP:
                breed_urls.add(href)
    return breed_urls


if __name__ == "__main__":
    all_breed_urls = set()
    for i in range(1, NUMBER_OF_PAGES+1):
        all_breed_urls.update(get_breed_urls_from_page(i))
    print(all_breed_urls)
    print(len(all_breed_urls))
