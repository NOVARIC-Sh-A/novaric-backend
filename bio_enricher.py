import wikipedia
import re
from datetime import datetime

# Install: pip install wikipedia

def get_zodiac_sign(day, month):
    zodiac_map = [
        (120, 'Capricorn'), (218, 'Aquarius'), (320, 'Pisces'), (420, 'Aries'),
        (521, 'Taurus'), (621, 'Gemini'), (722, 'Cancer'), (823, 'Leo'),
        (923, 'Virgo'), (1023, 'Libra'), (1122, 'Scorpio'), (1222, 'Sagittarius'), (1231, 'Capricorn')
    ]
    date_number = int(f"{month}{day:02d}")
    for z_date, sign in zodiac_map:
        if date_number <= z_date:
            return sign
    return 'Capricorn'

def fetch_politician_bio(name):
    print(f"🔍 Searching bio for: {name}...")
    try:
        # 1. Search Wikipedia (English first, fallback could be added)
        page = wikipedia.page(f"{name}")
        content = page.content[:1000] # Read first 1000 chars

        # 2. Regex to find birth date (Format: born 4 July 1964)
        # This is a basic pattern, can be expanded
        match = re.search(r'born\s+(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})', content)
        
        if match:
            day, month_str, year = match.groups()
            dt = datetime.strptime(f"{day} {month_str} {year}", "%d %B %Y")
            
            # Calculate Age
            today = datetime.now()
            age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
            
            # Calculate Zodiac
            zodiac = get_zodiac_sign(dt.day, dt.month)
            
            return {
                "dob": dt.strftime("%Y-%m-%d"),
                "age": age,
                "zodiac": zodiac,
                "summary": page.summary[:200] + "..."
            }
        else:
            print("   ⚠️  Date of birth not found in summary.")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

# Test Run
if __name__ == "__main__":
    profile = fetch_politician_bio("Edi Rama")
    print(profile)
    # Output: {'dob': '1964-07-04', 'age': 60, 'zodiac': 'Cancer', ...}