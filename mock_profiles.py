# mock_profiles.py
import random
import logging
from typing import Any, Dict, List, Union

# Type aliases
VipProfile = Dict[str, Any]
ParagonEntry = Dict[str, Any]

# =====================================================================================
# ARCHITECTURE IMPORTS: The "Bridge" to the New PARAGON Engine
# =====================================================================================
try:
    # NEW engine paths
    from etl.metric_loader import load_metrics_for
    from etl.scoring_engine import score_metrics

    print("✅ PARAGON System: New loader + scoring engine active.")
    ENGINE_AVAILABLE = True

    # Load all metric bundles for every politician ID (optional, can stay empty)
    RAW_EVIDENCE: Dict[str, Any] = {}

    # Example: preload for IDs that exist in the mock dataset
    # We dynamically detect IDs in the profiles later at hydration time,
    # so here we only set up the container.
except ImportError:
    print("⚠️ PARAGON System: Engine files not found. Running in Offline Mode.")
    ENGINE_AVAILABLE = False
    RAW_EVIDENCE = {}
except Exception as e:
    print(f"⚠️ PARAGON System: Error loading metrics: {e}")
    ENGINE_AVAILABLE = False
    RAW_EVIDENCE = {}

# =====================================================================================
# HELPER GENERATORS
# =====================================================================================

def generate_profile_photo_url(name: str) -> str:
    """
    Build a deterministic photo URL for a given name based on the NOVARIC format.
    """
    if not name:
        return "https://novaric.co/wp-content/uploads/2025/11/Placeholder.jpg"
    
    parts = name.split(" ")
    last_name = (parts.pop() or "").upper()
    # Remove special chars from first name (like 'Gj.')
    first_name = "".join(parts).replace(".", "")
    
    formatted_name = f"{first_name}{last_name}"
    return f"https://novaric.co/wp-content/uploads/2025/11/{formatted_name}.jpg"


def generate_random_score(min_val: int = 40, max_val: int = 85) -> int:
    return random.randint(min_val, max_val)


# --- FALLBACK GENERATORS ---
# These function are used only if specific hardcoded data is missing 
# AND real engine data is unavailable.

def generate_paragon_analysis(name: str) -> List[ParagonEntry]:
    """Generates generic Political analysis."""
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
    """Generates generic Media analysis."""
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


ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def create_placeholder_mp(mp_id: Union[str, int], name: str, party: str) -> VipProfile:
    """Helper to generate generic MPs."""
    return {
        "id": mp_id,
        "name": name,
        "imageUrl": generate_profile_photo_url(name),
        "category": f"Politikë ({party})",
        "shortBio": f"Deputet/e i/e Kuvendit të Shqipërisë, anëtar/e i/e {party}.",
        "detailedBio": f"""Informacion i detajuar për {name} do të shtohet së shpejti. Ky profil
është krijuar për të paraqitur veprimtarinë parlamentare dhe publike të deputetit/es
në kuadër të legjislaturës 2025.""",
        "paragonAnalysis": generate_paragon_analysis(name),
        "zodiacSign": random.choice(ZODIAC_SIGNS),
    }


# =====================================================================================
# 1. POLITICAL PROFILES
# =====================================================================================

