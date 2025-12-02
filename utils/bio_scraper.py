# utils/bio_scraper.py
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Albanian Month Mapping
AL_MONTHS = {
    "janar": 1, "shkurt": 2, "mars": 3, "prill": 4, "maj": 5, "qershor": 6,
    "korrik": 7, "gusht": 8, "shtator": 9, "tetor": 10, "nëntor": 11, "dhjetor": 12
}

def get_zodiac_sign(day, month):
    if (month == 3 and day >= 21) or (month == 4 and day <= 19): return "Aries"
    if (month == 4 and day >= 20) or (month == 5 and day <= 20): return "Taurus"
    if (month == 5 and day >= 21) or (month == 6 and day <= 20): return "Gemini"
    if (month == 6 and day >= 21) or (month == 7 and day <= 22): return "Cancer"
    if (month == 7 and day >= 23) or (month == 8 and day <= 22): return "Leo"
    if (month == 8 and day >= 23) or (month == 9 and day <= 22): return "Virgo"
    if (month == 9 and day >= 23) or (month == 10 and day <= 22): return "Libra"
    if (month == 10 and day >= 23) or (month == 11 and day <= 21): return "Scorpio"
    if (month == 11 and day >= 22) or (month == 12 and day <= 21): return "Sagittarius"
    if (month == 12 and day >= 22) or (month == 1 and day <= 19): return "Capricorn"
    if (month == 1 and day >= 20) or (month == 2 and day <= 18): return "Aquarius"
    if (month == 2 and day >= 19) or (month == 3 and day <= 20): return "Pisces"
    return "Unknown"

def scrape_profile_data(name):
    # Format name for Wikipedia URL (e.g., "Edi Rama" -> "Edi_Rama")
    formatted_name = name.replace(" ", "_")
    url = f"https://sq.wikipedia.org/wiki/{formatted_name}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return {"error": "Page not found"}

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find the Infobox (Tabela përmbledhëse)
        infobox = soup.find("table", {"class": "infobox"})
        
        birth_date = None
        
        if infobox:
            # Look for specific keywords in table rows
            for row in infobox.find_all("tr"):
                header = row.find("th")
                if header and ("Lindur" in header.text or "Datëlindja" in header.text):
                    data = row.find("td")
                    if data:
                        # Extract date text (e.g., "4 korrik 1964")
                        # Regex to find: Day Month Year
                        text = data.get_text()
                        match = re.search(r'(\d{1,2})\s+([a-zëç]+)\s+(\d{4})', text, re.IGNORECASE)
                        if match:
                            day, month_str, year = match.groups()
                            month = AL_MONTHS.get(month_str.lower())
                            if month:
                                birth_date = datetime(int(year), month, int(day))
                                break
        
        if not birth_date:
            # Fallback: Try searching the first paragraph
            first_p = soup.find('p')
            if first_p:
                text = first_p.get_text()
                match = re.search(r'(\d{1,2})\s+([a-zëç]+)\s+(\d{4})', text, re.IGNORECASE)
                if match:
                    day, month_str, year = match.groups()
                    month = AL_MONTHS.get(month_str.lower())
                    if month:
                        birth_date = datetime(int(year), month, int(day))

        if birth_date:
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            zodiac = get_zodiac_sign(birth_date.day, birth_date.month)
            
            return {
                "name": name,
                "dob": birth_date.strftime("%Y-%m-%d"),
                "age": age,
                "zodiac": zodiac,
                "found": True
            }
        else:
            return {"name": name, "found": False, "error": "Date not parsed"}

    except Exception as e:
        return {"name": name, "found": False, "error": str(e)}

# --- EXECUTION ---
if __name__ == "__main__":
    # List of names from your mockVipProfiles.ts
    targets = [
        "Edi Rama", "Sali Berisha", "Ilir Meta", "Lulzim Basha", 
        "Monika Kryemadhi", "Erion Veliaj", "Belind Këlliçi", 
        "Bajram Begaj", "Benet Beci", "Nard Ndoka",
        "Blendi Fevziu", "Grida Duma", "Ardit Gjebrea", 
        "Sokol Balla", "Eni Vasili", "Alketa Vejsiu"
    ]
    
    print("🔎 Starting Clinical Data Extraction from Wikipedia...")
    print("-" * 60)
    
    results = {}
    
    for target in targets:
        data = scrape_profile_data(target)
        if data.get("found"):
            print(f"✅ {target}: {data['age']} years old | {data['zodiac']} | {data['dob']}")
            results[target] = data
        else:
            print(f"⚠️ {target}: Could not find/parse date.")

    print("-" * 60)
    print("COPY THIS OBJECT INTO YOUR TYPESCRIPT FILE:")
    print(results)
