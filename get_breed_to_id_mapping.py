import json

import requests
from bs4 import BeautifulSoup, Tag

BREED_SELECTOR_URL = "https://www.akc.org/compare-breeds/"
BREED_SELECTOR_CSS = ".breed-comparison-wrap-fixed > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(2)"

if __name__ == "__main__":
    html_data = requests.get(BREED_SELECTOR_URL)
    html_soup = BeautifulSoup(html_data.content, "html5lib")
    breed_selector_html = html_soup.select(BREED_SELECTOR_CSS)
    breed_id_map = {int(i.attrs['data-id']): i.attrs['data-title'] for i in breed_selector_html[0].contents if type(i) == Tag}
    with open('breed_id_map.json', 'w') as fp:
        json.dump(breed_id_map, fp)