mock_political_profiles_data: List[VipProfile] = [
    {
        "id": "vip1",
        "name": "Edi Rama",
        "imageUrl": generate_profile_photo_url("Edi Rama"),
        "category": "Politikë (PS)",
        "shortBio": "Kryeministër i Shqipërisë, Kryetar i Partisë Socialiste.",
        "detailedBio": """Edi Rama (lindur më 4 korrik 1964) është një politikan, piktor dhe publicist
shqiptar, Kryeministër i Shqipërisë dhe Kryetar i Partisë Socialiste. Më parë ka
shërbyer si Ministër i Kulturës, Rinisë dhe Sporteve (1998-2000) dhe si Kryetar i
Bashkisë së Tiranës (2000-2011). Si kryebashkiak, ai transformoi pamjen e qytetit
me projekte rigjallëruese urbane. Udhëheqja e tij si kryeministër është fokusuar në
reformat strukturore, integrimin evropian dhe modernizimin e vendit.""",
        "zodiacSign": "Cancer",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 85,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit; puna në komisione.",
                "commentary": "Shquhet për projekte transformuese afatgjata si Rilindja Urbane, por kritikohet për mungesë konsultimi dhe kosto të lartë (PPP).",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 45,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": "Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë.",
                "commentary": "Qeverisja e tij është përballur me akuza të vazhdueshme për korrupsion, kapje të shtetit dhe mungesë transparence.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 60,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave të komunitetit.",
                "commentary": "Kritikohet për një qasje 'nga lart-poshtë' dhe për mungesë të theksuar të dialogut me grupet e interesit.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 95,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
                "commentary": "Ka një kontroll pothuajse absolut mbi Partinë Socialiste, duke qenë figura qendrore dhe vendimmarrësi i padiskutueshëm.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 65,
                "peerAverage": 60,
                "globalBenchmark": 68,
                "description": "Kontributi në forcimin e institucioneve demokratike dhe sundimit të ligjit.",
                "commentary": "Ka mbikëqyrur reforma të rëndësishme si ajo në drejtësi, por njëkohësisht akuzohet për centralizim të pushtetit.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 92,
                "peerAverage": 80,
                "globalBenchmark": 82,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": "Ruan një kohezion të fortë brenda grupit parlamentar dhe partisë, shpesh përmes një lidershipi autoritar.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 90,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": "Komunikues i jashtëzakonshëm dhe karizmatik, përdor median sociale dhe daljet publike në mënyrë efektive, por stili mund të jetë polarizues.",
            },
        ],
    },
    {
        "id": "vip2",
        "name": "Sali Berisha",
        "imageUrl": generate_profile_photo_url("Sali Berisha"),
        "category": "Politikë (PD)",
        "shortBio": "Ish-President dhe ish-Kryeministër, figurë historike e Partisë Demokratike.",
        "detailedBio": """Sali Berisha (lindur më 15 tetor 1944) është një kardiolog dhe politikan
shqiptar, i cili ka shërbyer si Presidenti i dytë i Shqipërisë (1992-1997) dhe si
Kryeministër (2005-2013). Ai ka qenë lideri i Partisë Demokratike të Shqipërisë për
dy dekada dhe mbetet një figurë me ndikim të madh në politikën shqiptare.""",
        "zodiacSign": "Libra",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 60,
                "peerAverage": 72,
                "globalBenchmark": 70,
                "description": "Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit.",
                "commentary": "Aktiviteti i tij parlamentar është i kufizuar, duke u fokusuar kryesisht në fjalime politike nga ballkoni dhe media sociale.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 30,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": "Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë.",
                "commentary": "Nën arrest shtëpie dhe përballet me akuza serioze për korrupsion nga SPAK, gjë që ka dëmtuar rëndë perceptimin e tij publik.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 70,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": "Cilësia e lidhjes me zonën zgjedhore.",
                "commentary": "Ruan një lidhje të fortë me bazën e tij historike mbështetëse, por ka vështirësi të arrijë audienca më të gjera.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 88,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": "Pavarësisht sfidave ligjore dhe politike, ai ruan një ndikim masiv dhe kontroll të fortë mbi grupimin e tij në PD.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 35,
                "peerAverage": 65,
                "globalBenchmark": 72,
                "description": "Kontributi në forcimin e institucioneve demokratike.",
                "commentary": "I shpallur 'non grata' nga SHBA dhe MB, gjë që e ka izoluar nga partnerët perëndimorë kyç.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 45,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": "Figura e tij është njëkohësisht bashkuese për ndjekësit e tij dhe thellësisht përçarëse për Partinë Demokratike.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 80,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": "Mbetet një orator i fuqishëm me aftësi për të mobilizuar mbështetësit e tij më besnikë, edhe pse retorika është konfrontuese.",
            },
        ],
    },
    {
        "id": "vip3",
        "name": "Ilir Meta",
        "imageUrl": generate_profile_photo_url("Ilir Meta"),
        "category": "Politikë (PL)",
        "shortBio": "Kryetar i Partisë së Lirisë, ish-President i Shqipërisë.",
        "detailedBio": """Ilir Meta (lindur më 24 mars 1969) është një politikan shqiptar, aktualisht
Kryetar i Partisë së Lirisë (ish-LSI). Ai ka mbajtur poste të larta shtetërore,
duke përfshirë Kryeministër, Kryetar Kuvendi dhe President. Njihet si 'kingmaker'
në skenën politike shqiptare.""",
        "zodiacSign": "Aries",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 55,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit.",
                "commentary": "Njihet më shumë si strateg takticien afatshkurtër për maksimizimin e pushtetit sesa si vizionar afatgjatë.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 35,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": "Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë.",
                "commentary": "Përballet me akuza të vazhdueshme për korrupsion dhe pasuri të pajustifikuar, intensifikuar nga hetimet e SPAK.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 68,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Cilësia e lidhjes me zonën zgjedhore.",
                "commentary": "Ka një aftësi të spikatur për të ndërtuar marrëdhënie klienteliste në nivel lokal.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 92,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": "Ka kontroll absolut mbi Partinë e Lirisë, duke qenë figura dominuese dhe vendimmarrësi kryesor.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 62,
                "peerAverage": 60,
                "globalBenchmark": 68,
                "description": "Kontributi në forcimin e institucioneve demokratike.",
                "commentary": "Mandati si President u shoqërua me përplasje institucionale. Veprimet e fundit kanë tensionuar marrëdhëniet ndërkombëtare.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 90,
                "peerAverage": 80,
                "globalBenchmark": 82,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": "Ruan kontroll të hekurt mbi strukturat e partisë, duke siguruar unitet të brendshëm.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 75,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": "Komunikimi është bërë gjithnjë e më i paparashikueshëm, emocional dhe shpërthyes.",
            },
        ],
    },
    {
        "id": "vip6",
        "name": "Lulzim Basha",
        "imageUrl": generate_profile_photo_url("Lulzim Basha"),
        "category": "Politikë (PD)",
        "shortBio": "Ish-Kryetar i Partisë Demokratike, deputet.",
        "detailedBio": """Lulzim Basha është një politikan shqiptar, i cili ka shërbyer si Kryetar i
Partisë Demokratike nga viti 2013 deri në 2022. Ka mbajtur poste të rëndësishme
ministrore (Jashtëm, Brendshëm) dhe ka qenë Kryetar i Bashkisë Tiranë.""",
        "zodiacSign": "Taurus",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 65,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit.",
                "commentary": "Shpesh është kritikuar për mungesë të një vizioni të qartë, duke reaguar më shumë ndaj zhvillimeve ditore.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 60,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": "Llogaridhënia ndaj publikut.",
                "commentary": "Nuk është përballur me akuza të mëdha korrupsioni personalisht, por kritikohet për menaxhimin e partisë.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 62,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": "Cilësia e lidhjes me zonën zgjedhore.",
                "commentary": "Ka marrëdhënie të mira ndërkombëtare, por kjo nuk përkthehet gjithmonë në mbështetje elektorale.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 50,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": "Ka humbur ndjeshëm ndikimin mbi PD, duke çuar në përçarje dhe izolim.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 70,
                "peerAverage": 65,
                "globalBenchmark": 72,
                "description": "Kontributi në forcimin e institucioneve demokratike.",
                "commentary": "Si ministër ka kontribuar në procese si liberalizimi i vizave, duke treguar aftësi pro-institucionale.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 40,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": "Lidershipi i tij çoi në përçarjen më të madhe në historinë e PD.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 70,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": "Komunikon në mënyrë të qetë dhe të strukturuar, por i mungon karizma mobilizuese.",
            },
        ],
    },
    {
        "id": "vip7",
        "name": "Monika Kryemadhi",
        "imageUrl": generate_profile_photo_url("Monika Kryemadhi"),
        "category": "Politikë (PL)",
        "shortBio": "Deputete, figurë drejtuese në Partinë e Lirisë.",
        "detailedBio": """Monika Kryemadhi është një politikane shqiptare, ish-kryetare e Lëvizjes
Socialiste për Integrim (tani Partia e Lirisë). Aktive në politikë që nga vitet '90,
ajo njihet si një zë i fuqishëm dhe energjik.""",
        "zodiacSign": "Gemini",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 58,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit.",
                "commentary": "Fokusi i saj ka qenë kryesisht organizimi i partisë dhe strategjitë elektorale.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 42,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": "Llogaridhënia ndaj publikut.",
                "commentary": "Përballet me akuza për pasuri të pajustifikuar dhe korrupsion, gjë që dëmton imazhin publik.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 75,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": "Cilësia e lidhjes me zonën zgjedhore.",
                "commentary": "Njihet për lidhje të fortë me bazën dhe aftësi mobilizimi në terren.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 85,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": "Ruan ndikim shumë të fortë brenda strukturave të Partisë së Lirisë.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 60,
                "peerAverage": 65,
                "globalBenchmark": 72,
                "description": "Kontributi në forcimin e institucioneve demokratike.",
                "commentary": "Nuk ka pasur rol direkt në menaxhimin ekonomik, por partia ka ndikuar në politika qeverisëse.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 88,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": "Ka treguar aftësi të larta organizative dhe kontroll të fortë mbi strukturat.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 82,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": "Komunikuese energjike dhe e drejtpërdrejtë, stili mund të jetë polarizues.",
            },
        ],
    },
    {
        "id": "vip8",
        "name": "Erion Veliaj",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/ErionVELIAJ.jpg",
        "category": "Politikë (PS)",
        "shortBio": "Kryetar i Bashkisë së Tiranës.",
        "detailedBio": """Erion Veliaj është Kryetar i Bashkisë së Tiranës që nga viti 2015. Më parë
ka shërbyer si Ministër i Mirëqenies Sociale. Njihet për projektet urbane në Tiranë
dhe iniciativat sociale.""",
        "zodiacSign": "Leo",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 82,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit.",
                "commentary": "Ka vizion të qartë për transformimin urban, por kritikohet për betonizim.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 40,
                "peerAverage": 58,
                "globalBenchmark": 65,
                "description": "Llogaridhënia ndaj publikut.",
                "commentary": "Administrata është përballur me skandale (5D, inceneratorët) dhe akuza për korrupsion.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 65,
                "peerAverage": 68,
                "globalBenchmark": 75,
                "description": "Cilësia e lidhjes me zonën zgjedhore.",
                "commentary": "Organizon takime të shpeshta, por akuzohet se injoron zërat kritikë dhe shoqërinë civile.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 85,
                "peerAverage": 80,
                "globalBenchmark": 82,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": "Ka ndikim të konsiderueshëm brenda PS dhe aftësi për të çuar përpara projekte madhore.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 75,
                "peerAverage": 70,
                "globalBenchmark": 72,
                "description": "Kontributi në forcimin e institucioneve demokratike.",
                "commentary": "Efikas në realizimin e projekteve, por kritikohet për mungesë transparence në tenderë.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 80,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": "Pozicionohet si besnik i lidershipit qendror, duke siguruar mbështetje politike.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 88,
                "peerAverage": 80,
                "globalBenchmark": 82,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": "Shumë i aftë në marketing politik, përdor intensivisht median sociale.",
            },
        ],
    },
    {
        "id": "vip29",
        "name": "Belind Këlliçi",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/BelindKELLICI.jpg",
        "category": "Politikë (PD)",
        "shortBio": "Deputet i Partisë Demokratike dhe figurë e re politike.",
        "detailedBio": """Belind Këlliçi është një figurë e re dhe energjike në PD. I njohur për
denoncimet publike lidhur me korrupsionin dhe abuzimet me pushtetin, veçanërisht
në nivel vendor. Zë kryesor i brezit të ri në opozitë.""",
        "zodiacSign": "Virgo",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 68,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Pjesëmarrja në hartimin e legjislacionit.",
                "commentary": "Fokusi kryesor është denoncimi dhe mbikëqyrja, veçanërisht në korrupsionin urban.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 85,
                "peerAverage": 60,
                "globalBenchmark": 75,
                "description": "Llogaridhënia ndaj publikut.",
                "commentary": "Zë i fortë për transparencë, luan rol aktiv si 'watchdog' i opozitës.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 75,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": "Lidhja me zonën zgjedhore.",
                "commentary": "Aktiv në media dhe takime me bazën, artikulon shqetësimet e tyre.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 82,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": "Ka vendosur tema kyçe të korrupsionit në axhendën publike.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 60,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Kontributi në forcimin e institucioneve demokratike.",
                "commentary": "Fokusuar në sfidimin e qeverisjes aktuale.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 70,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Roli në ruajtjen e unitetit partiak.",
                "commentary": "Figurë e rëndësishme në opozitë, por vepron në një parti të përçarë.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 88,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": "Komunikues i mprehtë, përdor prova dhe retorikë të fortë.",
            },
        ],
    },
    {
        "id": "vip30",
        "name": "Bajram Begaj",
        "imageUrl": generate_profile_photo_url("Bajram Begaj"),
        "category": "Politikë (President)",
        "shortBio": "President i Republikës së Shqipërisë.",
        "detailedBio": """Bajram Begaj është Presidenti aktual. Ish-Shef i Shtabit të Përgjithshëm me
karrierë të gjatë ushtarake dhe mjekësore. Roli i tij është përfaqësimi i unitetit
kombëtar dhe garantimi i Kushtetutës.""",
        "zodiacSign": "Pisces",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 55,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Roli në hartimin e politikave.",
                "commentary": "I kufizuar nga Kushtetuta; përdor ekspertizën institucionale në ushtrimin e detyrës.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 80,
                "peerAverage": 70,
                "globalBenchmark": 80,
                "description": "Llogaridhënia ndaj publikut.",
                "commentary": "Institucioni ruan transparencë të lartë formale; veprimtaria është publike.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 70,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Përfaqësimi i unitetit të kombit.",
                "commentary": "Ka qenë i përgjegjshëm ndaj detyrimeve kushtetuese dhe përfaqësimit ndërkombëtar.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 65,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": "Ndikim kryesisht institucional (dekrete). Nuk ka ndikim të fortë në debatin politik.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 85,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Kontributi në forcimin e institucioneve.",
                "commentary": "Garant i Kushtetutës. Ka mbajtur qëndrim stabil dhe pro-institucional.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 75,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli si figurë unifikuese.",
                "commentary": "Qëndron mbi palët politike për të ruajtur unitetin kombëtar.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 68,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": "Stili është formal, institucional dhe i përmbajtur; zë i matur i shtetit.",
            },
        ],
    },
    {
        "id": "mp19",
        "name": "Benet Beci",
        "imageUrl": generate_profile_photo_url("Benet Beci"),
        "category": "Politikë (PS)",
        "shortBio": "Kryetar i Bashkisë Shkodër, inxhinier dhe ish-deputet.",
        "detailedBio": """Benet Beci, Kryetar i Bashkisë Shkodër, ka drejtuar gjatë Fondin Shqiptar
të Zhvillimit (FSHZH). Udhëheqja e tij fokusohet në zhvillimin urban, shërbimet
publike dhe turizmin.""",
        "zodiacSign": "Aries",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 85,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Ekspertiza teknike dhe pjesëmarrja në politika.",
                "commentary": "Përvoja në menaxhimin e projekteve infrastrukturore i jep ekspertizë të thellë teknike.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 70,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Llogaridhënia ndaj publikut.",
                "commentary": "Imazh relativisht i pastër, por transparenca në bashki mbetet test.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 82,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Cilësia e lidhjes me komunitetin.",
                "commentary": "Qasje e hapur ndaj bashkëpunimit, fokus në projekte me impakt lokal.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 88,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Ndikimi në axhendën politike.",
                "commentary": "Marrëdhënie e mirë me qeverinë qendrore siguron fonde për projektet.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 85,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Kontributi në forcimin institucional.",
                "commentary": "Avantazh në menaxhimin administrativ dhe zbatimin efikas të projekteve.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 78,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në unitetin partiak.",
                "commentary": "Besnik me partinë, por kjo mund të kufizojë pavarësinë.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 75,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Komunikimi publik.",
                "commentary": "Komunikues i matur dhe teknik, fokusuar te rezultatet konkrete.",
            },
        ],
    },
    {
        "id": "vip_nn",
        "name": "Nard Ndoka",
        "imageUrl": generate_profile_photo_url("Nard Ndoka"),
        "category": "Politikë (PDK)",
        "shortBio": "Kryetar i Partisë Demokristiane, ish-ministër.",
        "detailedBio": """Nard Ndoka është themelues dhe kryetar i PDK. Ka qenë Ministër i Shëndetësisë.
I njohur për stilin e drejtpërdrejtë dhe satirik, është figurë me prani të lartë
mediatike.""",
        "zodiacSign": "Libra",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 55,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Ekspertiza dhe angazhimi politik.",
                "commentary": "Fokusi te komentimi politik dhe denoncimi, më pak te politikat specifike.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 65,
                "peerAverage": 62,
                "globalBenchmark": 70,
                "description": "Llogaridhënia dhe transparenca.",
                "commentary": "Profil relativisht i pastër nga afera të mëdha korruptive.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 80,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Lidhja me zonën zgjedhore.",
                "commentary": "Lidhje e fortë historike me zonën në Veri, artikulon shqetësimet e komunitetit.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 70,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": "Ndikimi politik.",
                "commentary": "Ndikim legjislativ i kufizuar, por ndikim i konsiderueshëm mediatik.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 50,
                "peerAverage": 67,
                "globalBenchmark": 73,
                "description": "Forcimi institucional.",
                "commentary": "Kritik ndaj institucioneve, kontribut modest në forcimin e tyre.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 85,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Uniteti partiak.",
                "commentary": "Kontroll i plotë dhe kohezion i lartë brenda PDK.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 90,
                "peerAverage": 71,
                "globalBenchmark": 74,
                "description": "Komunikimi publik.",
                "commentary": "Stil unik, i drejtpërdrejtë dhe shpesh viral; pika e tij më e fortë.",
            },
        ],
    },
]

