from codecs import xmlcharrefreplace_errors
'''
termninal
python -m venv prostredi     
source prostredi/bin/activate
pip install -r requirements.txt
python flask_app.py
'''

import requests
import logging
from bs4 import BeautifulSoup
from datetime import date

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

seznam_restauraci = {
    "technicka_menza": "https://agata.suz.cvut.cz/jidelnicky/index.php?clPodsystem=3&lang=cs",
    "jidlovice": "https://www.jidlovice.cz/telehouse/",
    "jidelna17": "https://www.jidelna17.cz/tydenni-menu",
    "restaurant_kulatak": "https://kulatak.cz/#menu-obsah",
    "cafe_prostoru": "https://streva.prostoru.cz/jidelnicekvlozeny.php",
    #"uTopolu": "http://www.utopolu.cz/menu",
}

def get_web(url):
    try:
        response = requests.get(url)
        page_html = response.text
        page = BeautifulSoup(page_html, features="html.parser") # veme html co jsme stahli a zparsuje ten STRING plnej html ho do actual python objektu
        return page
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def get_jidlovice_api():
    try:
        dnesni_datum = date.today().strftime('%Y-%m-%d')
        url = "https://jidlovice.cz/api/v1/branch/3/menu/" + dnesni_datum
        response = requests.get(url)
        jidlovice_dict = response.json()
        return jidlovice_dict
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def scrape_jidlovice(jidlovice_dict):
    try:
        menu = []
        for jedno_jidlo in jidlovice_dict["menu_items"]:
            nazev_jidla = jedno_jidlo["meal"]["name"]
            popis_jidla = jedno_jidlo["meal"]["description"]
            cena_jidla = jedno_jidlo["meal"]["price"]
            dict = {"text_jidlo": nazev_jidla + popis_jidla, "text_cena": cena_jidla}
            menu.append(dict)
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_kulatak(page):
    try:
        menu = []
        container = page.find(attrs={"class": "elementor-element-425aa18"})
        paragraphs = container.find_all('p', attrs={"style": "text-align: center;"})
        pomocna_prom = ""
        for jeden_paragraf in paragraphs:
            text_paragrafu = jeden_paragraf.get_text().strip().replace("\n", "")
            if text_paragrafu != "":
                if (text_paragrafu[0].isdigit() and text_paragrafu[1] == ")") or "Specialita týdne" in text_paragrafu:
                    pomocna_prom += text_paragrafu
                    continue
                if pomocna_prom != "":
                    if ",-" in text_paragrafu:
                        if len(text_paragrafu) > 6:
                            dict = {"text_jidlo": pomocna_prom + " " + text_paragrafu[0:-5], "text_cena": text_paragrafu[-5:]} #lepší by bylo opmocí regexpu ale bolí mě z toho hlava
                            pass
                        else:
                            dict = {"text_jidlo": pomocna_prom, "text_cena": text_paragrafu}
                        pomocna_prom = ""
                        menu.append(dict)
                    else:
                        pomocna_prom += " " + text_paragrafu
# použít regexp protože najednou dali cenu do stejnýho paragrafu jako zbytek jídla
# ještě vyřešit specialitu týdne která pomocna proměnná najít specialitu týdne a pak to xo je za toim
        logging.debug(menu)
        return menu
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
        logging.debug(menu)
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_technicka(page):
    try:
        menu = []
        containers = page.select("div.col.d-flex.flex-column.h-100")
        for container in containers:
            text_jidlo = container.find(attrs={"class": "card-title mb-1"}).get_text()
            text_cena = container.find(attrs={"class": "badge cena-badge me-2"}).get_text()
            dic = {"text_jidlo": text_jidlo, "text_cena": text_cena}
            menu.append(dic)
        logging.debug(menu)
        #zkontroluj že menu není prázdný, pokud ano použij týdenní menu
        #  raise NotImplementedError("jeste to nemam hotovy")
        if len(menu) == 0: ## if not menu
            pass
        return menu
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def scrape_prostoru(page):
    dnesni_datum = date.today().strftime('%d.%-m.')

    try:
        menu = []
        container = page.find("table")
        table_rows = container.find_all("tr")
        for table_row in table_rows:
            elements_in_row = table_row.find_all("td")
            if len(elements_in_row) == 0:
                continue
            if dnesni_datum in elements_in_row[0].get_text():
                text_jidla = str(elements_in_row[1])
                for radek in elements_in_row[1].contents:
                    if str(radek) == "<br/>":
                        continue
                    else:
                        text_jidlo = radek.get_text()
                        if "Polévka" in text_jidlo:
                                text_cena = "60"
                        else:
                                text_cena = "165"
                        dic = {"text_jidlo": text_jidlo, "text_cena": text_cena}
                        menu.append(dic)
        logging.debug(menu)
        return menu

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise e

def restaurants_all():
    vsechny_restaurants = {}
    for NAZEV_RESTAURACE, url in seznam_restauraci.items():
        if NAZEV_RESTAURACE == "technicka_menza":
            scraped_technicka_menza = scrape_technicka(get_web(url))
            vsechny_restaurants["Technická menza"] = scraped_technicka_menza
        elif NAZEV_RESTAURACE == "jidlovice":
            scraped_jidlovice = scrape_jidlovice(get_jidlovice_api())
            vsechny_restaurants["Jídlovice Telehouse"] = scraped_jidlovice
        elif NAZEV_RESTAURACE == "restaurant_kulatak":
            scraped_kulatak = scrape_kulatak(get_web(url))
            vsechny_restaurants["Kulaťák"] = scraped_kulatak
        elif NAZEV_RESTAURACE == "jidelna17":
            scraped_jidelna17 = scrape_jidelna17(get_web(url))
            vsechny_restaurants["Jídelna 17"] = scraped_jidelna17
        elif NAZEV_RESTAURACE == "cafe_prostoru":
            scraped_cafe_prostoru = scrape_prostoru(get_web(url))
            vsechny_restaurants["Café Prostoru"] = scraped_cafe_prostoru
    return vsechny_restaurants

if __name__ == "__main__":
    restaurants_all()