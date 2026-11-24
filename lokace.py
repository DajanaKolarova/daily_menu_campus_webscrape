"""Adresy a souřadnice restaurací pro mapu na stránce.

Souřadnice jsou zjištěné jednorázově (OpenStreetMap / Nominatim podle adresy), ať se při
každém načtení stránky nic nevyhledává. Klíč musí být přesně ten název, pod kterým se restaurace
zobrazuje na stránce (viz restaurants_all() v dailymenu_webscrape.py).

Novou restauraci přidáš sem: stačí adresa + lat/lon (např. pravý klik na místo v mapy.cz / Google Maps).
"""

LOKACE = {
    "Technická menza": {"adresa": "Jugoslávských partyzánů 1580/3, Praha 6", "lat": 50.10291, "lon": 14.39455},
    # TODO ověřit: Telehouse = budova Generála Píky 430/26 (alternativa: Wuchterlova 1608/10, lat 50.09797, lon 14.39792)
    "Jídlovice Telehouse": {"adresa": "Generála Píky 430/26, Praha 6", "lat": 50.09880, "lon": 14.38868},
    "Jídelna 17": {"adresa": "Evropská 2690/17, Praha 6", "lat": 50.09991, "lon": 14.38832},
    "Kulaťák": {"adresa": "Vítězné náměstí 820/12, Praha 6", "lat": 50.10049, "lon": 14.39714},
    # TODO ověřit: Café Prostoru sídlí v Národní technické knihovně (Technická 2710/6)
    "Café Prostoru": {"adresa": "Technická 2710/6, Praha 6", "lat": 50.10367, "lon": 14.39058},
    # TODO ověřit: je to menza ve Studentském domě (SÚZ ČVUT), Bílá 2571/6
    "Studentská menza": {"adresa": "Bílá 2571/6, Praha 6", "lat": 50.10575, "lon": 14.38852},
    "U Topolů": {"adresa": "Jugoslávských partyzánů 32, Praha 6", "lat": 50.10685, "lon": 14.39498},
    "Vera Kitchen": {"adresa": "Evropská 2758/11, Praha 6", "lat": 50.10009, "lon": 14.39084},
    # souřadnice z mapy vložené na jejich webu (upetnika.cz); adresu web neuvádí
    "U Pětníka": {"adresa": "Praha 6", "lat": 50.10447, "lon": 14.39369},
    "Na Kotlářce": {"adresa": "Na Kocínce 210/3, Praha 6", "lat": 50.10635, "lon": 14.38681},
}