# Placeholder MPs loop
_PLACEHOLDER_MPS = [
    ("mp49", "Kliti Hoti", "PD-ASHM"), ("mp50", "Greta Bardeli", "PD-ASHM"),
    ("mp51", "Ramadan Likaj", "PD-ASHM"), ("mp52", "Bardh Spahia", "PD-ASHM"),
    ("mp53", "Marjana Koçeku", "PS"), ("mp54", "Onid Bejleri", "PS"),
    ("mp55", "Xhenis Çela", "PS"), ("mp56", "Bujar Rexha", "PS"),
    ("mp57", "Tom Doshi", "PSD"), ("mp58", "Sabina Jorgo", "PSD"),
    ("mp59", "Flamur Hoxha", "PD-ASHM"), ("mp60", "Shkëlqim Shehu", "PD-ASHM"),
    ("mp61", "Eduard Shalsi", "PS"), ("mp62", "Elda Hoti", "PD-ASHM"),
    ("mp63", "Gjin Gjoni", "PD-ASHM"), ("mp64", "Kastriot Piroli", "PD-ASHM"),
    ("mp65", "Ulsi Manja", "PS"), ("mp66", "Ermal Pacaj", "PS"),
    ("mp67", "Marjeta Neli", "PS"), ("mp68", "Blendi Klosi", "PS"),
    ("mp69", "Alma Selami", "PS"), ("mp70", "Agron Malaj", "PS"),
    ("mp71", "Xhelal Mziu", "PD-ASHM"), ("mp72", "Denisa Vata", "PD-ASHM"),
    ("mp73", "Xhemal Gjunkshi", "PD-ASHM"), ("mp74", "Përparim Spahiu", "PD-ASHM"),
    ("mp75", "Klodiana Spahiu", "PS"), ("mp76", "Milva Ekonomi", "PS"),
    ("mp77", "Loer Kume", "PS"), ("mp78", "Skënder Pashaj", "PS"),
    ("mp79", "Aurora Mara", "PS"), ("mp80", "Arkend Balla", "PS"),
    ("mp81", "Ani Dyrmishi", "PS"), ("mp82", "Ilir Ndraxhi", "PS"),
    ("mp83", "Oerd Bylykbashi", "PD-ASHM"), ("mp84", "Artan Luku", "PD-ASHM"),
    ("mp85", "Manjola Luku", "PD-ASHM"), ("mp86", "Gent Strazimiri", "PD-ASHM"),
    ("mp87", "Igli Cara", "PD-ASHM"), ("mp88", "Arian Ndoja", "PD-ASHM"),
    ("mp89", "Aulon Kalaja", "PD-ASHM"), ("mp90", "Arbjan Mazniku", "PS"),
    ("mp91", "Bora Muzhaqi", "PS"), ("mp92", "Ermal Elezi", "PS"),
    ("mp93", "Adi Qose", "PS"), ("mp94", "Evis Kushi", "PS"),
    ("mp95", "Sara Mila", "PS"), ("mp96", "Saimir Hasalla", "PS"),
    ("mp97", "Olsi Komici", "PS"), ("mp98", "Aulona Bylykbashi", "PS"),
    ("mp99", "Agron Gaxho", "PS"), ("mp100", "Tomor Alizoti", "PD-ASHM"),
    ("mp101", "Edmond Haxhinasto", "PD-ASHM"), ("mp102", "Klodiana Çapja", "PD-ASHM"),
    ("mp103", "Blendi Himçi", "PD-ASHM"), ("mp104", "Petrit Malaj", "PS"),
    ("mp105", "Kiduina Zaka", "PS"), ("mp106", "Erjo Mile", "PS"),
    ("mp107", "Ana Nako", "PS"), ("mp108", "Ceno Klosi", "PS"),
    ("mp109", "Klevis Jahaj", "PS"), ("mp110", "Asfloral Haxhiu", "PS"),
    ("mp111", "Antoneta Dhima", "PS"), ("mp112", "Elton Korreshi", "PS"),
    ("mp113", "Zegjine Çaushi", "PS"), ("mp114", "Dhimitër Kruti", "PS"),
    ("mp115", "Luan Baçi", "PD-ASHM"), ("mp116", "Brunilda Haxhiu", "PD-ASHM"),
    ("mp117", "Saimir Korreshi", "PD-ASHM"), ("mp118", "Ervin Demo", "PS"),
    ("mp119", "Enriketa Jaho", "PS"), ("mp120", "Hysen Buzali", "PS"),
    ("mp121", "Fadil Nasufi", "PS"), ("mp122", "Julian Zyla", "PS"),
    ("mp123", "Enno Bozdo", "PD-ASHM"), ("mp124", "Zija Ismaili", "PD-ASHM"),
    ("mp125", "Niko Peleshi", "PS"), ("mp126", "Romina Kuko", "PS"),
    ("mp127", "Genti Lakollari", "PS"), ("mp128", "Ilirian Pendavinji", "PS"),
    ("mp129", "Bledi Çomo", "PS"), ("mp130", "Arian Jaupllari", "PS"),
    ("mp131", "Ivi Kaso", "PD-ASHM"), ("mp132", "Ledina Allolli", "PD-ASHM"),
    ("mp133", "Bledjon Nallbati", "PD-ASHM"), ("mp134", "Fidel Kreka", "PD-ASHM"),
    ("mp135", "Kristjano Koçibelli", "PD-ASHM"), ("mp136", "Mirela Furxhi", "PS"),
    ("mp137", "Tërmet Peçi", "PS"), ("mp138", "Piro Dhima", "PS"),
    ("mp139", "Tritan Shehu", "PD-ASHM"), ("mp140", "Bledar Çuçi", "PS"),
    ("mp141", "Zamira Sinaj", "PS"), ("mp142", "Erjona Ismaili", "PS"),
    ("mp143", "Pirro Vengu", "PS"), ("mp144", "Damian Gjiknuri", "PS"),
    ("mp145", "Vullnet Sinaj", "PS"), ("mp146", "Ardit Bido", "PS"),
    ("mp147", "Vasil Llajo", "PS"), ("mp148", "Brunilda Mersini", "PS"),
    ("mp149", "Bujar Leskaj", "PD-ASHM"), ("mp150", "Vangjel Dule", "PD-ASHM"),
    ("mp151", "Ina Zhupa", "PD-ASHM"), ("mp152", "Ogerta Manastirliu", "PS"),
    ("mp153", "Elisa Spiropali", "PS"), ("mp154", "Adea Pirdeni", "PS"),
    ("mp155", "Albana Kociu", "PS"), ("mp156", "Igli Hasani", "PS"),
    ("mp157", "Delina Ibrahimaj", "PS"), ("mp158", "Ilva Gjuzi", "PS"),
    ("mp159", "Iris Luarasi", "PS"), ("mp160", "Erjon Malaj", "PS"),
    ("mp161", "Blendi Gonxhja", "PS"), ("mp162", "Ervin Hoxha", "PS"),
    ("mp163", "Erion Braçe", "PS"), ("mp164", "Fatmir Xhafaj", "PS"),
    ("mp165", "Ornaldo Rakipi", "PS"), ("mp166", "Xhemal Qefalia", "PS"),
    ("mp167", "Anila Denaj", "PS"), ("mp168", "Edi Paloka", "PD-ASHM"),
    ("mp169", "Albana Vokshi", "PD-ASHM"), ("mp170", "Flamur Noka", "PD-ASHM"),
    ("mp171", "Jozefina Topalli", "PD-ASHM"), ("mp172", "Besart Xhaferri", "PD-ASHM"),
    ("mp173", "Fatmir Mediu", "PD-ASHM"), ("mp174", "Erisa Xhixho", "PD-ASHM"),
    ("mp175", "Klevis Balliu", "PD-ASHM"), ("mp176", "Mesila Doda", "PD-ASHM"),
    ("mp177", "Tedi Blushi", "PD-ASHM"), ("mp178", "Ilir Alimehmeti", "PD-ASHM"),
    ("mp179", "Agron Shehaj", "Partia Mundësia"),
    ("mp180", "Erald Kapri", "Partia Mundësia"),
    ("mp181", "Redi Muçi", "Lëvizja BASHKË"),
    ("mp182", "Ana Dajko", "Nisma “Shqipëria Bëhet”"),
    ("mp183", "Alban Pëllumbi", "PSD"),
]

