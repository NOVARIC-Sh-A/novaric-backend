# etl/politician_map.py
import unicodedata

# ------------------------------------------------------------
# Albanian-safe name normalization
# ------------------------------------------------------------
def normalize_name(name: str) -> str:
    if not name:
        return ""

    # Normalize Unicode (handles ç, ë, accents, combining chars)
    name = unicodedata.normalize("NFKC", name)

    # Replace non-breaking spaces
    name = name.replace("\u00A0", " ")

    # Lowercase
    name = name.lower().strip()

    # Normalize combining characters for ç
    name = name.replace("ç", "ç")  # c + combining cedilla → ç
    name = name.replace("Ç", "ç")
    name = name.replace("C̨", "ç")

    # Normalize combining characters for ë
    name = name.replace("ë", "ë")
    name = name.replace("Ë", "ë")

    return name


# ------------------------------------------------------------
# 1) OFFICIAL STATIC ID MAP
# ------------------------------------------------------------
POLITICIAN_ID_MAP = {
    "Edi Rama": 1,
    "Sali Berisha": 2,
    "Ilir Meta": 3,
    "Lulzim Basha": 4,
    "Monika Kryemadhi": 5,
    "Erion Veliaj": 6,
    "Belind Këlliçi": 7,
    "Bajram Begaj": 8,
    "Benet Beci": 9,
    "Nard Ndoka": 10,
    "Kliti Hoti": 11,
    "Greta Bardeli": 12,
    "Ramadan Likaj": 13,
    "Bardh Spahia": 14,
    "Marjana Koçeku": 15,
    "Onid Bejleri": 16,
    "Xhenis Çela": 17,
    "Bujar Rexha": 18,
    "Tom Doshi": 19,
    "Sabina Jorgo": 20,
    "Flamur Hoxha": 21,
    "Shkëlqim Shehu": 22,
    "Eduard Shalsi": 23,
    "Elda Hoti": 24,
    "Gjin Gjoni": 25,
    "Kastriot Piroli": 26,
    "Ulsi Manja": 27,
    "Ermal Pacaj": 28,
    "Marjeta Neli": 29,
    "Blendi Klosi": 30,
    "Alma Selami": 31,
    "Agron Malaj": 32,
    "Xhelal Mziu": 33,
    "Denisa Vata": 34,
    "Xhemal Gjunkshi": 35,
    "Përparim Spahiu": 36,
    "Klodiana Spahiu": 37,
    "Milva Ekonomi": 38,
    "Loer Kume": 39,
    "Skënder Pashaj": 40,
    "Aurora Mara": 41,
    "Arkend Balla": 42,
    "Ani Dyrmishi": 43,
    "Ilir Ndraxhi": 44,
    "Oerd Bylykbashi": 45,
    "Artan Luku": 46,
    "Manjola Luku": 47,
    "Gent Strazimiri": 48,
    "Igli Cara": 49,
    "Arian Ndoja": 50,
    "Aulon Kalaja": 51,
    "Arbjan Mazniku": 52,
    "Bora Muzhaqi": 53,
    "Ermal Elezi": 54,
    "Adi Qose": 55,
    "Evis Kushi": 56,
    "Sara Mila": 57,
    "Saimir Hasalla": 58,
    "Olsi Komici": 59,
    "Aulona Bylykbashi": 60,
    "Agron Gaxho": 61,
    "Tomor Alizoti": 62,
    "Edmond Haxhinasto": 63,
    "Klodiana Çapja": 64,
    "Blendi Himçi": 65,
    "Petrit Malaj": 66,
    "Kiduina Zaka": 67,
    "Erjo Mile": 68,
    "Ana Nako": 69,
    "Ceno Klosi": 70,
    "Klevis Jahaj": 71,
    "Asfloral Haxhiu": 72,
    "Antoneta Dhima": 73,
    "Elton Korreshi": 74,
    "Zegjine Çaushi": 75,
    "Dhimitër Kruti": 76,
    "Luan Baçi": 77,
    "Brunilda Haxhiu": 78,
    "Saimir Korreshi": 79,
    "Ervin Demo": 80,
    "Enriketa Jaho": 81,
    "Hysen Buzali": 82,
    "Fadil Nasufi": 83,
    "Julian Zyla": 84,
    "Enno Bozdo": 85,
    "Zija Ismaili": 86,
    "Niko Peleshi": 87,
    "Romina Kuko": 88,
    "Genti Lakollari": 89,
    "Ilirian Pendavinji": 90,
    "Bledi Çomo": 91,
    "Arian Jaupllari": 92,
    "Ivi Kaso": 93,
    "Ledina Allolli": 94,
    "Bledjon Nallbati": 95,
    "Fidel Kreka": 96,
    "Kristjano Koçibelli": 97,
    "Mirela Furxhi": 98,
    "Tërmet Peçi": 99,
    "Piro Dhima": 100,
}


# ------------------------------------------------------------
# 2) RICH METADATA MAP (future-proof for PARAGON)
# ------------------------------------------------------------
POLITICIAN_META = {
    name: {
        "id": pid,
        "full_name": name,
        "photo_url": None,
        "party": None,
        "region": None,
    }
    for name, pid in POLITICIAN_ID_MAP.items()
}


# ------------------------------------------------------------
# 3) NORMALIZED METADATA MAP
# ------------------------------------------------------------
POLITICIAN_META_NORMALIZED = {
    normalize_name(name): meta
    for name, meta in POLITICIAN_META.items()
}

POLITICIAN_ID_MAP_NORMALIZED = {
    normalize_name(name): pid
    for name, pid in POLITICIAN_ID_MAP.items()
}
