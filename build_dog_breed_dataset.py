import json
from dataclasses import dataclass, asdict
from statistics import mean

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger
from tqdm import tqdm
from itertools import zip_longest

URL_SUFFIX = "https://www.akc.org/dog-breed-selector/?breeds="

CSS_SELECTORS = {
    "personality": "div.breed-results-comparison__row:nth-child(5)",
    "size": "div.breed-results-comparison__row:nth-child(14)",
    "life_exp": "div.breed-results-comparison__row:nth-child(17)",
    "trainability": "div.breed-results-comparison__row:nth-child(23)",
    "grooming": "div.breed-results-comparison__row:nth-child(29)",
    "shedding": "div.breed-results-comparison__row:nth-child(32)",
    "activity_level": "div.breed-results-comparison__row:nth-child(35)",
    "barking": "div.breed-results-comparison__row:nth-child(38)",
}


STRING_TO_RATING = {
    "May Be Stubborn": 1,
    "Independent": 2,
    "Agreeable": 3,
    "Easy Training": 4,
    "Eager to Please": 5,
    "Couch Potato": 1,
    "Calm": 2,
    "Regular Exercise": 3,
    "Energetic": 4,
    "Needs Lots of Activity": 5,
}

### from this for list iteration in chunks https://stackoverflow.com/a/434411/5846481
def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def get_data_from_table(selector, html_soup, index):
    css_selector = CSS_SELECTORS.get(selector)
    return [i for i in html_soup.select(css_selector)[0].contents if type(i) == Tag][
        index
    ]


def clean_text(text_input):
    return (
        text_input.replace("\n", "")
        .replace("\t", "")
        .replace("  ", "")
        .replace("15 ", "")
    )


def clean_percentage(text_input):
    return 5 * (int(text_input.replace("width: ", "").replace("%;", "")) / 100)


def estimate_life_exp(input_text):
    try:
        age_range = input_text.replace(" years", "")
        range_list = [float(x) for x in age_range.split("-")]
        return mean(range_list)
    except:
        scrubbed_text = (
            input_text.replace("+", "")
            .replace("\n", "")
            .replace("\t", "")
            .replace(" ", "")
            .replace("years", "")
            .replace("~", "")
        )
        if "Lateteens" in scrubbed_text:
            return 18
        else:
            return float(scrubbed_text)


def reverse_scale(rating):
    # we always want the best score for our need to be 5.
    # this means we may need to reverse the scale
    return abs(rating - 6)


def get_breed_dataset_from_html(breed_id_list):
    full_url = URL_SUFFIX + json.dumps(breed_id_list)
    html_data = requests.get(full_url)
    html_soup = BeautifulSoup(html_data.content, "html5lib")
    dataset = []
    for idx, breed_id in tqdm(enumerate(breed_id_list)):
        ### missing data for 'Spinone Italiano - id - 25794' will ignore
        if breed_id not in {None, 25794}:
            name = breed_id_map.get(str(breed_id))
            personality = clean_text(
                get_data_from_table("personality", html_soup, idx).text
            )
            size = get_data_from_table("size", html_soup, idx).contents[1].text
            estimated_life_exp = estimate_life_exp(
                get_data_from_table("life_exp", html_soup, idx).text
            )
            trainability = STRING_TO_RATING[
                clean_text(get_data_from_table("trainability", html_soup, idx).text)
            ]
            try:
                grooming = clean_percentage(
                    get_data_from_table("grooming", html_soup, idx)
                    .contents[1]
                    .contents[3]
                    .contents[1]
                    .attrs["style"]
                )
            except:
                # assume this is because it doesn't effect them
                logger.warning(f"no grooming info for {name}")
                grooming = 1
            try:
                shedding = clean_percentage(
                    get_data_from_table("shedding", html_soup, idx)
                    .contents[1]
                    .contents[3]
                    .contents[1]
                    .attrs["style"]
                )
            except:
                logger.warning(f"no shedding info for {name}")
                shedding = 1
            grooming_score = reverse_scale(grooming)
            shedding_score = reverse_scale(shedding)
            activity_level = STRING_TO_RATING[
                clean_text(get_data_from_table("activity_level", html_soup, idx).text)
            ]
            activity_level_score = reverse_scale(activity_level)
            try:
                barking = clean_percentage(
                    get_data_from_table("barking", html_soup, idx)
                    .contents[1]
                    .contents[3]
                    .contents[1]
                    .attrs["style"]
                )
                barking_score = reverse_scale(barking)
            except:
                logger.warning(
                    f"missing barking data for {name} setting to medium which is 3"
                )
                barking_score = 3
            dataset.append(
                Breed(
                    name,
                    personality,
                    size,
                    estimated_life_exp,
                    trainability,
                    grooming_score,
                    shedding_score,
                    activity_level_score,
                    barking_score,
                )
            )
    return dataset


@dataclass
class Breed:
    name: str
    personality: str
    size: str
    estimated_life_exp: float
    trainability_score: int  # low to high trainability
    grooming_score: int  # high grooming to low grooming needs
    shedding_score: int  # occasional to frequent
    activity_level_score: int
    barking_score: int


if __name__ == "__main__":
    with open("breed_id_map.json") as f:
        breed_id_map = json.load(f)
    chunked_html_soup = []
    breed_id_list = [int(i) for i in breed_id_map.keys()]
    dataset = []
    for i in grouper(breed_id_list, 10):
        dataset.extend(get_breed_dataset_from_html(i))
    df = pd.DataFrame([asdict(x) for x in dataset])
    df.to_csv("breed_dataset.csv", index=False)
