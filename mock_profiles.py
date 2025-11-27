# mock_profiles.py
# Minimal profile metadata used by the backend.
# Scoring is generated dynamically in main.py

from typing import List, Dict, Any

PROFILES: List[Dict[str, Any]] = [
    {
        "id": "vip1",
        "name": "Edi Rama",
        "category": "Politikë (PS)",
        "type": "political",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/EdiRAMA.jpg",
        "shortBio": "Kryeministër i Shqipërisë, Kryetar i Partisë Socialiste.",
        "detailedBio": "Profil i shkurtër politik. Përshkrimi i plotë mund të zgjerohet më vonë.",
        "zodiacSign": "Cancer",
    },
    {
        "id": "vip2",
        "name": "Sali Berisha",
        "category": "Politikë (PD)",
        "type": "political",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/SaliBERISHA.jpg",
        "shortBio": "Ish-President dhe ish-Kryeministër i Shqipërisë.",
        "detailedBio": "Profil bazë për ish-kryeministrin dhe ish-presidentin.",
        "zodiacSign": "Libra",
    },
    {
        "id": "vip3",
        "name": "Ilir Meta",
        "category": "Politikë (PL)",
        "type": "political",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/IlirMETA.jpg",
        "shortBio": "Kryetar i Partisë së Lirisë, ish-President i Shqipërisë.",
        "detailedBio": "Profil bazë për ish-presidentin dhe liderin e Partisë së Lirisë.",
        "zodiacSign": "Aries",
    },
    {
        "id": "vip4",
        "name": "Blendi Fevziu",
        "category": "Media",
        "type": "media",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/BlendiFEVZIU.jpg",
        "shortBio": "Gazetar dhe drejtues i emisionit 'Opinion' në TV Klan.",
        "detailedBio": "Figurë kryesore në gazetarinë televizive shqiptare.",
        "zodiacSign": "Cancer",
    },
    {
        "id": "vip41",
        "name": "Grida Duma",
        "category": "Media",
        "type": "media",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/GridaDUMA.jpg",
        "shortBio": "Analiste politike dhe drejtuese e emisionit 'Top Story' në Top Channel.",
        "detailedBio": "Ish-politikane e nivelit të lartë, tani figurë qendrore në analizën televizive.",
        "zodiacSign": "Virgo",
    },
    {
        "id": "vip31",
        "name": "Samir Mane",
        "category": "Biznes",
        "type": "business",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/SamirMANE.jpg",
        "shortBio": "President i Grupit BALFIN.",
        "detailedBio": "Një nga sipërmarrësit më të fuqishëm në Shqipëri dhe rajon.",
        "zodiacSign": "Leo",
    },
    {
        "id": "vip33",
        "name": "Dr Alban Gj. THIKA",
        "category": "Politikë & Biznes",
        "type": "business",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/10/NOVARIC_Team-Member_A-THIKA_Small.png",
        "shortBio": (
            "Doctorate-level political and business strategist with over 20 years of "
            "international experience in public administration, enterprise development and "
            "campaign consultancy."
        ),
        "detailedBio": (
            "Kjo është një përmbledhje e shkurtër. Teksti i plotë biografik mund të "
            "marrë versionin nga front-end ose nga një bazë të dhënash në fazat e ardhshme."
        ),
        "zodiacSign": "Capricorn",
    },
]
