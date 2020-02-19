import pandas as pd
import requests
from bs4 import BeautifulSoup
from statistics import mean

from loguru import logger

with open("dog_breed_urls.txt", "r") as f:
    BREED_URLS = f.read().splitlines()

CSS_SELECTORS = dict(
    groom_freq="#panel-GROOMING > div:nth-child(1) > div:nth-child(4) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > div:nth-child(1)",
    shedding="#panel-GROOMING > div:nth-child(1) > div:nth-child(4) > div:nth-child(2) > div:nth-child(1) > div:nth-child(3) > div:nth-child(1)",
    exercise="#panel-EXERCISE > div:nth-child(1) > div:nth-child(4) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > div:nth-child(1)",
    trainability="#panel-TRAINING > div:nth-child(1) > div:nth-child(4) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > div:nth-child(1)",
    temperment="#panel-TRAINING > div:nth-child(1) > div:nth-child(4) > div:nth-child(2) > div:nth-child(1) > div:nth-child(3) > div:nth-child(1)",
    # health_tests="#panel-HEALTH > div:nth-child(1) > ul:nth-child(5)",
)

CSS_DEFAULT_SELECTORS = dict(
    exercise="html.gr__akc_org body.breed-template-default.single.single-breed div.cmw.bgc-white.page-single-breed section#breed-care div.tabs-with-image div.tabs-with-image__layout div.tabs-with-image__main div.tabs.tabs--active-border div.tabs__panel-wrap div#panel-EXERCISE.tabs__tab-panel.is-active div.tabs__tab-panel-content div.graph-section div.graph-section__inner div.bar-graph div.bar-graph__bg div.bar-graph__section",
    temperment="html.gr__akc_org body.breed-template-default.single.single-breed div.cmw.bgc-white.page-single-breed section#breed-care div.tabs-with-image div.tabs-with-image__layout div.tabs-with-image__main div.tabs.tabs--active-border div.tabs__panel-wrap div#panel-TRAINING.tabs__tab-panel.is-active div.tabs__tab-panel-content div.graph-section div.graph-section__inner div.bar-graph div.bar-graph__bg div.bar-graph__section",
    health_tests="html.gr__akc_org body.breed-template-default.single.single-breed div.cmw.bgc-white.page-single-breed section#breed-care div.tabs-with-image div.tabs-with-image__layout div.tabs-with-image__main div.tabs.tabs--active-border div.tabs__panel-wrap div#panel-HEALTH.tabs__tab-panel.is-active div.tabs__tab-panel-content ul",
)

class Breed:
    def __init__(self, url):
        name =


def get_name(html_soup):
    return html_soup.select("#page-title")[0].text.replace(" ", "").replace("\n", "")


def get_personality(html_soup):
    return html_soup.find_all(
        "span",
        class_="attribute-list__description attribute-list__text attribute-list__text--lg mb4 bpm-mb5 pb0 d-block",
    )[0].text


def estimate_height(html_soup):
    range = html_soup.select("li.attribute-list__row:nth-child(3) > span:nth-child(2)")[
        0
    ].text.replace(" inches", "")
    range_list = [float(x) for x in range.split("-")]
    return mean(range_list)


def estimate_weight(html_soup):
    range = html_soup.select("li.attribute-list__row:nth-child(4) > span:nth-child(2)")[
        0
    ].text.replace(" pounds", "")
    range_list = [float(x) for x in range.split("-")]
    return mean(range_list)


def estimate_life_exp(html_soup, name):
    try:
        range = html_soup.select("li.attribute-list__row:nth-child(5) > span:nth-child(2)")[
            0
        ].text.replace(" years", "")
        range_list = [float(x) for x in range.split("-")]
        return mean(range_list)
    except:
        logger.warning('bad_data for {}')
        return None


def get_bar_value(css_selector_name, html_soup):
    css_selector = CSS_SELECTORS[css_selector_name]
    percentage_string = html_soup.select(css_selector)[0].attrs["style"]
    score = int(percentage_string.replace("width: ", "").replace("%;",""))
    return score

def health_check_count(css_selector_name, html_soup):
    css_selector = CSS_SELECTORS[css_selector_name]

def get_breed_data(url):
    html_data = requests.get(url)
    html_soup = BeautifulSoup(html_data.content, "html5lib")
    breed_data = dict(
        name=get_name(html_soup),
        personality=get_personality(html_soup),
        # estimated_height_inches=estimate_height(html_soup), removing these for now as the parsing is hard for male female
        # estimated_weight=estimate_weight(html_soup),
        estimated_life_exp=estimate_life_exp(html_soup),
        grooming_freq=get_bar_value('groom_freq',html_soup),  # occasional to lots
        shedding=get_bar_value('shedding',html_soup),  # infreq to freq
        exercise_required = get_bar_value('exercise',html_soup),  # little to lots
        trainability = get_bar_value('trainability',html_soup),  # stubborn to eager to please
        temperament = get_bar_value('temperment',html_soup),  # aloof to outgoing
        # number_of_recommended_health_checks = None  # the higher the unhealthier
    )
    return breed_data


if __name__ == "__main__":
    data = [get_breed_data(i) for i in BREED_URLS]
    pd.DataFrame(data).to_csv('dog_dataset.csv',index=False)


