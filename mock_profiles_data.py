# mock_profiles_data.py
"""
Centralized mock datasets for seeding and local development.

This file is intentionally "data-first" and safe to import:
- No ETL / Supabase calls
- No side-effects beyond building Python lists/dicts

You should import these from mock_profiles.py, e.g.:
    from mock_profiles_data import (
        POLITICIAN_NAME_TO_ID,
        mock_political_profiles_data,
        mock_media_profiles_data,
        mock_business_profiles_data,
    )

Design notes:
- We keep profile "id" as a string (vip1/mp49/etc.) for app/UI stability.
- We also include "politician_id" as an integer for PARAGON/ETL alignment.
"""

from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Tuple, Union

VipProfile = Dict[str, Any]
ParagonEntry = Dict[str, Any]


# =============================================================================
# 1) POLITICAL: Name -> Integer ID mapping (PARAGON / ETL expects integer IDs)
# =============================================================================

POLITICIAN_NAME_TO_ID: Dict[str, int] = {
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


# =============================================================================
# 2) Utilities (pure helpers, safe to import)
# =============================================================================

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _slugify_name_for_photo(name: str) -> str:
    # Keep it simple and deterministic; upstream can improve later if needed.
    # Removes dots and extra spaces; keeps letters (including Albanian chars).
    return re.sub(r"\s+", "", name.replace(".", "")).strip()


def generate_profile_photo_url(name: str) -> str:
    """
    Deterministic NOVARIC photo URL format.
    Example: "Edi Rama" -> "EdiRAMA.jpg" (based on first + LASTNAME)
    """
    if not name:
        return "https://novaric.co/wp-content/uploads/2025/11/Placeholder.jpg"

    parts = [p for p in name.split(" ") if p]
    last_name = (parts[-1] if parts else "").upper()
    first_name = "".join(parts[:-1]).replace(".", "")
    formatted = f"{_slugify_name_for_photo(first_name)}{_slugify_name_for_photo(last_name)}"
    return f"https://novaric.co/wp-content/uploads/2025/11/{formatted}.jpg"


def generate_random_score(min_val: int = 40, max_val: int = 85) -> int:
    return random.randint(min_val, max_val)


def generate_paragon_analysis(name: str) -> List[ParagonEntry]:
    """Fallback analysis for political profiles."""
    return [
        {
            "dimension": "Policy Engagement & Expertise",
            "score": generate_random_score(),
            "peerAverage": 68,
            "globalBenchmark": 72,
            "description": "Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit; puna në komisione.",
            "commentary": f"Të dhënat për performancën legjislative të {name} do të mblidhen dhe analizohen gjatë mandatit aktual.",
        },
        {
            "dimension": "Accountability & Transparency",
            "score": generate_random_score(),
            "peerAverage": 62,
            "globalBenchmark": 70,
            "description": "Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë.",
            "commentary": f"Transparenca dhe llogaridhënia për {name} do të vlerësohen bazuar në veprimtarinë publike.",
        },
        {
            "dimension": "Representation & Responsiveness",
            "score": generate_random_score(),
            "peerAverage": 70,
            "globalBenchmark": 75,
            "description": "Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave të komunitetit.",
            "commentary": f"Angazhimi i {name} me zonën zgjedhore dhe komunitetin do të monitorohet.",
        },
        {
            "dimension": "Assertiveness & Influence",
            "score": generate_random_score(),
            "peerAverage": 65,
            "globalBenchmark": 68,
            "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
            "commentary": f"Ndikimi politik i {name} do të matet përmes nismave dhe rolit në debatet kyçe.",
        },
        {
            "dimension": "Governance & Institutional Strength",
            "score": generate_random_score(),
            "peerAverage": 67,
            "globalBenchmark": 73,
            "description": "Kontributi në forcimin e institucioneve demokratike dhe sundimit të ligjit.",
            "commentary": f"Veprimtaria e {name} në lidhje me qeverisjen dhe reformat institucionale do të jetë objekt analize.",
        },
        {
            "dimension": "Organizational & Party Cohesion",
            "score": generate_random_score(),
            "peerAverage": 75,
            "globalBenchmark": 78,
            "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
            "commentary": f"Qëndrimet dhe votimet e {name} do të analizohen në raport me linjën zyrtare të partisë.",
        },
        {
            "dimension": "Narrative & Communication",
            "score": generate_random_score(),
            "peerAverage": 71,
            "globalBenchmark": 74,
            "description": "Efektiveti dhe qartësia e komunikimit publik.",
            "commentary": f"Aftësitë komunikuese dhe diskursi publik i {name} do të vlerësohen në vazhdimësi.",
        },
    ]


def generate_maragon_analysis(name: str) -> List[ParagonEntry]:
    """Fallback analysis for media profiles."""
    return [
        {
            "dimension": "Pajtueshmëria Etike",
            "score": generate_random_score(70, 90),
            "peerAverage": 75,
            "globalBenchmark": 92,
            "description": "Pajtueshmëria themelore me standardet etike/operacionale.",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Profesionalizmi në Kriza",
            "score": generate_random_score(70, 90),
            "peerAverage": 78,
            "globalBenchmark": 85,
            "description": "Aftësia për të ruajtur qetësinë dhe standardet profesionale gjatë lajmeve të fundit.",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Saktësia Faktike & Verifikimi",
            "score": generate_random_score(70, 90),
            "peerAverage": 72,
            "globalBenchmark": 88,
            "description": "Rigoroziteti në verifikimin e informacionit para transmetimit.",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Paanshmëria, Balanca & Anshmëria",
            "score": generate_random_score(60, 85),
            "peerAverage": 65,
            "globalBenchmark": 90,
            "description": "Mat aftësinë për të moderuar debatin në mënyrë të paanshme.",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Thellësia e Analizës/Pyetjeve",
            "score": generate_random_score(70, 90),
            "peerAverage": 75,
            "globalBenchmark": 88,
            "description": "Aftësia për të bërë pyetje të thelluara dhe për të ndjekur përgjigjet.",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Qartësia & Koherenca",
            "score": generate_random_score(80, 95),
            "peerAverage": 80,
            "globalBenchmark": 90,
            "description": "Qartësia e të folurit, artikulimi dhe aftësia për të menaxhuar rrjedhën logjike.",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Promovimi i të Menduarit Kritik",
            "score": generate_random_score(65, 85),
            "peerAverage": 70,
            "globalBenchmark": 85,
            "description": "Inkurajimi i audiencës për të konsideruar perspektiva të shumëfishta.",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
    ]


def create_placeholder_political(
    *,
    politician_id: int,
    name: str,
    party: str,
    profile_id_prefix: str = "vip",
) -> VipProfile:
    """
    Creates a minimal political profile that matches the app's expected schema.
    - id: string (vipX)
    - politician_id: int (ETL-aligned)
    """
    return {
        "id": f"{profile_id_prefix}{politician_id}",
        "politician_id": politician_id,
        "name": name,
        "imageUrl": generate_profile_photo_url(name),
        "category": f"Politikë ({party})",
        "shortBio": f"Deputet/e i/e Kuvendit të Shqipërisë, anëtar/e i/e {party}.",
        "detailedBio": (
            f"Informacion i detajuar për {name} do të shtohet së shpejti. "
            "Ky profil është krijuar për zhvillim dhe testim."
        ),
        "zodiacSign": random.choice(ZODIAC_SIGNS),
        "paragonAnalysis": generate_paragon_analysis(name),
    }


# =============================================================================
# 3) Datasets (exported)
# =============================================================================
#
# IMPORTANT:
# - If you have “rich” profile dicts elsewhere, paste them here and keep placeholders
#   only for the remainder.
# - The placeholder party logic below is conservative. Replace with your true parties
#   if you have authoritative data.

# Party overrides for known leaders (optional, extend as needed)
_POLITICAL_PARTY_OVERRIDES: Dict[str, str] = {
    "Edi Rama": "PS",
    "Sali Berisha": "PD",
    "Ilir Meta": "PL",
    "Lulzim Basha": "PD",
    "Monika Kryemadhi": "PL",
    "Erion Veliaj": "PS",
    "Belind Këlliçi": "PD",
    "Bajram Begaj": "President",
    "Benet Beci": "PS",
    "Nard Ndoka": "PDK",
}

# Default party if unknown (replace this with better logic if you have it)
_DEFAULT_PARTY = "Independent"


def build_mock_political_profiles() -> List[VipProfile]:
    """
    Build a stable political dataset using POLITICIAN_NAME_TO_ID.
    Produces placeholder profiles unless you later replace individual entries.
    """
    out: List[VipProfile] = []
    # Stable ordering by politician_id
    for name, pid in sorted(POLITICIAN_NAME_TO_ID.items(), key=lambda x: x[1]):
        party = _POLITICAL_PARTY_OVERRIDES.get(name, _DEFAULT_PARTY)
        out.append(
            create_placeholder_political(
                politician_id=pid,
                name=name,
                party=party,
                profile_id_prefix="vip",
            )
        )
    return out


mock_political_profiles_data: List[VipProfile] = build_mock_political_profiles()


# Media/business datasets can be populated similarly. Keeping them safe defaults.
mock_media_profiles_data: List[VipProfile] = []
mock_business_profiles_data: List[VipProfile] = []


# =============================================================================
# 4) Optional: convenience export of all profiles (data-only, no hydration here)
# =============================================================================

ALL_MOCK_PROFILES: List[VipProfile] = (
    mock_political_profiles_data
    + mock_media_profiles_data
    + mock_business_profiles_data
)
