# utils/bio_scraper.py

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any

# ------------------------------
# ALBANIAN MONTH MAP
# ------------------------------
AL_MONTHS = {
    "janar": 1, "shkurt": 2, "mars": 3, "prill": 4, "maj": 5, "qershor": 6,
    "korrik": 7, "gusht": 8, "shtator": 9, "tetor": 10, "nëntor": 11, "dhjetor": 12,
    "dhjetorë": 12  # variant
}

EN_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
}

# ------------------------------
# ZODIAC CALCULATOR
# ------------------------------
def get_zodiac_sign(day, month):
    signs = [
        ("Capricorn", (12, 22), (1, 19)), ("Aquarius", (1, 20), (2, 18)),
        ("Pisces", (2, 19), (3, 20)), ("Aries", (3, 21), (4, 19)),
        ("Taurus", (4, 20), (5, 20)), ("Gemini", (5, 21), (6, 20)),
        ("Cancer", (6, 21), (7, 22)), ("Leo", (7, 23), (8, 22)),
        ("Virgo", (8, 23), (9, 22)), ("Libra", (9, 23), (10, 22)),
        ("Scorpio", (10, 23), (11, 21)), ("Sagittarius", (11, 22), (12, 21))
    ]
    for sign, start, end in signs:
        if (month == start[0] and day >= start[1]) or (month == end[0] and day <= end[1]):
            return sign
    return "Unknown"

# ------------------------------
# SAFE REQUEST WRAPPER
# ------------------------------
def safe_get(url: str, retries=3, timeout=6):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout, headers={
                "User-Agent": "NOVARIC-ResearchBot/1.0"
            })
            if response.status_code == 200:
                return response
        except Exception:
            pass
        time.sleep(1.5)
    return None

# ------------------------------
# DATE PARSER (ALBANIAN + ENGLISH)
# ------------------------------
def parse_date(text: str) -> Optional[datetime]:
    text = text.lower().strip()

    # Albanian format: "4 korrik 1964"
    m = re.search(r"(\d{1,2})\s+([a-zëç]+)\s+(\d{4})", text)
    if m:
        day, month_str, year = m.groups()
        if month_str in AL_MONTHS:
            return datetime(int(year), AL_MONTHS[month_str], int(day))

    # English format: "4 July 1964"
    m = re.search(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", text)
    if m:
        day, month_str, year = m.groups()
        if month_str in EN_MONTHS:
            return datetime(int(year), EN_MONTHS[month_str], int(day))

    return None

# ------------------------------
# SCRAPER 1 — SQ WIKIPEDIA
# ------------------------------
def scrape_sq_wikipedia(name: str) -> Optional[datetime]:
    formatted = name.replace(" ", "_")
    url = f"https://sq.wikipedia.org/wiki/{formatted}"
    res = safe_get(url)
    if not res:
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    infobox = soup.find("table", {"class": "infobox"})
    if not infobox:
        return None

    for row in infobox.find_all("tr"):
        header = row.find("th")
        if not header:
            continue
        if "lindur" in header.text.lower() or "datëlindja" in header.text.lower():
            data = row.find("td")
            if data:
                date = parse_date(data.text)
                if date:
                    return date
    return None

# ------------------------------
# SCRAPER 2 — EN WIKIPEDIA (fallback)
# ------------------------------
def scrape_en_wikipedia(name: str) -> Optional[datetime]:
    formatted = name.replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{formatted}"
    res = safe_get(url)
    if not res:
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    bday = soup.find("span", {"class": "bday"})
    if bday:
        try:
            return datetime.strptime(bday.text.strip(), "%Y-%m-%d")
        except:
            pass
    return None

# ------------------------------
# SCRAPER 3 — WIKIDATA API
# ------------------------------
def scrape_wikidata(name: str) -> Optional[datetime]:
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "language": "sq",
        "format": "json",
        "search": name
    }
    res = safe_get(url, timeout=10)
    if not res:
        return None

    data = res.json()
    if "search" not in data or len(data["search"]) == 0:
        return None

    entity_id = data["search"][0]["id"]

    # Get entity details
    res = safe_get(f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json")
    if not res:
        return None

    entity = res.json()
    claims = entity["entities"][entity_id]["claims"]

    if "P569" in claims:  # P569 = date of birth
        dob_raw = claims["P569"][0]["mainsnak"]["datavalue"]["value"]["time"]
        # Format: "+1964-07-04T00:00:00Z"
        try:
            year, month, day = map(int, dob_raw[1:11].split("-"))
            return datetime(year, month, day)
        except:
            return None

    return None

# ------------------------------
# UNIFIED SCRAPER
# ------------------------------
def scrape_profile_data(name: str) -> Dict[str, Any]:
    date = (
        scrape_sq_wikipedia(name)
        or scrape_en_wikipedia(name)
        or scrape_wikidata(name)
    )

    if not date:
        return {"name": name, "found": False, "error": "Birth date not found"}

    today = datetime.now()
    age = today.year - date.year - ((today.month, today.day) < (date.month, date.day))
    zodiac = get_zodiac_sign(date.day, date.month)

    return {
        "name": name,
        "dob": date.strftime("%Y-%m-%d"),
        "age": age,
        "zodiac": zodiac,
        "found": True
    }

# ------------------------------
# CLI EXECUTION
# ------------------------------
if __name__ == "__main__":
    targets = [
        "Edi Rama", "Sali Berisha", "Ilir Meta", "Lulzim Basha",
        "Monika Kryemadhi", "Erion Veliaj", "Belind Këlliçi",
        "Bajram Begaj", "Benet Beci", "Nard Ndoka",
        "Blendi Fevziu", "Grida Duma", "Ardit Gjebrea",
        "Sokol Balla", "Eni Vasili", "Alketa Vejsiu"
    ]
    
    print("🔎 Starting NOVARIC Clinical Bio Extraction")
    print("=" * 70)

    results = {}

    for person in targets:
        print(f"➡ Processing {person} ...")
        data = scrape_profile_data(person)
        results[person] = data
        if data["found"]:
            print(f"   ✔ {data['dob']} | {data['age']} yrs | {data['zodiac']}")
        else:
            print(f"   ⚠ No date found: {data.get('error')}")

    print("=" * 70)
    print("✔ COPY & PASTE INTO TYPESCRIPT:")
    print(results)