for _mp_id, _name, _party in _PLACEHOLDER_MPS:
    mock_political_profiles_data.append(create_placeholder_mp(_mp_id, _name, _party))


# =====================================================================================
# 2. MEDIA & OTHER PROFILES (MARAGON)
# =====================================================================================

mock_media_profiles_data: List[VipProfile] = [
    {
        "id": "vip4",
        "name": "Blendi Fevziu",
        "imageUrl": generate_profile_photo_url("Blendi Fevziu"),
        "category": "Media",
        "shortBio": "Gazetar dhe drejtues i emisionit 'Opinion' në TV Klan.",
        "detailedBio": """Blendi Fevziu është një nga gazetarët dhe opinionistët më të njohur në Shqipëri.
Ai drejton emisionin politik 'Opinion', ndër më të ndjekurit në vend. Autor i librave historikë
dhe biografikë. Njihet për stilin direkt dhe moderimin e debateve të nxehta.""",
        "zodiacSign": "Cancer",
        "maragonAnalysis": [
            {
                "dimension": "Pajtueshmëria Etike",
                "score": 88,
                "peerAverage": 75,
                "globalBenchmark": 92,
                "description": "Pajtueshmëria themelore me standardet etike/operacionale.",
                "commentary": "Ruan reputacion të fortë etik, duke mbajtur emisionin larg skandaleve të mëdha.",
            },
            {
                "dimension": "Profesionalizmi në Kriza",
                "score": 85,
                "peerAverage": 78,
                "globalBenchmark": 85,
                "description": "Aftësia për të ruajtur qetësinë dhe standardet profesionale gjatë krizave.",
                "commentary": "Përvojë në menaxhimin e situatave live me tension të lartë.",
            },
            {
                "dimension": "Saktësia Faktike & Verifikimi",
                "score": 85,
                "peerAverage": 72,
                "globalBenchmark": 88,
                "description": "Rigoroziteti në verifikimin e informacionit.",
                "commentary": "Përgatitje e lartë, por shpejtësia live lejon pasaktësi të vogla.",
            },
            {
                "dimension": "Paanshmëria, Balanca & Anshmëria",
                "score": 78,
                "peerAverage": 65,
                "globalBenchmark": 90,
                "description": "Moderimi i paanshëm.",
                "commentary": "Synon paanshmëri, por stili konfrontues mund të perceptohet si favorizim.",
            },
            {
                "dimension": "Thellësia e Analizës/Pyetjeve",
                "score": 82,
                "peerAverage": 75,
                "globalBenchmark": 88,
                "description": "Aftësia për të bërë pyetje të thelluara.",
                "commentary": "Pyetje të mprehta, por numri i të ftuarve kufizon thellimin.",
            },
            {
                "dimension": "Qartësia & Koherenca",
                "score": 95,
                "peerAverage": 80,
                "globalBenchmark": 90,
                "description": "Qartësia e të folurit dhe menaxhimi logjik.",
                "commentary": "Komunikues i shkëlqyer dhe i shpejtë, mban vëmendjen e audiencës.",
            },
            {
                "dimension": "Promovimi i të Menduarit Kritik",
                "score": 75,
                "peerAverage": 70,
                "globalBenchmark": 85,
                "description": "Inkurajimi i perspektivave të shumëfishta.",
                "commentary": "Sjell zëra të ndryshëm, por formati favorizon përplasjen mbi reflektimin.",
            },
        ],
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/Opinion_Albanian_TV_program_logo.jpeg",
        "audienceRating": 88,
        "audienceDemographics": {"age": "45-65", "gender": "65% Meshkuj", "location": "Urban & Rural"},
    },
    {
        "id": "vip41",
        "name": "Grida Duma",
        "imageUrl": generate_profile_photo_url("Grida Duma"),
        "category": "Media",
        "shortBio": "Analiste politike dhe drejtuese e 'Top Story' në Top Channel.",
        "detailedBio": """Grida Duma është figurë e shquar publike, ish-politikane e lartë në PD,
tani analiste dhe drejtuese emisioni. Njihet për stilin elokuent dhe pyetjet e mprehta,
duke ndërthurur përvojën politike me moderimin.""",
        "zodiacSign": "Virgo",
        "maragonAnalysis": [
            {
                "dimension": "Pajtueshmëria Etike",
                "score": 87,
                "peerAverage": 75,
                "globalBenchmark": 92,
                "description": "Pajtueshmëria themelore me standardet etike.",
                "commentary": "Tranzicion profesional i suksesshëm nga politika në media.",
            },
            {
                "dimension": "Profesionalizmi në Kriza",
                "score": 90,
                "peerAverage": 78,
                "globalBenchmark": 85,
                "description": "Aftësia për të ruajtur qetësinë në kriza.",
                "commentary": "Eksperienca politike i jep kontroll të jashtëzakonshëm në debate të tensionuara.",
            },
            {
                "dimension": "Saktësia Faktike & Verifikimi",
                "score": 91,
                "peerAverage": 72,
                "globalBenchmark": 88,
                "description": "Rigoroziteti në verifikimin e informacionit.",
                "commentary": "Vazhdon traditën investigative të 'Top Story' me tema të mirë-hulumtuara.",
            },
            {
                "dimension": "Paanshmëria, Balanca & Anshmëria",
                "score": 75,
                "peerAverage": 65,
                "globalBenchmark": 90,
                "description": "Moderimi i paanshëm.",
                "commentary": "Sfidohet për shkak të së shkuarës politike, por përpiqet për balancë.",
            },
            {
                "dimension": "Thellësia e Analizës/Pyetjeve",
                "score": 92,
                "peerAverage": 75,
                "globalBenchmark": 88,
                "description": "Pyetje të thelluara dhe njohuri.",
                "commentary": "Avantazh unik nga njohja e brendshme politike; pyetje incizive.",
            },
            {
                "dimension": "Qartësia & Koherenca",
                "score": 94,
                "peerAverage": 80,
                "globalBenchmark": 90,
                "description": "Qartësia dhe artikulimi.",
                "commentary": "Tejet e artikuluar, bën temat komplekse të kuptueshme.",
            },
            {
                "dimension": "Promovimi i të Menduarit Kritik",
                "score": 86,
                "peerAverage": 70,
                "globalBenchmark": 85,
                "description": "Inkurajimi i perspektivave kritike.",
                "commentary": "Nxit audiencën të vërë në dyshim narrativat zyrtare përmes dosjeve investigative.",
            },
        ],
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/TopStory.jpg",
        "audienceRating": 91,
        "audienceDemographics": {"age": "35-55", "gender": "55% Meshkuj", "location": "Urban"},
    },
    {
        "id": "vip5",
        "name": "Ardit Gjebrea",
        "imageUrl": generate_profile_photo_url("Ardit Gjebrea"),
        "category": "Media & Showbiz",
        "shortBio": "Këngëtar, producent dhe drejtues i 'E Diela Shqiptare'.",
        "detailedBio": """Ardit Gjebrea është figurë poliedrike: këngëtar, kompozitor, producent dhe
prezantues. Krijues i 'E Diela Shqiptare' dhe organizator i festivalit 'Kënga Magjike'.""",
        "zodiacSign": "Gemini",
        "maragonAnalysis": generate_maragon_analysis("Ardit Gjebrea"),
        "tvShowLogoUrl": "https://www.tvklan.al/wp-content/uploads/2022/01/EDIELA-SHQIPTARE-1.png",
        "audienceRating": 95,
        "audienceDemographics": {"age": "18-65+", "gender": "70% Femra", "location": "Kombëtare"},
    },
    {
        "id": "vip9",
        "name": "Sokol Balla",
        "imageUrl": generate_profile_photo_url("Sokol Balla"),
        "category": "Media",
        "shortBio": "Gazetar dhe analist, drejtues i 'Real Story'.",
        "detailedBio": """Sokol Balla është gazetar dhe analist i njohur. Drejton emisionin
'Real Story', ku analizon zhvillimet politike dhe sociale.""",
        "zodiacSign": "Sagittarius",
        "maragonAnalysis": [
            {
                "dimension": "Pajtueshmëria Etike",
                "score": 85,
                "peerAverage": 75,
                "globalBenchmark": 92,
                "description": "Pajtueshmëria themelore me standardet etike.",
                "commentary": "Karrierë pa kompromise të mëdha etike; gazetari e përgjegjshme.",
            },
            {
                "dimension": "Profesionalizmi në Kriza",
                "score": 82,
                "peerAverage": 78,
                "globalBenchmark": 85,
                "description": "Profesionalizmi në situata të tensionuara.",
                "commentary": "Menaxhon mirë situatat e paparashikuara live.",
            },
            {
                "dimension": "Saktësia Faktike & Verifikimi",
                "score": 82,
                "peerAverage": 72,
                "globalBenchmark": 88,
                "description": "Verifikimi i informacionit.",
                "commentary": "Përkushtim ndaj verifikimit, por nganjëherë varet nga burime politike.",
            },
            {
                "dimension": "Paanshmëria, Balanca & Anshmëria",
                "score": 75,
                "peerAverage": 65,
                "globalBenchmark": 90,
                "description": "Moderimi i paanshëm.",
                "commentary": "Përpiqet për ekuilibër, por dinamika e të ftuarve mund të anojë.",
            },
            {
                "dimension": "Thellësia e Analizës/Pyetjeve",
                "score": 88,
                "peerAverage": 75,
                "globalBenchmark": 88,
                "description": "Pyetje të thelluara.",
                "commentary": "Demonstron njohuri të thella dhe bën pyetje sfiduese.",
            },
            {
                "dimension": "Qartësia & Koherenca",
                "score": 88,
                "peerAverage": 80,
                "globalBenchmark": 90,
                "description": "Qartësia dhe artikulimi.",
                "commentary": "Strukturon debatin në mënyrë logjike dhe të lehtë për t'u ndjekur.",
            },
            {
                "dimension": "Promovimi i të Menduarit Kritik",
                "score": 80,
                "peerAverage": 70,
                "globalBenchmark": 85,
                "description": "Inkurajimi i mendimit kritik.",
                "commentary": "Inkurajon kritikën përmes konfrontimit të ideve.",
            },
        ],
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/real-story-abc-2.jpg",
        "audienceRating": 82,
        "audienceDemographics": {"age": "40-60", "gender": "60% Meshkuj", "location": "Urban"},
    },
    {
        "id": "vip10",
        "name": "Eni Vasili",
        "imageUrl": generate_profile_photo_url("Eni Vasili"),
        "category": "Media",
        "shortBio": "Gazetare dhe drejtuese e 'Open'.",
        "detailedBio": """Eni Vasili drejton emisionin 'Open'. Njihet për stilin energjik dhe
aftësinë për të menaxhuar debate të nxehta me figura publike.""",
        "zodiacSign": "Aries",
        "maragonAnalysis": [
            {
                "dimension": "Pajtueshmëria Etike",
                "score": 86,
                "peerAverage": 75,
                "globalBenchmark": 92,
                "description": "Pajtueshmëria etike.",
                "commentary": "Fokusohet te përmbajtja, respekton të ftuarit.",
            },
            {
                "dimension": "Profesionalizmi në Kriza",
                "score": 90,
                "peerAverage": 78,
                "globalBenchmark": 85,
                "description": "Menaxhimi i krizave live.",
                "commentary": "Shumë e aftë në de-përshkallëzimin e tensioneve profesionale.",
            },
            {
                "dimension": "Saktësia Faktike & Verifikimi",
                "score": 88,
                "peerAverage": 72,
                "globalBenchmark": 88,
                "description": "Verifikimi i fakteve.",
                "commentary": "Rigorozitet i lartë në përgatitjen e dosjeve investigative.",
            },
            {
                "dimension": "Paanshmëria, Balanca & Anshmëria",
                "score": 80,
                "peerAverage": 65,
                "globalBenchmark": 90,
                "description": "Paanshmëria.",
                "commentary": "Ofron hapësirë për të gjitha palët, pavarësisht stilit energjik.",
            },
            {
                "dimension": "Thellësia e Analizës/Pyetjeve",
                "score": 85,
                "peerAverage": 75,
                "globalBenchmark": 88,
                "description": "Thellësia e pyetjeve.",
                "commentary": "Pyetje direkte, kërkon përgjigje konkrete.",
            },
            {
                "dimension": "Qartësia & Koherenca",
                "score": 90,
                "peerAverage": 80,
                "globalBenchmark": 90,
                "description": "Qartësia në komunikim.",
                "commentary": "Menaxhon qartë rrjedhën e debateve komplekse.",
            },
            {
                "dimension": "Promovimi i të Menduarit Kritik",
                "score": 82,
                "peerAverage": 70,
                "globalBenchmark": 85,
                "description": "Nxitja e mendimit kritik.",
                "commentary": "Përballja e opinioneve i jep audiencës material për gjykim.",
            },
        ],
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/Open.jpg",
        "audienceRating": 85,
        "audienceDemographics": {"age": "30-55", "gender": "50% M, 50% F", "location": "Urban"},
    },
    {
        "id": "vip11",
        "name": "Inva Mula",
        "imageUrl": generate_profile_photo_url("Inva Mula"),
        "category": "Art & Kulturë",
        "shortBio": "Soprano me famë ndërkombëtare.",
        "detailedBio": "Inva Mula është soprano me famë botërore, ambasadore e kulturës shqiptare në skenat më prestigjioze.",
        "zodiacSign": "Gemini",
    },
    {
        "id": "vip13",
        "name": "Alketa Vejsiu",
        "imageUrl": generate_profile_photo_url("Alketa Vejsiu"),
        "category": "Media & Showbiz",
        "shortBio": "Prezantuese, producente, sipërmarrëse.",
        "detailedBio": "Figurë poliedrike në media, modë dhe sipërmarrje. Drejtuese e spektakleve të mëdha.",
        "zodiacSign": "Pisces",
        "maragonAnalysis": generate_maragon_analysis("Alketa Vejsiu"),
        "audienceRating": 78,
        "audienceDemographics": {"age": "18-35", "gender": "65% Femra", "location": "Urban"},
    },
    {
        "id": "vip14",
        "name": "Arian Çani",
        "imageUrl": generate_profile_photo_url("Arian Çani"),
        "category": "Media",
        "shortBio": "Prezantues i 'Zonë e Lirë'.",
        "detailedBio": "Figurë ikonike dhe provokuese. 'Zonë e Lirë' njihet për stilin jokonvencional dhe pa filtra.",
        "zodiacSign": "Libra",
        "maragonAnalysis": generate_maragon_analysis("Arian Çani"),
        "audienceRating": 75,
        "audienceDemographics": {"age": "25-50", "gender": "70% Meshkuj", "location": "Kombëtare"},
    },
    {
        "id": "vip15",
        "name": "Arbana Osmani",
        "imageUrl": generate_profile_photo_url("Arbana Osmani"),
        "category": "Media & Showbiz",
        "shortBio": "Prezantuese e 'Big Brother VIP Albania'.",
        "detailedBio": "Një nga prezantueset më të suksesshme. Njihet veçanërisht për drejtimin e fenomenit televiziv BBVIP.",
        "zodiacSign": "Taurus",
        "maragonAnalysis": generate_maragon_analysis("Arbana Osmani"),
        "tvShowLogoUrl": "https://upload.wikimedia.org/wikipedia/en/thumb/5/52/Big_Brother_VIP_Albania_3.png/250px-Big_Brother_VIP_Albania_3.png",
        "audienceRating": 98,
        "audienceDemographics": {"age": "16-45", "gender": "60% Femra", "location": "Kombëtare & Diasporë"},
    },
    {
        "id": "vip16",
        "name": "Adi Krasta",
        "imageUrl": generate_profile_photo_url("Adi Krasta"),
        "category": "Media",
        "shortBio": "Gazetar dhe prezantues me karrierë të gjatë.",
        "detailedBio": "Stil elokuent dhe intelektual. Ka drejtuar emisione historike, zë kritik dhe i pavarur.",
        "zodiacSign": "Leo",
        "maragonAnalysis": generate_maragon_analysis("Adi Krasta"),
        "audienceRating": 79,
        "audienceDemographics": {"age": "40+", "gender": "60% Meshkuj", "location": "Urban"},
    },
    {
        "id": "vip17",
        "name": "Sonila Meço",
        "imageUrl": generate_profile_photo_url("Sonila Meço"),
        "category": "Media",
        "shortBio": "Gazetare, prezantuese lajmesh.",
        "detailedBio": "Figurë autoritative, njihet për profesionalizëm, qartësi dhe pyetje të mprehta.",
        "zodiacSign": "Scorpio",
        "maragonAnalysis": generate_maragon_analysis("Sonila Meço"),
        "audienceRating": 84,
        "audienceDemographics": {"age": "35-60", "gender": "50% M, 50% F", "location": "Urban"},
    },
    {
        "id": "vip18",
        "name": "Marin Mema",
        "imageUrl": generate_profile_photo_url("Marin Mema"),
        "category": "Media",
        "shortBio": "Gazetar investigativ, 'Gjurmë Shqiptare'.",
        "detailedBio": "Fokusohet në histori dhe kulturë, duke zbuluar fate shqiptarësh dhe tema kombëtare.",
        "zodiacSign": "Capricorn",
        "maragonAnalysis": generate_maragon_analysis("Marin Mema"),
        "audienceRating": 93,
        "audienceDemographics": {"age": "25-65+", "gender": "55% Meshkuj", "location": "Kombëtare & Diasporë"},
    },
    {
        "id": "vip19",
        "name": "Blendi Salaj",
        "imageUrl": generate_profile_photo_url("Blendi Salaj"),
        "category": "Media & Radio",
        "shortBio": "Gazetar, prezantues radiofonik.",
        "detailedBio": "Zë i njohur radiofonik, komentator social me stil të hapur dhe ironik.",
        "zodiacSign": "Gemini",
        "maragonAnalysis": generate_maragon_analysis("Blendi Salaj"),
        "audienceRating": 77,
        "audienceDemographics": {"age": "20-40", "gender": "50% M, 50% F", "location": "Urban (Tiranë)"},
    },
    {
        "id": "vip20",
        "name": "Enkel Demi (Tomi)",
        "imageUrl": generate_profile_photo_url("Enkel Demi (Tomi)"),
        "category": "Media & Letërsi",
        "shortBio": "Gazetar, shkrimtar.",
        "detailedBio": "Ndërthur komentin social, kulturën dhe humorin. Vlerësohet për thellësinë e analizave.",
        "zodiacSign": "Cancer",
        "maragonAnalysis": generate_maragon_analysis("Enkel Demi (Tomi)"),
        "audienceRating": 76,
        "audienceDemographics": {"age": "35+", "gender": "55% Meshkuj", "location": "Urban"},
    },
    {
        "id": "vip21",
        "name": "Armina Mevlani",
        "imageUrl": generate_profile_photo_url("Armina Mevlani"),
        "category": "Showbiz & Influencer",
        "shortBio": "Blogere mode, sipërmarrëse.",
        "detailedBio": "Influencuese e njohur mode, markë e fortë personale në showbiz.",
        "zodiacSign": "Sagittarius",
        "maragonAnalysis": generate_maragon_analysis("Armina Mevlani"),
        "audienceRating": 68,
        "audienceDemographics": {"age": "18-30", "gender": "80% Femra", "location": "Urban"},
    },
    {
        "id": "vip22",
        "name": "Bledi Mane",
        "imageUrl": generate_profile_photo_url("Bledi Mane"),
        "category": "Media",
        "shortBio": "Gazetar provokues.",
        "detailedBio": "Stil i drejtpërdrejtë dhe polemizues. Trajton tema tabu.",
        "zodiacSign": "Aries",
        "maragonAnalysis": generate_maragon_analysis("Bledi Mane"),
        "audienceRating": 65,
        "audienceDemographics": {"age": "20-45", "gender": "65% Meshkuj", "location": "Kombëtare"},
    },
    {
        "id": "vip23",
        "name": "Mustafa Nano",
        "imageUrl": generate_profile_photo_url("Mustafa Nano"),
        "category": "Media",
        "shortBio": "Publicist, analist.",
        "detailedBio": "Qëndrime kundër rrymës, analiza kritike ndaj fenomeneve sociale dhe fetare.",
        "zodiacSign": "Virgo",
        "maragonAnalysis": generate_maragon_analysis("Mustafa Nano"),
        "audienceRating": 74,
        "audienceDemographics": {"age": "40+", "gender": "70% Meshkuj", "location": "Urban"},
    },
    {
        "id": "vip24",
        "name": "Ermal Peçi",
        "imageUrl": generate_profile_photo_url("Ermal Peçi"),
        "category": "Media & Showbiz",
        "shortBio": "Prezantues argëtues.",
        "detailedBio": "Fokusuar në emisione argëtuese dhe showbiz. Stil pozitiv dhe energjik.",
        "zodiacSign": "Libra",
        "maragonAnalysis": generate_maragon_analysis("Ermal Peçi"),
        "audienceRating": 72,
        "audienceDemographics": {"age": "18-40", "gender": "60% Femra", "location": "Kombëtare"},
    },
    {
        "id": "vip25",
        "name": "Ilva Tare",
        "imageUrl": generate_profile_photo_url("Ilva Tare"),
        "category": "Media",
        "shortBio": "Gazetare me përvojë.",
        "detailedBio": "Respektuar për profesionalizëm dhe paanshmëri. 'Tonight Ilva Tare' ishte platformë qendrore debati.",
        "zodiacSign": "Aquarius",
        "maragonAnalysis": generate_maragon_analysis("Ilva Tare"),
        "audienceRating": 87,
        "audienceDemographics": {"age": "35-60", "gender": "55% Meshkuj", "location": "Urban"},
    },
    {
        "id": "vip26",
        "name": "Dalina Buzi",
        "imageUrl": generate_profile_photo_url("Dalina Buzi"),
        "category": "Media & Produksion",
        "shortBio": "Themeluese e 'Anabel Media'.",
        "detailedBio": "Sipërmarrëse, skenariste. Krijon përmbajtje që rezonon me audiencën e re femërore.",
        "zodiacSign": "Leo",
        "maragonAnalysis": generate_maragon_analysis("Dalina Buzi"),
        "audienceRating": 81,
        "audienceDemographics": {"age": "18-35", "gender": "85% Femra", "location": "Urban"},
    },
    {
        "id": "vip27",
        "name": "Ledion Liço",
        "imageUrl": generate_profile_photo_url("Ledion Liço"),
        "category": "Media & Showbiz",
        "shortBio": "Prezantues dhe producent.",
        "detailedBio": "Stil modern. Ka drejtuar formatet më të mëdha të talent-show.",
        "zodiacSign": "Aries",
        "maragonAnalysis": generate_maragon_analysis("Ledion Liço"),
        "audienceRating": 80,
        "audienceDemographics": {"age": "16-40", "gender": "60% Femra", "location": "Kombëtare"},
    },
    {
        "id": "vip28",
        "name": "Dritan Shakohoxha",
        "imageUrl": generate_profile_photo_url("Dritan Shakohoxha"),
        "category": "Gazetari Sportive",
        "shortBio": "Komentator sportiv.",
        "detailedBio": "'Zëri' i futbollit. Njihet për pasionin dhe stilin unik.",
        "zodiacSign": "Taurus",
        "maragonAnalysis": generate_maragon_analysis("Dritan Shakohoxha"),
        "audienceRating": 96,
        "audienceDemographics": {"age": "16-60", "gender": "80% Meshkuj", "location": "Kombëtare & Diasporë"},
    },
    {
        "id": "vip32",
        "name": "Ylli Rakipi",
        "imageUrl": generate_profile_photo_url("Ylli Rakipi"),
        "category": "Media",
        "shortBio": "Gazetar i 'Të Paekspozuarit'.",
        "detailedBio": "Gazetar investigativ. Kritik ndaj pushtetit, denoncon afera korruptive.",
        "zodiacSign": "Scorpio",
        "maragonAnalysis": generate_maragon_analysis("Ylli Rakipi"),
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/TPaEks.jpg",
        "audienceRating": 78,
        "audienceDemographics": {"age": "45+", "gender": "75% Meshkuj", "location": "Kombëtare"},
    },
]


