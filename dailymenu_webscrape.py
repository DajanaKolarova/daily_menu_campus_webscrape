from codecs import xmlcharrefreplace_errors

import requests
import logging
from bs4 import BeautifulSoup
from datetime import date
#import pytesseract


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

seznam_restauraci = {
    "restaurant_kulatak": "https://kulatak.cz/#menu-obsah",
    "jidlovice": "https://www.jidlovice.cz/telehouse/",
    "jidelna17": "https://www.jidelna17.cz/tydenni-menu",
}

def get_web(url):
    response = requests.get(url)
    page_html = response.text # pomocná proměnná

    page = BeautifulSoup(page_html)  # veme html co jsme stahli a zparsuje ten STRING plnej html ho do actual python objektu (napr. listy, dictionaries...)
    return page


def get_jidlovice_api():
    dnesni_datum = date.today().strftime('%Y-%m-%d')
    url = "https://jidlovice.cz/api/v1/branch/3/menu/" + dnesni_datum
    response = requests.get(url)
    jidlovice_dict = response.json()
    return jidlovice_dict


def scrape_jidlovice(jidlovice_dict):

    try:
        menu = []
        for jedno_jidlo in jidlovice_dict["menu_items"]:
            nazev_jidla = jedno_jidlo["meal"]["name"]
            popis_jidla = jedno_jidlo["meal"]["description"]
            cena_jidla = jedno_jidlo["meal"]["price"]

            dict = {"text_jidlo": nazev_jidla + popis_jidla, "text_cena": cena_jidla}
            menu.append(dict)
        print(menu)
        return menu


    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_kulatak(page):

    try:
        container = page.find(attrs={"class": "elementor-element-425aa18"})
        paragraphs = container.find_all('p')
        for jeden_paragraf in paragraphs:
            text_paragrafu = jeden_paragraf.get_text().strip().replace("\n", "")

            if text_paragrafu != "":
                print(text_paragrafu)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_jidelna17(page):

    try:
        container = page.find(attrs={"id": "pondeli"})
        row_jidel = container.find_all(attrs={"class": "food-menu__list-item-row"})


        menu = []
        for jidlo in row_jidel:

            element_jidlo = jidlo.find(attrs={"class": "food-menu__list-item-title"})
            if element_jidlo is None:
                continue
            text_jidlo = element_jidlo.get_text().strip()

            text_cena = jidlo.find(attrs={"class": "food-menu__list-item-price"}).get_text()
            dic = {"text_jidlo": text_jidlo, "text_cena": text_cena}
            menu.append(dic)

        from pprint import pprint
        pprint(menu)
        return menu


    except Exception as e:
        logger.error(f"Unexpected error: {e}")


for NAZEV_RESTAURACE, url in seznam_restauraci.items():

    if NAZEV_RESTAURACE == "restaurant_kulatak":
        scrape_kulatak(get_web(url))

    elif NAZEV_RESTAURACE == "jidlovice":
        scrape_jidlovice(get_jidlovice_api())

    elif NAZEV_RESTAURACE == "jidelna17":
        scrape_menu = scrape_jidelna17(get_web(url))

    else:
        print("Máš hlad? Tak si ho hlad")