# =====================================================================================
# 3. BUSINESS PROFILES
# =====================================================================================

mock_business_profiles_data: List[VipProfile] = [
    {
        "id": "vip12",
        "name": "Ermal Mamaqi",
        "imageUrl": generate_profile_photo_url("Ermal Mamaqi"),
        "category": "Showbiz & Biznes",
        "shortBio": "Aktor, producent, sipërmarrës.",
        "detailedBio": """Figurë shumëplanëshe: humor, film, biznes, trajner motivimi. Sukses në showbiz
dhe zhvillim personal.""",
        "zodiacSign": "Aquarius",
        "maragonAnalysis": generate_maragon_analysis("Ermal Mamaqi"),
        "audienceRating": 83,
        "audienceDemographics": {"age": "25-45", "gender": "50% M, 50% F", "location": "Urban"},
    },
    {
        "id": "vip31",
        "name": "Samir Mane",
        "imageUrl": generate_profile_photo_url("Samir Mane"),
        "category": "Biznes",
        "shortBio": "President i Grupit BALFIN.",
        "detailedBio": """President i Grupit BALFIN (NEPTUN, SPAR, miniera, turizëm, pasuri të paluajtshme).
Një nga biznesmenët më të fuqishëm dhe me ndikim në rajon.""",
        "zodiacSign": "Leo",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 92,
                "peerAverage": 80,
                "globalBenchmark": 85,
                "description": "Vizioni i Biznesit & Inovacioni.",
                "commentary": "Aftësi e jashtëzakonshme për diversifikim portofoli dhe lider rajonal.",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 88,
                "peerAverage": 82,
                "globalBenchmark": 84,
                "description": "Lidershipi dhe Menaxhimi.",
                "commentary": "Stil efektiv i orientuar drejt rritjes; vendimmarrje strategjike e centralizuar.",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 90,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Performanca Financiare.",
                "commentary": "Rritje e qëndrueshme, kontribut i madh në ekonomi.",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 75,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Përgjegjësia Sociale e Korporatës (CSR).",
                "commentary": "Angazhim në rritje në CSR, por kritika për ndikim mjedisor të disa projekteve.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 85,
                "peerAverage": 80,
                "globalBenchmark": 83,
                "description": "Reputacioni dhe Ndikimi Publik.",
                "commentary": "Biznesmen i suksesshëm, por përflitet për lidhje me pushtetin.",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 65,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Llogaridhënia dhe transparenca.",
                "commentary": "Mungesë transparence për marrëdhëniet me qeverinë (PPP).",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 80,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Stabiliteti Organizativ.",
                "commentary": "Menaxhim i shkëlqyer i rritjes dhe diversifikimit.",
            },
        ],
    },
    {
        "id": "vip33",
        "name": "Dr Alban Gj. THIKA",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/10/NOVARIC_Team-Member_A-THIKA_Small.png",
        "category": "Politikë & Biznes",
        "shortBio": "Strategic Consultant & CEO NOVARIC.",
        "detailedBio": """### Professional Summary
A Doctorate-level political and business strategist with over 20 years of international experience spanning public administration, enterprise development, campaign consultancy, and academic research across Albania, Malta, and Australia. Combines rigorous academic training in International Relations and Business Administration with an entrepreneurial mindset to drive reform, innovation, and growth. Adept at navigating complex multicultural and regulatory environments, with direct experience in EU project management and high-level political advisory roles. Proven resilience and a consistent drive to initiate and lead new ventures in challenging markets.

### Core Competencies
- **Political Strategy & Public Affairs:** Political Consulting, Campaign Strategy, Public Policy Analysis, International Relations, Public Administration, EU Project Management.
- **Business & Management:** Strategic Planning, Business Development & Start-ups, International Trade & Sourcing, Market Analysis, Operations Management, Change Management.
- **Communication & Leadership:** Cross-Cultural Communication, Public Speaking, Coalition Building, Negotiation & Conflict Resolution, Resilience & Adaptability.

### Professional Experience
**Deputy Party Leader | Christian Democratic Party of Albania | Tirana, Albania**
*(2023) – Present*

**Founder & CEO | NOVARIC® (Sh.A. Albania & Ltd. Malta) | Tirana & Valletta**
*2014 – Present*

**Political Consultant & Parliamentary Assistant | Nationalist Party | Valletta, Malta**
*2013 – 2017*

### Political Candidacies & Civic Engagement
- **Candidate, Local Council Elections | St. Paul’s Bay, Malta** (2015)
- **Independent Candidate for Mayor | Shkoder, Albania** (2007)

### Education
- **Doctor of Business Administration (DBA)** - University of South Australia, Adelaide, Australia (2010)
- **Master of Business Administration (MBA), Advanced** - University of Adelaide, Adelaide, Australia (2004)
- **Bachelor of Arts (Honours), International Relations (B+)** - University of Malta, Msida, Malta (2001)""",
        "zodiacSign": "Capricorn",
    },
]


# =====================================================================================
# 4. HYDRATION LOGIC (The "Bridge" to the Engine) — OPTION A (ENGINE WINS)
# =====================================================================================

def hydrate_profiles_with_engine(profiles: List[VipProfile]) -> None:
    """
    Iterate through all profiles and, where possible, overwrite static paragonAnalysis
    with clinically computed results from the PARAGON engine.
    
    OPTION A (recommended for production):
    - Static paragonAnalysis values act as fallback only.
    - Whenever metric bundles exist for a given ID, engine scores take precedence.
    """
    if not ENGINE_AVAILABLE:
        return  # Engine not available; keep static mock data

    count_updated = 0

    for profile in profiles:
        pid = profile.get("id")
        if not pid:
            continue

        metrics_bundle = None

        # 1. Prefer preloaded RAW_EVIDENCE if present
        if RAW_EVIDENCE.get(pid):
            metrics_bundle = RAW_EVIDENCE[pid]
        else:
            # 2. Load evidence on demand via metric_loader
            try:
                metrics_bundle = load_metrics_for(pid)
            except Exception as e:
                logging.warning("PARAGON: Error loading metrics for %s: %s", pid, e)
                continue

        if not metrics_bundle:
            # No real data for this ID; keep static analysis
            continue

        # 3. Score metrics using scoring_engine
        try:
            new_analysis = score_metrics(metrics_bundle)
        except Exception as e:
            logging.warning("PARAGON: Error scoring metrics for %s: %s", pid, e)
            continue

        if not new_analysis:
            continue

        # 4. Overwrite static fallback paragonAnalysis with engine results
        profile["paragonAnalysis"] = new_analysis
        count_updated += 1

    if count_updated > 0:
        logging.info("🚀 PARAGON Engine: Clinically updated %d profiles with real data.", count_updated)


# =====================================================================================
# 5. FINAL EXPORT: COMBINE ALL PROFILES
# This is the list exported for use by main.py
# =====================================================================================

PROFILES: List[VipProfile] = (
    mock_political_profiles_data 
    + mock_media_profiles_data 
    + mock_business_profiles_data
)

# Run the hydration pass before exporting to ensure PROFILES has latest data
hydrate_profiles_with_engine(PROFILES)
