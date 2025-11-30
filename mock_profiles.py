# mock_profiles.py
# Minimal profile metadata used by the backend.
# Scoring is generated dynamically in main.py

import random
from typing import Any, Dict, List, Union

# Lightweight runtime types
VipProfile = Dict[str, Any]
ParagonEntry = Dict[str, Any]


# #####################################################################################
# Helper generators (photo URL, random scores, PARAGON / MARAGON entries)
# #####################################################################################

def generate_profile_photo_url(name: str) -> str:
    """
    Build a deterministic photo URL for a given name.
    """
    if not name:
        return "https://novaric.co/wp-content/uploads/2025/11/Placeholder.jpg"
    parts = name.split(" ")
    last_name = (parts.pop() or "").upper()
    first_name = "".join(parts).replace(".", "")
    formatted_name = f"{first_name}{last_name}"
    return f"https://novaric.co/wp-content/uploads/2025/11/{formatted_name}.jpg"


def generate_random_score(min_val: int = 40, max_val: int = 85) -> int:
    return random.randint(min_val, max_val)


def generate_paragon_analysis(name: str) -> List[ParagonEntry]:
    return [
        {
            "dimension": "Policy Engagement & Expertise",
            "score": generate_random_score(),
            "peerAverage": 68,
            "globalBenchmark": 72,
            "description": """Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit;
puna në komisione dhe ekspertiza në fusha specifike.""",
            "commentary": f"""Të dhënat për performancën legjislative të {name} do të mblidhen dhe
analizohen gjatë mandatit aktual parlamentar.""",
        },
        {
            "dimension": "Accountability & Transparency",
            "score": generate_random_score(),
            "peerAverage": 62,
            "globalBenchmark": 70,
            "description": """Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë
dhe respektimi i standardeve etike.""",
            "commentary": f"""Transparenca dhe llogaridhënia për {name} do të vlerësohen
bazuar në veprimtarinë publike dhe pajtueshmërinë me rregulloret.""",
        },
        {
            "dimension": "Representation & Responsiveness",
            "score": generate_random_score(),
            "peerAverage": 70,
            "globalBenchmark": 75,
            "description": """Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave
të komunitetit.""",
            "commentary": f"""Angazhimi i {name} me zonën zgjedhore dhe komunitetin do të
monitorohet gjatë gjithë legjislaturës.""",
        },
        {
            "dimension": "Assertiveness & Influence",
            "score": generate_random_score(),
            "peerAverage": 65,
            "globalBenchmark": 68,
            "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
            "commentary": f"""Ndikimi politik i {name} do të matet përmes nismave dhe rolit
në debatet kyçe.""",
        },
        {
            "dimension": "Governance & Institutional Strength",
            "score": generate_random_score(),
            "peerAverage": 67,
            "globalBenchmark": 73,
            "description": """Kontributi në forcimin e institucioneve demokratike dhe
sundimit të ligjit.""",
            "commentary": f"""Veprimtaria e {name} në lidhje me qeverisjen dhe reformat
institucionale do të jetë objekt analize.""",
        },
        {
            "dimension": "Organizational & Party Cohesion",
            "score": generate_random_score(),
            "peerAverage": 75,
            "globalBenchmark": 78,
            "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
            "commentary": f"""Qëndrimet dhe votimet e {name} do të analizohen në raport
me linjën zyrtare të partisë.""",
        },
        {
            "dimension": "Narrative & Communication",
            "score": generate_random_score(),
            "peerAverage": 71,
            "globalBenchmark": 74,
            "description": "Efektiveti dhe qartësia e komunikimit publik.",
            "commentary": f"""Aftësitë komunikuese dhe diskursi publik i {name} do të
vlerësohen në vazhdimësi.""",
        },
    ]


def generate_maragon_analysis(name: str) -> List[ParagonEntry]:
    return [
        {
            "dimension": "Pajtueshmëria Etike",
            "score": generate_random_score(70, 90),
            "peerAverage": 75,
            "globalBenchmark": 92,
            "description": """Pajtueshmëria themelore me standardet etike/operacionale,
siç përcaktohet në Kodin e Standardeve.""",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Profesionalizmi në Kriza",
            "score": generate_random_score(70, 90),
            "peerAverage": 78,
            "globalBenchmark": 85,
            "description": """Aftësia për të ruajtur qetësinë dhe standardet profesionale
gjatë lajmeve të fundit ose debateve të tensionuara.""",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Saktësia Faktike & Verifikimi",
            "score": generate_random_score(70, 90),
            "peerAverage": 72,
            "globalBenchmark": 88,
            "description": """Rigoroziteti në verifikimin e informacionit para transmetimit,
atribuimin e saktë të burimeve dhe dallimin e qartë midis faktit dhe opinionit.""",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Paanshmëria, Balanca & Anshmëria",
            "score": generate_random_score(60, 85),
            "peerAverage": 65,
            "globalBenchmark": 90,
            "description": """Mat aftësinë për të moderuar debatin në mënyrë të paanshme,
duke u dhënë kohë dhe hapësirë të barabartë të gjitha palëve.""",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Thellësia e Analizës/Pyetjeve",
            "score": generate_random_score(70, 90),
            "peerAverage": 75,
            "globalBenchmark": 88,
            "description": """Aftësia për të bërë pyetje të thelluara, për të ndjekur përgjigjet
dhe për të demonstruar njohuri të thella mbi temën.""",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Qartësia & Koherenca",
            "score": generate_random_score(80, 95),
            "peerAverage": 80,
            "globalBenchmark": 90,
            "description": """Qartësia e të folurit, artikulimi dhe aftësia për të menaxhuar rrjedhën
logjike të një debati ose interviste.""",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Promovimi i të Menduarit Kritik",
            "score": generate_random_score(65, 85),
            "peerAverage": 70,
            "globalBenchmark": 85,
            "description": """Inkurajimi i audiencës për të konsideruar perspektiva të shumëfishta
dhe për të sfiduar supozimet e tyre.""",
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
    ]


ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def create_placeholder_mp(mp_id: Union[str, int], name: str, party: str) -> VipProfile:
    return {
        "id": mp_id,
        "name": name,
        "imageUrl": generate_profile_photo_url(name),
        "category": f"Politikë ({party})",
        "shortBio": f"Deputet/e i/e Kuvendit të Shqipërisë, anëtar/e i/e {party}.",
        "detailedBio": f"""Informacion i detajuar për {name} do të shtohet së shpejti. Ky profil
është krijuar për të paraqitur veprimtarinë parlamentare dhe publike të deputetit/es
në kuadër të legjislaturës 2025. Të dhënat e performancës do të përditësohen
periodikisht bazuar në monitorimin e aktivitetit legjislativ, deklarimeve publike
dhe angazhimit në komunitet.""",
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
                "description": """Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit;
puna në komisione dhe ekspertiza në fusha specifike.""",
                "commentary": """Shquhet për projekte transformuese afatgjata si Rilindja Urbane,
por kritikohet për mungesë konsultimi dhe kosto të lartë, veçanërisht me projektet
e Partneritetit Publik-Privat (PPP).""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 45,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": """Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë
dhe respektimi i standardeve etike.""",
                "commentary": """Qeverisja e tij është përballur me akuza të vazhdueshme për korrupsion,
kapje të shtetit dhe mungesë transparence, të cilat mbeten një sfidë e madhe për
imazhin e tij.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 60,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": """Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave të
komunitetit.""",
                "commentary": """Kritikohet për një qasje "nga lart-poshtë" dhe për mungesë të theksuar
të dialogut me grupet e interesit dhe qytetarët.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 95,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
                "commentary": """Ka një kontroll pothuajse absolut mbi Partinë Socialiste, duke qenë
figura qendrore dhe vendimmarrësi i padiskutueshëm, gjë që siguron unitet por
kufizon debatin e brendshëm.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 65,
                "peerAverage": 60,
                "globalBenchmark": 68,
                "description": """Kontributi në forcimin e institucioneve demokratike dhe sundimit
të ligjit.""",
                "commentary": """Ka mbikëqyrur reforma të rëndësishme si ajo në drejtësi, por
njëkohësisht akuzohet për centralizim të pushtetit dhe dobësim të institucioneve
të pavarura.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 92,
                "peerAverage": 80,
                "globalBenchmark": 82,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": """Ruan një kohezion të fortë brenda grupit parlamentar dhe partisë,
shpesh përmes një lidershipi autoritar.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 90,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Komunikues i jashtëzakonshëm dhe karizmatik, përdor median sociale
dhe daljet publike në mënyrë efektive, por stili i tij mund të jetë polarizues
dhe shpeshherë konfrontues.""",
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
dy dekada dhe mbetet një figurë me ndikim të madh në politikën shqiptare. Karriera e
tij është shënuar nga tranzicioni i Shqipërisë drejt demokracisë dhe ekonomisë së tregut.""",
        "zodiacSign": "Libra",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 60,
                "peerAverage": 72,
                "globalBenchmark": 70,
                "description": """Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit;
puna në komisione dhe ekspertiza në fusha specifike.""",
                "commentary": """Aktiviteti i tij parlamentar është i kufizuar, duke u fokusuar
kryesisht në fjalime politike nga ballkoni dhe media sociale, dhe më pak
në iniciativa konkrete legjislative.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 30,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": """Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë
dhe respektimi i standardeve etike.""",
                "commentary": """Nën arrest shtëpie dhe përballet me akuza serioze për korrupsion
nga SPAK, gjë që ka dëmtuar rëndë perceptimin e tij publik përtej bazës së tij
mbështetëse.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 70,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": """Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave
të komunitetit.""",
                "commentary": """Ruan një lidhje të fortë me bazën e tij historike mbështetëse,
por ka vështirësi të arrijë audienca më të gjera.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 88,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
                "commentary": """Pavarësisht sfidave ligjore dhe politike, ai ruan një ndikim masiv
dhe një kontroll të fortë mbi grupimin e tij brenda Partisë Demokratike, duke
shkaktuar përçarjen e saj.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 35,
                "peerAverage": 65,
                "globalBenchmark": 72,
                "description": """Kontributi në forcimin e institucioneve demokratike dhe sundimit
të ligjit.""",
                "commentary": """I shpallur "non grata" nga SHBA dhe MB, gjë që e ka izoluar nga
partnerët perëndimorë kyç, duke kufizuar rolin e tij në qeverisje dhe diplomaci.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 45,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": """Figura e tij është njëkohësisht bashkuese për ndjekësit e tij
dhe thellësisht përçarëse për Partinë Demokratike në tërësi, duke çuar në
ndarjen e saj.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 80,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Mbetet një orator i fuqishëm me aftësi për të mobilizuar
mbështetësit e tij më besnikë, edhe pse retorika e tij është bërë gjithnjë e
më shumë përçarëse dhe konfrontuese.""",
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
duke përfshirë Kryeministër i Shqipërisë (1999-2002), Kryetar i Kuvendit (2013-2017)
dhe President i Shqipërisë (2017-2022). Meta është i njohur për karrierën e tij të
gjatë politike dhe rolin e tij si "kingmaker" në skenën politike shqiptare.""",
        "zodiacSign": "Aries",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 55,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": """Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit;
puna në komisione dhe ekspertiza në fusha specifike.""",
                "commentary": """Njihet më shumë si një strateg dhe takticien politik afatshkurtër,
i fokusuar te lëvizjet për të maksimizuar pushtetin, sesa si një vizionar me plane
afatgjata për vendin.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 35,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": """Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë
dhe respektimi i standardeve etike.""",
                "commentary": """Përballet me akuza të vazhdueshme për korrupsion dhe pasuri të
pajustifikuar, të cilat janë intensifikuar me hetimet e SPAK, duke dëmtuar rëndë
imazhin e tij.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 68,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": """Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave
të komunitetit.""",
                "commentary": """Ka një aftësi të spikatur për të ndërtuar marrëdhënie klienteliste
në nivel lokal, por kjo nuk përkthehet gjithmonë në përgjegjshmëri të gjerë publike.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 92,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
                "commentary": """Ka kontroll absolut mbi Partinë e Lirisë, duke qenë figura
dominuese dhe vendimmarrësi kryesor, pavarësisht ndryshimeve formale në krye
të partisë.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 62,
                "peerAverage": 60,
                "globalBenchmark": 68,
                "description": """Kontributi në forcimin e institucioneve demokratike dhe sundimit
të ligjit.""",
                "commentary": """Mandati i tij si President u shoqërua me përplasje të forta
institucionale dhe akuza për tejkalim kompetencash. Veprimet e tij të fundit kanë
tensionuar marrëdhëniet me partnerët ndërkombëtarë.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 90,
                "peerAverage": 80,
                "globalBenchmark": 82,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": """Ruan kontroll të hekurt mbi strukturat e partisë, duke siguruar
unitet dhe disiplinë të brendshme.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 75,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Komunikimi i tij është bërë gjithnjë e më i paparashikueshëm,
emocional dhe shpërthyes, gjë që e bën më pak efektiv dhe shpeshherë objekt humori.""",
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
Partisë Demokratike nga viti 2013 deri në 2022. Ai ka mbajtur disa poste ministrore,
përfshirë Ministër i Punëve të Jashtme dhe Ministër i Brendshëm, si dhe ka qenë
Kryetar i Bashkisë së Tiranës. Basha ka qenë një figurë qendrore në politikën
opozitare shqiptare për shumë vite.""",
        "zodiacSign": "Taurus",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 65,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": """Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit;
puna në komisione dhe ekspertiza në fusha specifike.""",
                "commentary": """Shpesh është kritikuar për mungesë të një vizioni të qartë dhe
afatgjatë, duke u fokusuar më shumë në reagime ndaj zhvillimeve ditore.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 60,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": """Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë
dhe respektimi i standardeve etike.""",
                "commentary": """Nuk është përballur me akuza të mëdha korrupsioni personalisht,
por lidershipi i tij është kritikuar për menaxhimin e çështjeve të brendshme
të partisë.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 62,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": """Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave
të komunitetit.""",
                "commentary": """Ka marrëdhënie të mira me partnerët ndërkombëtarë, por kjo nuk
është përkthyer gjithmonë në mbështetje të fortë elektorale.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 50,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
                "commentary": """Ka humbur ndjeshëm ndikimin dhe kontrollin mbi Partinë Demokratike,
duke çuar në përçarjen e saj dhe duke u pozicionuar si një figurë më e izoluar.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 70,
                "peerAverage": 65,
                "globalBenchmark": 72,
                "description": """Kontributi në forcimin e institucioneve demokratike dhe sundimit
të ligjit.""",
                "commentary": """Në rolet e tij ministrore ka kontribuar në procese të rëndësishme
si liberalizimi i vizave, duke treguar aftësi pro-institucionale.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 40,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": """Lidershipi i tij çoi në përçarjen më të madhe në historinë e Partisë
Demokratike, duke humbur mbështetjen e një pjese të madhe të strukturave.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 70,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Komunikon në mënyrë të qetë dhe të strukturuar, por i mungon
karizma dhe fuqia mobilizuese e liderëve të tjerë historikë.""",
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
Socialiste për Integrim (tani Partia e Lirisë). Ajo është deputete në Kuvendin e
Shqipërisë dhe ka një karrierë të gjatë politike, duke qenë aktive në skenë që nga
vitet '90. Kryemadhi është e njohur për rolin e saj si një zë i fuqishëm në politikën
shqiptare.""",
        "zodiacSign": "Gemini",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 58,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": """Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit;
puna në komisione dhe ekspertiza në fusha specifike.""",
                "commentary": """Fokusi i saj ka qenë kryesisht në organizimin e partisë dhe
strategjitë elektorale afatshkurtra, më shumë sesa në propozime specifike
politikash.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 42,
                "peerAverage": 55,
                "globalBenchmark": 65,
                "description": """Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë
dhe respektimi i standardeve etike.""",
                "commentary": """Përballet me akuza për pasuri të pajustifikuar dhe korrupsion, gjë
që ka ndikuar negativisht në imazhin e saj publik.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 75,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": """Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave
të komunitetit.""",
                "commentary": """Njihet për një lidhje të fortë me bazën elektorale të partisë
dhe aftësinë për të mobilizuar mbështetësit në terren.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 85,
                "peerAverage": 85,
                "globalBenchmark": 80,
                "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
                "commentary": """Ruan një ndikim shumë të fortë brenda strukturave të Partisë së
Lirisë, duke qenë një figurë kyçe vendimmarrëse.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 60,
                "peerAverage": 65,
                "globalBenchmark": 72,
                "description": """Kontributi në forcimin e institucioneve demokratike dhe sundimit
të ligjit.""",
                "commentary": """Nuk ka pasur rol direkt në menaxhimin ekonomik, por partia e saj ka
ndikuar në politikat ekonomike kur ka qenë në qeveri.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 88,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": """Ka treguar aftësi të larta organizative dhe ruan një kontroll të
fortë mbi strukturat e partisë.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 82,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Komunikuese energjike dhe e drejtpërdrejtë, me aftësi për të
mobilizuar bazën e partisë, ndonëse stili i saj mund të jetë polarizues.""",
            },
        ],
    },
    {
        "id": "vip8",
        "name": "Erion Veliaj",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/ErionVELIAJ.jpg",
        "category": "Politikë (PS)",
        "shortBio": "Kryetar i Bashkisë së Tiranës.",
        "detailedBio": """Erion Veliaj është Kryetar i Bashkisë së Tiranës që nga viti 2015, i
rizgjedhur për mandate të tjera. Më parë, ai ka shërbyer si Ministër i Mirëqenies
Sociale dhe Rinisë. Veliaj njihet për projektet e tij urbane në Tiranë dhe
iniciativat sociale. Aktiviteti i tij politik filloi me lëvizjen qytetare "MJAFT!".""",
        "zodiacSign": "Leo",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 82,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": """Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit;
puna në komisione dhe ekspertiza në fusha specifike.""",
                "commentary": """Ka demonstruar një vizion të qartë për transformimin urban të
Tiranës, megjithëse kritikohet për fokusin te betoni dhe mungesën e hapësirave
të gjelbra.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 40,
                "peerAverage": 58,
                "globalBenchmark": 65,
                "description": """Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë
dhe respektimi i standardeve etike.""",
                "commentary": """Administrata e tij është përballur me skandale dhe akuza të shumta
për korrupsion, veçanërisht lidhur me dosjen "5D" dhe inceneratorët.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 65,
                "peerAverage": 68,
                "globalBenchmark": 75,
                "description": """Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave
të komunitetit.""",
                "commentary": """Organizon takime të shpeshta me komunitetin, por shpesh akuzohet se
injoron zërat kritikë dhe shoqërinë civile, veçanërisht në çështje urbane.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 85,
                "peerAverage": 80,
                "globalBenchmark": 82,
                "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
                "commentary": """Ka një ndikim të konsiderueshëm brenda Partisë Socialiste dhe
aftësi për të çuar përpara projekte madhore, pavarësisht kundërshtimeve.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 75,
                "peerAverage": 70,
                "globalBenchmark": 72,
                "description": """Kontributi në forcimin e institucioneve demokratike dhe sundimit
të ligjit.""",
                "commentary": """Ka treguar efikasitet në realizimin e projekteve të mëdha, por
kritikohet për mungesë transparence në tenderë dhe kosto të larta.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 80,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": """Pozicionohet si një figurë besnike e lidershipit qendror, duke
siguruar mbështetje politike për projektet e tij.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 88,
                "peerAverage": 80,
                "globalBenchmark": 82,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Shumë i aftë në komunikim dhe marketing politik. Përdor mediat
sociale dhe eventet publike në mënyrë intensive për të promovuar punën e tij.""",
            },
        ],
    },
    {
        "id": "vip29",
        "name": "Belind Këlliçi",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/11/BelindKELLICI.jpg",
        "category": "Politikë (PD)",
        "shortBio": "Deputet i Partisë Demokratike dhe figurë e re politike.",
        "detailedBio": """Belind Këlliçi është një figurë e re dhe energjike në Partinë Demokratike.
Si deputet, ai është shquar për denoncimet e tij publike lidhur me korrupsionin dhe
abuzimet me pushtetin, veçanërisht në nivel vendor. Mban një profil aktiv mediatik
dhe konsiderohet një nga zërat kryesorë të brezit të ri në opozitë.""",
        "zodiacSign": "Virgo",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 68,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Pjesëmarrja në hartimin e legjislacionit dhe ekspertiza në fusha specifike.",
                "commentary": """Fokusi i tij kryesor është denoncimi dhe mbikëqyrja, më shumë sesa
propozimi i politikave të reja. Ekspertiza e tij është e përqendruar në çështjet e
korrupsionit urban.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 85,
                "peerAverage": 60,
                "globalBenchmark": 75,
                "description": "Llogaridhënia ndaj publikut dhe transparenca.",
                "commentary": """Është një nga zërat më të fortë në opozitë që kërkon llogaridhënie
dhe transparencë, veçanërisht për administratën e Tiranës, duke luajtur një rol aktiv
si "watchdog".""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 75,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": "Lidhja me zonën zgjedhore dhe përgjigja ndaj nevojave të komunitetit.",
                "commentary": """Aktiv në media dhe në takime me bazën e opozitës, duke artikuluar
shqetësimet e tyre.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 82,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": """Ka arritur të vendosë në axhendën publike disa tema kyçe të
korrupsionit, duke treguar një ndikim të konsiderueshëm mediatik dhe politik.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 60,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Kontributi në forcimin e institucioneve demokratike.",
                "commentary": """Veprimtaria e tij është e fokusuar në sfidimin e qeverisjes aktuale,
por kontributi i tij në ndërtimin e alternativave institucionale mbetet për t'u parë.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 70,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Roli në ruajtjen e unitetit partiak.",
                "commentary": """Është një figurë e rëndësishme brenda grupimit kryesor të opozitës,
por vepron në një parti thellësisht të përçarë.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 88,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Një nga komunikuesit më të mprehtë dhe efektivë të brezit të tij
në opozitë, i aftë të përdorë prova dhe retorikë të fortë.""",
            },
        ],
    },
    {
        "id": "vip30",
        "name": "Bajram Begaj",
        "imageUrl": generate_profile_photo_url("Bajram Begaj"),
        "category": "Politikë (President)",
        "shortBio": "President i Republikës së Shqipërisë.",
        "detailedBio": """Bajram Begaj është Presidenti aktual i Republikës së Shqipërisë. Para se të
merrte këtë detyrë, ai kishte një karrierë të gjatë ushtarake, duke mbajtur gradën
e Gjeneral Majorit dhe duke shërbyer si Shef i Shtabit të Përgjithshëm të Forcave
të Armatosura. Roli i tij si president është i fokusuar në përfaqësimin e unitetit
të kombit dhe garantimin e funksionimit kushtetues të shtetit.""",
        "zodiacSign": "Pisces",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 55,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Roli në hartimin e politikave është i kufizuar nga Kushtetuta.",
                "commentary": """Në rolin e tij si President, nuk ka angazhim direkt në politika, por
përdor ekspertizën e tij institucionale në ushtrimin e detyrës. Sfondi i tij ushtarak
dhe mjekësor është një pasuri.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 80,
                "peerAverage": 70,
                "globalBenchmark": 80,
                "description": "Llogaridhënia ndaj publikut dhe transparenca institucionale.",
                "commentary": """Institucioni i Presidencës ruan një nivel të lartë transparence
formale. Veprimtaria e tij është përgjithësisht publike dhe e dokumentuar.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 70,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Përfaqësimi i unitetit të kombit dhe përgjigja ndaj kërkesave institucionale.",
                "commentary": """Ka luajtur rolin e tij si përfaqësues i shtetit në arenën
ndërkombëtare dhe ka qenë i përgjegjshëm ndaj detyrimeve kushtetuese.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 65,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": """Ndikimi i tij është kryesisht institucional, përmes kthimit të
ligjeve dhe emërimeve. Nuk ka një ndikim të fortë personal në debatin e
përditshëm politik.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 85,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Kontributi në forcimin e institucioneve dhe sundimit të ligjit.",
                "commentary": """Roli i tij kryesor është ai i garantit të Kushtetutës. Ka mbajtur
një qëndrim përgjithësisht stabil dhe pro-institucional, duke shërbyer si një
faktor ekuilibrues.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 75,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli si figurë unifikuese mbi palët.",
                "commentary": """Qëndron mbi palët politike, siç e kërkon roli i tij. Ky pikëzim
reflekton përpjekjen për të ruajtur unitetin kombëtar, jo kohezionin partiak.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 68,
                "peerAverage": 75,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Stili i tij i komunikimit është formal, institucional dhe i përmbajtur.
Nuk synon të jetë një komunikator karizmatik, por një zë i matur i shtetit.""",
            },
        ],
    },
    {
        "id": "mp19",
        "name": "Benet Beci",
        "imageUrl": generate_profile_photo_url("Benet Beci"),
        "category": "Politikë (PS)",
        "shortBio": "Kryetar i Bashkisë Shkodër, inxhinier dhe ish-deputet.",
        "detailedBio": """Benet Beci, aktualisht Kryetar i Bashkisë Shkodër, është një figurë me një
karrierë të gjatë në administratën publike dhe politikë. I diplomuar si inxhinier,
ai ka drejtuar Fondin Shqiptar të Zhvillimit (FSHZH) për një periudhë të gjatë,
duke menaxhuar projekte të rëndësishme infrastrukturore në nivel kombëtar. Para
zgjedhjes së tij si kryebashkiak, Beci ka shërbyer edhe si deputet i Partisë
Socialiste në Kuvendin e Shqipërisë. Udhëheqja e tij në Shkodër fokusohet në
zhvillimin urban, përmirësimin e shërbimeve publike dhe promovimin e potencialit
turistik dhe ekonomik të rajonit.""",
        "zodiacSign": "Aries",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 85,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": """Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit;
puna në komisione dhe ekspertiza në fusha specifike.""",
                "commentary": """Përvoja e gjatë në menaxhimin e projekteve infrastrukturore i jep
një ekspertizë të thellë teknike, veçanërisht në zhvillimin urban dhe rajonal.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 70,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": """Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë
dhe respektimi i standardeve etike.""",
                "commentary": """Deri tani ka një imazh relativisht të pastër, por sfidat e transparencës
në bashki, si në rastin "Shkreli", mbeten një test për llogaridhënien e tij.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 82,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": """Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave
të komunitetit.""",
                "commentary": """Tregon një qasje të hapur ndaj bashkëpunimit me komunitetin dhe
grupet e interesit, duke u fokusuar në projekte me impakt direkt lokal.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 88,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
                "commentary": """Përkatësia e tij politike dhe përvoja e mëparshme i sigurojnë një
marrëdhënie shumë të mirë me qeverinë qendrore dhe aftësi për të siguruar fonde.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 85,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Kontributi në forcimin e institucioneve demokratike dhe sundimit të ligjit.",
                "commentary": """Përvoja në FSHZH i jep një avantazh të madh në menaxhimin administrativ
dhe zbatimin efikas të projekteve.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 78,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
                "commentary": """Ruan një linjë besnike me partinë, gjë që i siguron mbështetje
politike, por mund të kufizojë pavarësinë në vendime të caktuara.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 75,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Komunikues i matur dhe teknik, i fokusuar te rezultatet konkrete,
por jo gjithmonë i aftë të ngjallë pasion politik.""",
            },
        ],
    },
    {
        "id": "vip_nn",
        "name": "Nard Ndoka",
        "imageUrl": generate_profile_photo_url("Nard Ndoka"),
        "category": "Politikë (PDK)",
        "shortBio": "Kryetar i Partisë Demokristiane, ish-ministër dhe figurë e njohur mediatike.",
        "detailedBio": """Nard Ndoka (lindur më 7 tetor 1963) është një politikan shqiptar, themelues
dhe kryetar i Partisë Demokristiane (PDK). Ai ka shërbyer në poste të larta si
Ministër i Shëndetësisë dhe deputet në Kuvendin e Shqipërisë. I njohur për stilin
e tij të drejtpërdrejtë dhe shpeshherë satirik të komunikimit, Ndoka është një
figurë me prani të lartë mediatike, i cili komenton rregullisht zhvillimet politike
dhe sociale në vend.""",
        "zodiacSign": "Libra",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 55,
                "peerAverage": 65,
                "globalBenchmark": 70,
                "description": "Pjesëmarrja në hartimin e legjislacionit dhe ekspertiza në fusha specifike.",
                "commentary": """Aktiviteti i tij fokusohet më shumë te komentimi politik dhe
denoncimi sesa te angazhimi i thelluar në hartimin e politikave specifike.
Ekspertiza e tij është më e spikatur në fushat që lidhen me përfaqësimin rajonal.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 65,
                "peerAverage": 62,
                "globalBenchmark": 70,
                "description": "Llogaridhënia ndaj publikut dhe transparenca.",
                "commentary": """Nuk është i lidhur me afera të mëdha korruptive, duke ruajtur një
profil relativisht të pastër. Megjithatë, si pjesë e klasës politike, transparenca
mbetet një sfidë e vazhdueshme.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 80,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Lidhja me zonën zgjedhore dhe përgjigja ndaj nevojave të komunitetit.",
                "commentary": """Ka një lidhje të fortë historike me zonën e tij zgjedhore në Veri të
Shqipërisë. Njihet si një zë që artikulon shqetësimet e komunitetit të tij.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 70,
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": """Si lider i një partie të vogël, ndikimi i tij legjislativ është i
kufizuar. Megjithatë, ai arrin të ketë një ndikim të konsiderueshëm në debatin
publik përmes pranisë së tij të vazhdueshme mediatike.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 50,
                "peerAverage": 67,
                "globalBenchmark": 73,
                "description": "Kontributi në forcimin e institucioneve demokratike.",
                "commentary": """Kritik ndaj institucioneve aktuale, por kontributi i tij në
forcimin e tyre mbetet modest, duke reflektuar rolin e tij opozitar dhe si parti
e vogël.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 85,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Roli në ruajtjen e unitetit partiak.",
                "commentary": """Si themelues dhe lider i padiskutueshëm i PDK-së, ai ruan një
kontroll të plotë dhe kohezion të lartë brenda partisë së tij.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 90,
                "peerAverage": 71,
                "globalBenchmark": 74,
                "description": "Efektiveti dhe qartësia e komunikimit publik.",
                "commentary": """Pika e tij më e fortë. Ka një stil komunikimi unik, të drejtpërdrejtë
dhe shpesh me nota humori, që e bën një figurë shumë të njohur dhe shpesh virale
në media e rrjete sociale.""",
            },
        ],
    },
]

# Placeholder MPs – generated in bulk (same as many createPlaceholderMP(...) calls)
_PLACEHOLDER_MPS: List[tuple] = [
    ("mp49", "Kliti Hoti", "PD-ASHM"),
    ("mp50", "Greta Bardeli", "PD-ASHM"),
    ("mp51", "Ramadan Likaj", "PD-ASHM"),
    ("mp52", "Bardh Spahia", "PD-ASHM"),
    ("mp53", "Marjana Koçeku", "PS"),
    ("mp54", "Onid Bejleri", "PS"),
    ("mp55", "Xhenis Çela", "PS"),
    ("mp56", "Bujar Rexha", "PS"),
    ("mp57", "Tom Doshi", "PSD"),
    ("mp58", "Sabina Jorgo", "PSD"),
    ("mp59", "Flamur Hoxha", "PD-ASHM"),
    ("mp60", "Shkëlqim Shehu", "PD-ASHM"),
    ("mp61", "Eduard Shalsi", "PS"),
    ("mp62", "Elda Hoti", "PD-ASHM"),
    ("mp63", "Gjin Gjoni", "PD-ASHM"),
    ("mp64", "Kastriot Piroli", "PD-ASHM"),
    ("mp65", "Ulsi Manja", "PS"),
    ("mp66", "Ermal Pacaj", "PS"),
    ("mp67", "Marjeta Neli", "PS"),
    ("mp68", "Blendi Klosi", "PS"),
    ("mp69", "Alma Selami", "PS"),
    ("mp70", "Agron Malaj", "PS"),
    ("mp71", "Xhelal Mziu", "PD-ASHM"),
    ("mp72", "Denisa Vata", "PD-ASHM"),
    ("mp73", "Xhemal Gjunkshi", "PD-ASHM"),
    ("mp74", "Përparim Spahiu", "PD-ASHM"),
    ("mp75", "Klodiana Spahiu", "PS"),
    ("mp76", "Milva Ekonomi", "PS"),
    ("mp77", "Loer Kume", "PS"),
    ("mp78", "Skënder Pashaj", "PS"),
    ("mp79", "Aurora Mara", "PS"),
    ("mp80", "Arkend Balla", "PS"),
    ("mp81", "Ani Dyrmishi", "PS"),
    ("mp82", "Ilir Ndraxhi", "PS"),
    ("mp83", "Oerd Bylykbashi", "PD-ASHM"),
    ("mp84", "Artan Luku", "PD-ASHM"),
    ("mp85", "Manjola Luku", "PD-ASHM"),
    ("mp86", "Gent Strazimiri", "PD-ASHM"),
    ("mp87", "Igli Cara", "PD-ASHM"),
    ("mp88", "Arian Ndoja", "PD-ASHM"),
    ("mp89", "Aulon Kalaja", "PD-ASHM"),
    ("mp90", "Arbjan Mazniku", "PS"),
    ("mp91", "Bora Muzhaqi", "PS"),
    ("mp92", "Ermal Elezi", "PS"),
    ("mp93", "Adi Qose", "PS"),
    ("mp94", "Evis Kushi", "PS"),
    ("mp95", "Sara Mila", "PS"),
    ("mp96", "Saimir Hasalla", "PS"),
    ("mp97", "Olsi Komici", "PS"),
    ("mp98", "Aulona Bylykbashi", "PS"),
    ("mp99", "Agron Gaxho", "PS"),
    ("mp100", "Tomor Alizoti", "PD-ASHM"),
    ("mp101", "Edmond Haxhinasto", "PD-ASHM"),
    ("mp102", "Klodiana Çapja", "PD-ASHM"),
    ("mp103", "Blendi Himçi", "PD-ASHM"),
    ("mp104", "Petrit Malaj", "PS"),
    ("mp105", "Kiduina Zaka", "PS"),
    ("mp106", "Erjo Mile", "PS"),
    ("mp107", "Ana Nako", "PS"),
    ("mp108", "Ceno Klosi", "PS"),
    ("mp109", "Klevis Jahaj", "PS"),
    ("mp110", "Asfloral Haxhiu", "PS"),
    ("mp111", "Antoneta Dhima", "PS"),
    ("mp112", "Elton Korreshi", "PS"),
    ("mp113", "Zegjine Çaushi", "PS"),
    ("mp114", "Dhimitër Kruti", "PS"),
    ("mp115", "Luan Baçi", "PD-ASHM"),
    ("mp116", "Brunilda Haxhiu", "PD-ASHM"),
    ("mp117", "Saimir Korreshi", "PD-ASHM"),
    ("mp118", "Ervin Demo", "PS"),
    ("mp119", "Enriketa Jaho", "PS"),
    ("mp120", "Hysen Buzali", "PS"),
    ("mp121", "Fadil Nasufi", "PS"),
    ("mp122", "Julian Zyla", "PS"),
    ("mp123", "Enno Bozdo", "PD-ASHM"),
    ("mp124", "Zija Ismaili", "PD-ASHM"),
    ("mp125", "Niko Peleshi", "PS"),
    ("mp126", "Romina Kuko", "PS"),
    ("mp127", "Genti Lakollari", "PS"),
    ("mp128", "Ilirian Pendavinji", "PS"),
    ("mp129", "Bledi Çomo", "PS"),
    ("mp130", "Arian Jaupllari", "PS"),
    ("mp131", "Ivi Kaso", "PD-ASHM"),
    ("mp132", "Ledina Allolli", "PD-ASHM"),
    ("mp133", "Bledjon Nallbati", "PD-ASHM"),
    ("mp134", "Fidel Kreka", "PD-ASHM"),
    ("mp135", "Kristjano Koçibelli", "PD-ASHM"),
    ("mp136", "Mirela Furxhi", "PS"),
    ("mp137", "Tërmet Peçi", "PS"),
    ("mp138", "Piro Dhima", "PS"),
    ("mp139", "Tritan Shehu", "PD-ASHM"),
    ("mp140", "Bledar Çuçi", "PS"),
    ("mp141", "Zamira Sinaj", "PS"),
    ("mp142", "Erjona Ismaili", "PS"),
    ("mp143", "Pirro Vengu", "PS"),
    ("mp144", "Damian Gjiknuri", "PS"),
    ("mp145", "Vullnet Sinaj", "PS"),
    ("mp146", "Ardit Bido", "PS"),
    ("mp147", "Vasil Llajo", "PS"),
    ("mp148", "Brunilda Mersini", "PS"),
    ("mp149", "Bujar Leskaj", "PD-ASHM"),
    ("mp150", "Vangjel Dule", "PD-ASHM"),
    ("mp151", "Ina Zhupa", "PD-ASHM"),
    ("mp152", "Ogerta Manastirliu", "PS"),
    ("mp153", "Elisa Spiropali", "PS"),
    ("mp154", "Adea Pirdeni", "PS"),
    ("mp155", "Albana Kociu", "PS"),
    ("mp156", "Igli Hasani", "PS"),
    ("mp157", "Delina Ibrahimaj", "PS"),
    ("mp158", "Ilva Gjuzi", "PS"),
    ("mp159", "Iris Luarasi", "PS"),
    ("mp160", "Erjon Malaj", "PS"),
    ("mp161", "Blendi Gonxhja", "PS"),
    ("mp162", "Ervin Hoxha", "PS"),
    ("mp163", "Erion Braçe", "PS"),
    ("mp164", "Fatmir Xhafaj", "PS"),
    ("mp165", "Ornaldo Rakipi", "PS"),
    ("mp166", "Xhemal Qefalia", "PS"),
    ("mp167", "Anila Denaj", "PS"),
    ("mp168", "Edi Paloka", "PD-ASHM"),
    ("mp169", "Albana Vokshi", "PD-ASHM"),
    ("mp170", "Flamur Noka", "PD-ASHM"),
    ("mp171", "Jozefina Topalli", "PD-ASHM"),
    ("mp172", "Besart Xhaferri", "PD-ASHM"),
    ("mp173", "Fatmir Mediu", "PD-ASHM"),
    ("mp174", "Erisa Xhixho", "PD-ASHM"),
    ("mp175", "Klevis Balliu", "PD-ASHM"),
    ("mp176", "Mesila Doda", "PD-ASHM"),
    ("mp177", "Tedi Blushi", "PD-ASHM"),
    ("mp178", "Ilir Alimehmeti", "PD-ASHM"),
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
        "shortBio": """Gazetar dhe drejtues i emisionit "Opinion" në TV Klan.""",
        "detailedBio": """Blendi Fevziu është një nga gazetarët dhe opinionistët më të njohur në Shqipëri.
Ai drejton emisionin politik "Opinion" në TV Klan, i cili është një ndër emisionet
më të ndjekura dhe me ndikim në vend. Fevziu është gjithashtu autor i disa librave,
shpesh me tematikë historike dhe biografike. Ai njihet për stilin e tij direkt dhe
aftësinë për të moderuar debate të nxehta politike.""",
        "zodiacSign": "Cancer",
        "maragonAnalysis": [
            {
                "dimension": "Pajtueshmëria Etike",
                "score": 88,
                "peerAverage": 75,
                "globalBenchmark": 92,
                "description": """Pajtueshmëria themelore me standardet etike/operacionale,
siç përcaktohet në Kodin e Standardeve.""",
                "commentary": """Ruan një reputacion të fortë etik, duke e mbajtur emisionin larg
skandaleve të mëdha etike. Mban distancë profesionale nga subjektet që mbulon,
në përputhje me parimet e pavarësisë.""",
            },
            {
                "dimension": "Profesionalizmi në Kriza",
                "score": 85,
                "peerAverage": 78,
                "globalBenchmark": 85,
                "description": """Aftësia për të ruajtur qetësinë dhe standardet profesionale
gjatë lajmeve të fundit ose debateve të tensionuara.""",
                "commentary": """Ka përvojë të gjatë në menaxhimin e situatave live me tension të lartë.
Ndonëse ndonjëherë ndërpret të ftuarit, arrin të mbajë kontrollin e debatit pa
lejuar përshkallëzim.""",
            },
            {
                "dimension": "Saktësia Faktike & Verifikimi",
                "score": 85,
                "peerAverage": 72,
                "globalBenchmark": 88,
                "description": """Rigoroziteti në verifikimin e informacionit para transmetimit,
atribuimin e saktë të burimeve dhe dallimin e qartë midis faktit dhe opinionit.""",
                "commentary": """Fevziu tregon një nivel të lartë të përgatitjes, por shpejtësia e
formatit live ndonjëherë lejon pasaktësi të vogla. Mbështetet shumë në reputacionin
e të ftuarve.""",
            },
            {
                "dimension": "Paanshmëria, Balanca & Anshmëria",
                "score": 78,
                "peerAverage": 65,
                "globalBenchmark": 90,
                "description": """Mat aftësinë për të moderuar debatin në mënyrë të paanshme,
duke u dhënë kohë dhe hapësirë të barabartë të gjitha palëve.""",
                "commentary": """Ndonëse synon paanshmëri, stili i tij konfrontues dhe ndërprerjet e
shpeshta mund të perceptohen si favorizim ose si mungesë ekuilibri nga audienca.""",
            },
            {
                "dimension": "Thellësia e Analizës/Pyetjeve",
                "score": 82,
                "peerAverage": 75,
                "globalBenchmark": 88,
                "description": """Aftësia për të bërë pyetje të thelluara, për të ndjekur përgjigjet
dhe për të demonstruar njohuri të thella mbi temën.""",
                "commentary": """Shpesh bën pyetje të mprehta dhe direkte, por dinamika e debatit me
shumë të ftuar e pengon të thellohet sa duhet në një çështje të vetme.""",
            },
            {
                "dimension": "Qartësia & Koherenca",
                "score": 95,
                "peerAverage": 80,
                "globalBenchmark": 90,
                "description": """Qartësia e të folurit, artikulimi dhe aftësia për të menaxhuar rrjedhën
logjike të një debati ose interviste.""",
                "commentary": """Një nga pikat e tij më të forta. Është një komunikues i shkëlqyer,
i shpejtë dhe me aftësi të jashtëzakonshme për të mbajtur vëmendjen e audiencës.""",
            },
            {
                "dimension": "Promovimi i të Menduarit Kritik",
                "score": 75,
                "peerAverage": 70,
                "globalBenchmark": 85,
                "description": """Inkurajimi i audiencës për të konsideruar perspektiva të shumëfishta
dhe për të sfiduar supozimet e tyre.""",
                "commentary": """Duke sjellë zëra të ndryshëm, ai ekspozon publikun ndaj këndvështrimeve
të ndryshme, por formati i debatit shpesh favorizon përplasjen më shumë sesa
reflektimin e thellë.""",
            },
        ],
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/Opinion_Albanian_TV_program_logo.jpeg",
        "audienceRating": 88,
        "audienceDemographics": {
            "age": "45-65",
            "gender": "65% Meshkuj",
            "location": "Urban & Rural",
        },
    },
    {
        "id": "vip41",
        "name": "Grida Duma",
        "imageUrl": generate_profile_photo_url("Grida Duma"),
        "category": "Media",
        "shortBio": """Analiste politike dhe drejtuese e emisionit "Top Story" në Top Channel.""",
        "detailedBio": """Grida Duma është një figurë e shquar publike në Shqipëri, e njohur për
karrierën e saj si politikane e nivelit të lartë në Partinë Demokratike dhe së fundmi
si një analiste dhe drejtuese me ndikim në media. Pas një karriere intensive politike
si deputete dhe zë i fuqishëm opozitar, ajo bëri një lëvizje të bujshme duke marrë
drejtimin e emisionit investigativ "Top Story" në Top Channel. Ajo njihet për stilin
e saj elokuent, të artikuluar dhe pyetjet e mprehta, duke sjellë në ekran një
perspektivë unike që ndërthur përvojën e brendshme politike me rolin e moderatores.""",
        "zodiacSign": "Virgo",
        "maragonAnalysis": [
            {
                "dimension": "Pajtueshmëria Etike",
                "score": 87,
                "peerAverage": 75,
                "globalBenchmark": 92,
                "description": """Pajtueshmëria themelore me standardet etike/operacionale,
siç përcaktohet në Kodin e Standardeve.""",
                "commentary": """Ka bërë një tranzicion profesional nga politika në media, duke iu
përmbajtur linjave etike të vendosura nga Top Channel dhe emisioni "Top Story".""",
            },
            {
                "dimension": "Profesionalizmi në Kriza",
                "score": 90,
                "peerAverage": 78,
                "globalBenchmark": 85,
                "description": """Aftësia për të ruajtur qetësinë dhe standardet profesionale
gjatë lajmeve të fundit ose debateve të tensionuara.""",
                "commentary": """Eksperienca e saj e gjatë politike i jep një aftësi të
jashtëzakonshme për të ruajtur qetësinë dhe kontrollin gjatë debateve të
tensionuara live, duke menaxhuar me autoritet të ftuar të vështirë.""",
            },
            {
                "dimension": "Saktësia Faktike & Verifikimi",
                "score": 91,
                "peerAverage": 72,
                "globalBenchmark": 88,
                "description": """Rigoroziteti në verifikimin e informacionit para transmetimit,
atribuimin e saktë të burimeve dhe dallimin e qartë midis faktit dhe opinionit.""",
                "commentary": """"Top Story" ka një traditë të gazetarisë investigative.
Duma e vazhdon këtë linjë me tema të mirë-hulumtuara dhe një fokus të fortë te
faktet e dokumentuara.""",
            },
            {
                "dimension": "Paanshmëria, Balanca & Anshmëria",
                "score": 75,
                "peerAverage": 65,
                "globalBenchmark": 90,
                "description": """Mat aftësinë për të moderuar debatin në mënyrë të paanshme,
duke u dhënë kohë dhe hapësirë të barabartë të gjitha palëve.""",
                "commentary": """Ky mbetet dimensioni i saj më sfidues. Për shkak të karrierës së
saj të afërt si figurë e lartë e opozitës, ajo përballet vazhdimisht me akuza për
anshmëri. Megjithatë, përpiqet të moderojë debate të balancuara.""",
            },
            {
                "dimension": "Thellësia e Analizës/Pyetjeve",
                "score": 92,
                "peerAverage": 75,
                "globalBenchmark": 88,
                "description": """Aftësia për të bërë pyetje të thelluara, për të ndjekur përgjigjet
dhe për të demonstruar njohuri të thella mbi temën.""",
                "commentary": """Përvoja e saj direkte në politikë i jep një avantazh unik. Ajo bën
pyetje të thella dhe incizive që shkojnë përtej sipërfaqes, shpesh duke i sfiduar
politikanët nga një pozicion i njohjes së brendshme.""",
            },
            {
                "dimension": "Qartësia & Koherenca",
                "score": 94,
                "peerAverage": 80,
                "globalBenchmark": 90,
                "description": """Qartësia e të folurit, artikulimi dhe aftësia për të menaxhuar rrjedhën
logjike të një debati ose interviste.""",
                "commentary": """Një nga pikat e saj më të forta. Është tejet e artikuluar, me një stil
komunikimi të qartë dhe koherent që i bën temat komplekse të kuptueshme.""",
            },
            {
                "dimension": "Promovimi i të Menduarit Kritik",
                "score": 86,
                "peerAverage": 70,
                "globalBenchmark": 85,
                "description": """Inkurajimi i audiencës për të konsideruar perspektiva të shumëfishta
dhe për të sfiduar supozimet e tyre.""",
                "commentary": """Përmes prezantimit të dosjeve të detajuara investigative dhe pyetjeve
sfiduese, ajo e nxit vazhdimisht audiencën të vërë në dyshim narrativat zyrtare
dhe të analizojë çështjet në mënyrë kritike.""",
            },
        ],
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/TopStory.jpg",
        "audienceRating": 91,
        "audienceDemographics": {
            "age": "35-55",
            "gender": "55% Meshkuj",
            "location": "Urban",
        },
    },
    {
        "id": "vip5",
        "name": "Ardit Gjebrea",
        "imageUrl": generate_profile_photo_url("Ardit Gjebrea"),
        "category": "Media & Showbiz",
        "shortBio": 'Këngëtar, producent dhe drejtues i "E Diela Shqiptare".',
        "detailedBio": """Ardit Gjebrea është një figurë poliedrike në skenën shqiptare, i njohur
si këngëtar, kompozitor, producent televiziv dhe prezantues. Ai është krijuesi dhe
drejtuesi i programit maratonë të së dielës "E Diela Shqiptare" në TV Klan.
Gjebrea ka një karrierë të gjatë në muzikë, duke filluar që në moshë të re, dhe ka
organizuar disa nga festivalet më të rëndësishme muzikore në Shqipëri, si
"Kënga Magjike".""",
        "zodiacSign": "Gemini",
        "maragonAnalysis": generate_maragon_analysis("Ardit Gjebrea"),
        "tvShowLogoUrl": "https://www.tvklan.al/wp-content/uploads/2022/01/EDIELA-SHQIPTARE-1.png",
        "audienceRating": 95,
        "audienceDemographics": {
            "age": "18-65+",
            "gender": "70% Femra",
            "location": "Kombëtare",
        },
    },
    {
        "id": "vip9",
        "name": "Sokol Balla",
        "imageUrl": generate_profile_photo_url("Sokol Balla"),
        "category": "Media",
        "shortBio": 'Gazetar dhe analist politik, drejtues i emisionit "Real Story".',
        "detailedBio": """Sokol Balla është një gazetar dhe analist i njohur, me një karrierë të gjatë
në mediat kryesore shqiptare. Ai aktualisht drejton emisionin "Real Story", ku
analizon zhvillimet politike dhe sociale me të ftuar kyç.""",
        "zodiacSign": "Sagittarius",
        "maragonAnalysis": [
            {
                "dimension": "Pajtueshmëria Etike",
                "score": 85,
                "peerAverage": 75,
                "globalBenchmark": 92,
                "description": """Pajtueshmëria themelore me standardet etike/operacionale,
siç përcaktohet në Kodin e Standardeve.""",
                "commentary": """Njihet për një karrierë pa kompromise të mëdha etike. Mban një linjë
të qartë profesionale, duke respektuar parimet e gazetarisë së përgjegjshme.""",
            },
            {
                "dimension": "Profesionalizmi në Kriza",
                "score": 82,
                "peerAverage": 78,
                "globalBenchmark": 85,
                "description": """Aftësia për të ruajtur qetësinë dhe standardet profesionale
gjatë lajmeve të fundit ose debateve të tensionuara.""",
                "commentary": """Si një gazetar me përvojë, ai menaxhon mirë situatat e paparashikuara
live, duke ruajtur një qasje të matur dhe profesionale.""",
            },
            {
                "dimension": "Saktësia Faktike & Verifikimi",
                "score": 82,
                "peerAverage": 72,
                "globalBenchmark": 88,
                "description": """Rigoroziteti në verifikimin e informacionit para transmetimit,
atribuimin e saktë të burimeve dhe dallimin e qartë midis faktit dhe opinionit.""",
                "commentary": """Balla shfaq një përkushtim të mirë ndaj verifikimit, por nganjëherë
mbështetet te burime politike që kërkojnë verifikim të mëtejshëm nga shikuesi.""",
            },
            {
                "dimension": "Paanshmëria, Balanca & Anshmëria",
                "score": 75,
                "peerAverage": 65,
                "globalBenchmark": 90,
                "description": """Mat aftësinë për të moderuar debatin në mënyrë të paanshme,
duke u dhënë kohë dhe hapësirë të barabartë të gjitha palëve.""",
                "commentary": """Përpiqet të mbajë një qasje të ekuilibruar, por dinamika e debatit
dhe përzgjedhja e të ftuarve mund të anojë ndonjëherë pa dashje.""",
            },
            {
                "dimension": "Thellësia e Analizës/Pyetjeve",
                "score": 88,
                "peerAverage": 75,
                "globalBenchmark": 88,
                "description": """Aftësia për të bërë pyetje të thelluara, për të ndjekur përgjigjet
dhe për të demonstruar njohuri të thella mbi temën.""",
                "commentary": """Demonstron njohuri të thella mbi çështjet që trajton dhe është i aftë
të bëjë pyetje sfiduese që shkojnë përtej sipërfaqes.""",
            },
            {
                "dimension": "Qartësia & Koherenca",
                "score": 88,
                "peerAverage": 80,
                "globalBenchmark": 90,
                "description": """Qartësia e të folurit, artikulimi dhe aftësia për të menaxhuar rrjedhën
logjike të një debati ose interviste.""",
                "commentary": """Komunikues i qartë dhe moderator i aftë. Ai e strukturon debatin në
mënyrë logjike dhe koherente, duke e bërë të lehtë për t'u ndjekur.""",
            },
            {
                "dimension": "Promovimi i të Menduarit Kritik",
                "score": 80,
                "peerAverage": 70,
                "globalBenchmark": 85,
                "description": """Inkurajimi i audiencës për të konsideruar perspektiva të shumëfishta
dhe për të sfiduar supozimet e tyre.""",
                "commentary": """Përmes pyetjeve të tij dhe konfrontimit të ideve, ai inkurajon një
nivel të të menduarit kritik, megjithëse fokusi mbetet te debati politik.""",
            },
        ],
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/real-story-abc-2.jpg",
        "audienceRating": 82,
        "audienceDemographics": {
            "age": "40-60",
            "gender": "60% Meshkuj",
            "location": "Urban",
        },
    },
    {
        "id": "vip10",
        "name": "Eni Vasili",
        "imageUrl": generate_profile_photo_url("Eni Vasili"),
        "category": "Media",
        "shortBio": 'Gazetare dhe drejtuese e emisionit "Open" në Top Channel.',
        "detailedBio": """Eni Vasili është një gazetare dhe moderatore e njohur, e cila drejton
emisionin e debatit politik "Open". Ajo njihet për stilin e saj energjik dhe aftësinë
për të menaxhuar debate të nxehta me figura të rëndësishme publike.""",
        "zodiacSign": "Aries",
        "maragonAnalysis": [
            {
                "dimension": "Pajtueshmëria Etike",
                "score": 86,
                "peerAverage": 75,
                "globalBenchmark": 92,
                "description": """Pajtueshmëria themelore me standardet etike/operacionale,
siç përcaktohet në Kodin e Standardeve.""",
                "commentary": """Ruan standarde të larta etike, duke u fokusuar te përmbajtja dhe jo
te skandalet personale apo profesionale. Tregon respekt për të ftuarit.""",
            },
            {
                "dimension": "Profesionalizmi në Kriza",
                "score": 90,
                "peerAverage": 78,
                "globalBenchmark": 85,
                "description": """Aftësia për të ruajtur qetësinë dhe standardet profesionale
gjatë lajmeve të fundit ose debateve të tensionuara.""",
                "commentary": """Shumë e aftë në menaxhimin e debateve të ashpra live, duke mbajtur
kontrollin e studios dhe duke de-përshkallëzuar tensionet në mënyrë profesionale.""",
            },
            {
                "dimension": "Saktësia Faktike & Verifikimi",
                "score": 88,
                "peerAverage": 72,
                "globalBenchmark": 88,
                "description": """Rigoroziteti në verifikimin e informacionit para transmetimit,
atribuimin e saktë të burimeve dhe dallimin e qartë midis faktit dhe opinionit.""",
                "commentary": """Tregon një rigorozitet të lartë në përgatitjen e temave dhe
verifikimin e fakteve, veçanërisht në dosjet investigative që prezanton.""",
            },
            {
                "dimension": "Paanshmëria, Balanca & Anshmëria",
                "score": 80,
                "peerAverage": 65,
                "globalBenchmark": 90,
                "description": """Mat aftësinë për të moderuar debatin në mënyrë të paanshme,
duke u dhënë kohë dhe hapësirë të barabartë të gjitha palëve.""",
                "commentary": """Arrin të jetë një moderatore e paanshme, duke u dhënë hapësirë
të gjitha palëve, edhe pse stili i saj energjik mund të perceptohet si ndërprerës.""",
            },
            {
                "dimension": "Thellësia e Analizës/Pyetjeve",
                "score": 85,
                "peerAverage": 75,
                "globalBenchmark": 88,
                "description": """Aftësia për të bërë pyetje të thelluara, për të ndjekur përgjigjet
dhe për të demonstruar njohuri të thella mbi temën.""",
                "commentary": """Bën pyetje direkte dhe të informuara, shpesh duke i vënë të ftuarit
përballë fakteve dhe duke kërkuar përgjigje konkrete.""",
            },
            {
                "dimension": "Qartësia & Koherenca",
                "score": 90,
                "peerAverage": 80,
                "globalBenchmark": 90,
                "description": """Qartësia e të folurit, artikulimi dhe aftësia për të menaxhuar rrjedhën
logjike të një debati ose interviste.""",
                "commentary": """Ka një komunikim shumë të qartë dhe një aftësi të spikatur për të
menaxhuar rrjedhën e një debati kompleks me shumë zëra.""",
            },
            {
                "dimension": "Promovimi i të Menduarit Kritik",
                "score": 82,
                "peerAverage": 70,
                "globalBenchmark": 85,
                "description": """Inkurajimi i audiencës për të konsideruar perspektiva të shumëfishta
dhe për të sfiduar supozimet e tyre.""",
                "commentary": """Duke përballur opinionet kundërshtuese në studio, ajo i ofron audiencës
material të pasur për të formuar gjykimin e vet.""",
            },
        ],
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/Open.jpg",
        "audienceRating": 85,
        "audienceDemographics": {
            "age": "30-55",
            "gender": "50% Meshkuj, 50% Femra",
            "location": "Urban",
        },
    },
    {
        "id": "vip11",
        "name": "Inva Mula",
        "imageUrl": generate_profile_photo_url("Inva Mula"),
        "category": "Art & Kulturë",
        "shortBio": "Soprano me famë ndërkombëtare.",
        "detailedBio": """Inva Mula është një soprano shqiptare me famë botërore. Ajo ka performuar në
skenat më prestigjioze të operës në botë dhe është një ambasadore e shquar e kulturës
shqiptare.""",
        "zodiacSign": "Gemini",
    },
    {
        "id": "vip13",
        "name": "Alketa Vejsiu",
        "imageUrl": generate_profile_photo_url("Alketa Vejsiu"),
        "category": "Media & Showbiz",
        "shortBio": "Prezantuese televizive, producente dhe sipërmarrëse.",
        "detailedBio": """Alketa Vejsiu është një figurë poliedrike në botën e medias shqiptare. E njohur
si prezantuese e disa prej spektakleve më të mëdha televizive, ajo është gjithashtu
një producente e suksesshme dhe sipërmarrëse në fushën e eventeve dhe modës.""",
        "zodiacSign": "Pisces",
        "maragonAnalysis": generate_maragon_analysis("Alketa Vejsiu"),
        "audienceRating": 78,
        "audienceDemographics": {
            "age": "18-35",
            "gender": "65% Femra",
            "location": "Urban",
        },
    },
    {
        "id": "vip14",
        "name": "Arian Çani",
        "imageUrl": generate_profile_photo_url("Arian Çani"),
        "category": "Media",
        "shortBio": 'Prezantues i emisionit "Zonë e Lirë" në ABC News.',
        "detailedBio": """Arian Çani është një figurë ikonike dhe provokuese e ekranit shqiptar.
Emisioni i tij "Zonë e Lirë" është një nga më jetëgjatët, i njohur për stilin e tij
jokonvencional, humorin dhe debatet e hapura pa filtra.""",
        "zodiacSign": "Libra",
        "maragonAnalysis": generate_maragon_analysis("Arian Çani"),
        "audienceRating": 75,
        "audienceDemographics": {
            "age": "25-50",
            "gender": "70% Meshkuj",
            "location": "Kombëtare",
        },
    },
    {
        "id": "vip15",
        "name": "Arbana Osmani",
        "imageUrl": generate_profile_photo_url("Arbana Osmani"),
        "category": "Media & Showbiz",
        "shortBio": 'Prezantuese e "Big Brother VIP Albania" në Top Channel.',
        "detailedBio": """Arbana Osmani është një nga prezantueset më të dashura dhe më të suksesshme
në Shqipëri. Ajo ka drejtuar formate të mëdha televizive, por njihet veçanërisht
për drejtimin e "Big Brother VIP Albania", fenomeni më i madh televiziv i viteve
të fundit.""",
        "zodiacSign": "Taurus",
        "maragonAnalysis": generate_maragon_analysis("Arbana Osmani"),
        "tvShowLogoUrl": "https://upload.wikimedia.org/wikipedia/en/thumb/5/52/Big_Brother_VIP_Albania_3.png/250px-Big_Brother_VIP_Albania_3.png",
        "audienceRating": 98,
        "audienceDemographics": {
            "age": "16-45",
            "gender": "60% Femra",
            "location": "Kombëtare & Diasporë",
        },
    },
    {
        "id": "vip16",
        "name": "Adi Krasta",
        "imageUrl": generate_profile_photo_url("Adi Krasta"),
        "category": "Media",
        "shortBio": "Gazetar dhe prezantues me karrierë të gjatë në media.",
        "detailedBio": """Adi Krasta është një gazetar, prezantues dhe publicist me një karrierë
të gjatë dhe me ndikim. I njohur për stilin e tij elokuent dhe intelektual, ai ka
drejtuar disa nga emisionet më të rëndësishme në historinë e televizionit shqiptar,
duke qenë një zë kritik dhe i pavarur.""",
        "zodiacSign": "Leo",
        "maragonAnalysis": generate_maragon_analysis("Adi Krasta"),
        "audienceRating": 79,
        "audienceDemographics": {
            "age": "40+",
            "gender": "60% Meshkuj",
            "location": "Urban",
        },
    },
    {
        "id": "vip17",
        "name": "Sonila Meço",
        "imageUrl": generate_profile_photo_url("Sonila Meço"),
        "category": "Media",
        "shortBio": "Gazetare, prezantuese lajmesh dhe drejtuese emisionesh.",
        "detailedBio": """Sonila Meço është një gazetare e njohur dhe figurë autoritative në median
shqiptare. Me një karrierë që përfshin prezantimin e edicioneve kryesore të lajmeve
dhe drejtimin e emisioneve politike, ajo njihet për profesionalizmin, qartësinë
dhe pyetjet e saj të mprehta.""",
        "zodiacSign": "Scorpio",
        "maragonAnalysis": generate_maragon_analysis("Sonila Meço"),
        "audienceRating": 84,
        "audienceDemographics": {
            "age": "35-60",
            "gender": "50% M, 50% F",
            "location": "Urban",
        },
    },
    {
        "id": "vip18",
        "name": "Marin Mema",
        "imageUrl": generate_profile_photo_url("Marin Mema"),
        "category": "Media",
        "shortBio": 'Gazetar investigativ, i njohur për emisionin "Gjurmë Shqiptare".',
        "detailedBio": """Marin Mema është një gazetar investigativ i vlerësuar, i famshëm për
emisionin e tij "Gjurmë Shqiptare". Puna e tij fokusohet në zbulimin e historisë,
kulturës dhe fateve të shqiptarëve brenda dhe jashtë kufijve, shpesh duke trajtuar
tema të ndjeshme kombëtare.""",
        "zodiacSign": "Capricorn",
        "maragonAnalysis": generate_maragon_analysis("Marin Mema"),
        "audienceRating": 93,
        "audienceDemographics": {
            "age": "25-65+",
            "gender": "55% Meshkuj",
            "location": "Kombëtare & Diasporë",
        },
    },
    {
        "id": "vip19",
        "name": "Blendi Salaj",
        "imageUrl": generate_profile_photo_url("Blendi Salaj"),
        "category": "Media & Radio",
        "shortBio": "Gazetar, prezantues radiofonik dhe aktivist i shoqërisë civile.",
        "detailedBio": """Blendi Salaj është një zë i njohur në radion shqiptare dhe një komentator
aktiv i jetës publike. I njohur për stilin e tij të hapur dhe shpeshherë ironik,
ai trajton çështje sociale dhe politike, duke u bërë një pikë referimi për audiencën
urbane dhe të re.""",
        "zodiacSign": "Gemini",
        "maragonAnalysis": generate_maragon_analysis("Blendi Salaj"),
        "audienceRating": 77,
        "audienceDemographics": {
            "age": "20-40",
            "gender": "50% M, 50% F",
            "location": "Urban (Tiranë)",
        },
    },
    {
        "id": "vip20",
        "name": "Enkel Demi (Tomi)",
        "imageUrl": generate_profile_photo_url("Enkel Demi (Tomi)"),
        "category": "Media & Letërsi",
        "shortBio": 'Gazetar, shkrimtar dhe drejtues i emisionit "Shih Programin".',
        "detailedBio": """Enkel Demi, i njohur gjerësisht si Tomi, është një gazetar, shkrimtar dhe
figurë intelektuale. Me një stil unik që ndërthur komentin social, kulturën dhe
humorin, ai ka krijuar një hapësirë të veçantë në median shqiptare, duke u vlerësuar
për thellësinë e analizave të tij.""",
        "zodiacSign": "Cancer",
        "maragonAnalysis": generate_maragon_analysis("Enkel Demi (Tomi)"),
        "audienceRating": 76,
        "audienceDemographics": {
            "age": "35+",
            "gender": "55% Meshkuj",
            "location": "Urban",
        },
    },
    {
        "id": "vip21",
        "name": "Armina Mevlani",
        "imageUrl": generate_profile_photo_url("Armina Mevlani"),
        "category": "Showbiz & Influencer",
        "shortBio": "Blogere mode, sipërmarrëse dhe personazh mediatik.",
        "detailedBio": """Armina Mevlani është një nga influencueset dhe blogeret më të njohura të
modës në Shqipëri. Ajo ka ndërtuar një markë të fortë personale dhe është një figurë
me ndikim në botën e showbiz-it, modës dhe sipërmarrjes.""",
        "zodiacSign": "Sagittarius",
        "maragonAnalysis": generate_maragon_analysis("Armina Mevlani"),
        "audienceRating": 68,
        "audienceDemographics": {
            "age": "18-30",
            "gender": "80% Femra",
            "location": "Urban",
        },
    },
    {
        "id": "vip22",
        "name": "Bledi Mane",
        "imageUrl": generate_profile_photo_url("Bledi Mane"),
        "category": "Media",
        "shortBio": "Gazetar i njohur për stilin e tij provokues dhe pa kompromis.",
        "detailedBio": """Bledi Mane është një gazetar i njohur për stilin e tij të drejtpërdrejtë,
provokues dhe shpesh polemizues. Ai nuk heziton të trajtojë tema tabu dhe të sfidojë
figura publike, duke krijuar shpesh debate të nxehta mediatike.""",
        "zodiacSign": "Aries",
        "maragonAnalysis": generate_maragon_analysis("Bledi Mane"),
        "audienceRating": 65,
        "audienceDemographics": {
            "age": "20-45",
            "gender": "65% Meshkuj",
            "location": "Kombëtare",
        },
    },
    {
        "id": "vip23",
        "name": "Mustafa Nano",
        "imageUrl": generate_profile_photo_url("Mustafa Nano"),
        "category": "Media",
        "shortBio": "Publicist, analist dhe drejtues emisioni.",
        "detailedBio": """Mustafa Nano është një publicist dhe analist i shquar, i njohur për
qëndrimet e tij shpesh kundër rrymës dhe analizat kritike ndaj fenomeneve politike,
sociale dhe fetare në Shqipëri. Stili i tij polemik e bën atë një zë të veçantë dhe
me ndikim në debatin publik.""",
        "zodiacSign": "Virgo",
        "maragonAnalysis": generate_maragon_analysis("Mustafa Nano"),
        "audienceRating": 74,
        "audienceDemographics": {
            "age": "40+",
            "gender": "70% Meshkuj",
            "location": "Urban",
        },
    },
    {
        "id": "vip24",
        "name": "Ermal Peçi",
        "imageUrl": generate_profile_photo_url("Ermal Peçi"),
        "category": "Media & Showbiz",
        "shortBio": "Prezantues televiziv, i njohur për emisione argëtuese.",
        "detailedBio": """Ermal Peçi është një prezantues televiziv i njohur, i fokusuar kryesisht
në emisione argëtuese dhe intervista me personazhe të showbiz-it. Ai njihet për
stilin e tij pozitiv dhe energjik.""",
        "zodiacSign": "Libra",
        "maragonAnalysis": generate_maragon_analysis("Ermal Peçi"),
        "audienceRating": 72,
        "audienceDemographics": {
            "age": "18-40",
            "gender": "60% Femra",
            "location": "Kombëtare",
        },
    },
    {
        "id": "vip25",
        "name": "Ilva Tare",
        "imageUrl": generate_profile_photo_url("Ilva Tare"),
        "category": "Media",
        "shortBio": 'Gazetare me përvojë dhe ish-drejtuese e "Tonight Ilva Tare".',
        "detailedBio": """Ilva Tare është një nga figurat më të respektuara të gazetarisë shqiptare.
Për shumë vite, emisioni i saj "Tonight Ilva Tare" ishte një platformë qendrore për
debatin politik në vend. Ajo njihet për profesionalizmin, paanshmërinë dhe
standardet e larta etike.""",
        "zodiacSign": "Aquarius",
        "maragonAnalysis": generate_maragon_analysis("Ilva Tare"),
        "audienceRating": 87,
        "audienceDemographics": {
            "age": "35-60",
            "gender": "55% Meshkuj",
            "location": "Urban",
        },
    },
    {
        "id": "vip26",
        "name": "Dalina Buzi",
        "imageUrl": generate_profile_photo_url("Dalina Buzi"),
        "category": "Media & Produksion",
        "shortBio": 'Gazetare, skenariste dhe themeluese e "Anabel Media".',
        "detailedBio": """Dalina Buzi është një sipërmarrëse e suksesshme mediatike, e njohur si
themeluesja e "Anabel Media". Ajo është gjithashtu një skenariste dhe producente,
duke krijuar përmbajtje që rezonon fuqishëm me audiencën e re dhe femërore në Shqipëri.""",
        "zodiacSign": "Leo",
        "maragonAnalysis": generate_maragon_analysis("Dalina Buzi"),
        "audienceRating": 81,
        "audienceDemographics": {
            "age": "18-35",
            "gender": "85% Femra",
            "location": "Urban",
        },
    },
    {
        "id": "vip27",
        "name": "Ledion Liço",
        "imageUrl": generate_profile_photo_url("Ledion Liço"),
        "category": "Media & Showbiz",
        "shortBio": "Prezantues dhe producent televiziv.",
        "detailedBio": """Ledion Liço është një prezantues dhe producent televiziv me një karrierë
të gjatë. I njohur për stilin e tij modern dhe energjik, ai ka drejtuar disa nga
formatet më të mëdha të argëtimit dhe talent-show në Shqipëri.""",
        "zodiacSign": "Aries",
        "maragonAnalysis": generate_maragon_analysis("Ledion Liço"),
        "audienceRating": 80,
        "audienceDemographics": {
            "age": "16-40",
            "gender": "60% Femra",
            "location": "Kombëtare",
        },
    },
    {
        "id": "vip28",
        "name": "Dritan Shakohoxha",
        "imageUrl": generate_profile_photo_url("Dritan Shakohoxha"),
        "category": "Gazetari Sportive",
        "shortBio": "Komentator i njohur sportiv.",
        "detailedBio": """Dritan Shakohoxha është "zëri" i futbollit në Shqipëri. Si komentatori më i
famshëm sportiv, ai njihet për pasionin, emocionin dhe stilin e tij unik të
komentimit, veçanërisht gjatë ndeshjeve të Kombëtares Shqiptare.""",
        "zodiacSign": "Taurus",
        "maragonAnalysis": generate_maragon_analysis("Dritan Shakohoxha"),
        "audienceRating": 96,
        "audienceDemographics": {
            "age": "16-60",
            "gender": "80% Meshkuj",
            "location": "Kombëtare & Diasporë",
        },
    },
    {
        "id": "vip32",
        "name": "Ylli Rakipi",
        "imageUrl": generate_profile_photo_url("Ylli Rakipi"),
        "category": "Media",
        "shortBio": 'Gazetar dhe drejtues i emisionit "Të Paekspozuarit".',
        "detailedBio": """Ylli Rakipi është një gazetar investigativ dhe drejtues i emisionit
"Të Paekspozuarit". Ai njihet për stilin e tij kritik dhe pa kompromis ndaj
pushtetit, duke u fokusuar në denoncimin e aferave korruptive dhe abuzimeve.""",
        "zodiacSign": "Scorpio",
        "maragonAnalysis": generate_maragon_analysis("Ylli Rakipi"),
        "tvShowLogoUrl": "https://novaric.co/wp-content/uploads/2025/11/TPaEks.jpg",
        "audienceRating": 78,
        "audienceDemographics": {
            "age": "45+",
            "gender": "75% Meshkuj",
            "location": "Kombëtare",
        },
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
        "shortBio": "Aktor, moderator, producent dhe sipërmarrës.",
        "detailedBio": """Ermal Mamaqi është një figurë shumëplanëshe, i njohur si aktor humori,
moderator, producent filmash dhe së fundmi si sipërmarrës dhe trajner motivimi.
Ai ka arritur sukses të konsiderueshëm në botën e showbiz-it dhe ka zgjeruar
aktivitetin e tij në fushën e biznesit dhe zhvillimit personal.""",
        "zodiacSign": "Aquarius",
        "maragonAnalysis": generate_maragon_analysis("Ermal Mamaqi"),
        "audienceRating": 83,
        "audienceDemographics": {
            "age": "25-45",
            "gender": "50% M, 50% F",
            "location": "Urban",
        },
    },
    {
        "id": "vip31",
        "name": "Samir Mane",
        "imageUrl": generate_profile_photo_url("Samir Mane"),
        "category": "Biznes",
        "shortBio": "President i Grupit BALFIN, një nga sipërmarrësit më të suksesshëm.",
        "detailedBio": """Samir Mane është themeluesi dhe Presidenti i Grupit BALFIN, një nga
grupet më të mëdha të investimeve private në Shqipëri dhe rajon. Aktivitetet e tij
shtrihen në fusha si pasuritë e paluajtshme, shitjet me pakicë (me rrjetet NEPTUN
dhe SPAR), industria minerare dhe turizmi. Ai konsiderohet një nga biznesmenët më
të fuqishëm dhe me ndikim në ekonominë shqiptare.""",
        "zodiacSign": "Leo",
        "paragonAnalysis": [
            {
                "dimension": "Policy Engagement & Expertise",
                "score": 92,
                "peerAverage": 80,
                "globalBenchmark": 85,
                "description": """Vizioni i Biznesit & Inovacioni: Aftësia për të identifikuar dhe
shfrytëzuar mundësi të reja tregu.""",
                "commentary": """Ka treguar një aftësi të jashtëzakonshme për të diversifikuar
portofolin e investimeve, nga pasuritë e paluajtshme te shitjet me pakicë dhe
turizmi, duke e bërë Grupin BALFIN lider rajonal.""",
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": 88,
                "peerAverage": 82,
                "globalBenchmark": 84,
                "description": """Lidershipi dhe Menaxhimi: Stili i menaxhimit dhe aftësia për të
udhëhequr një grup të madh.""",
                "commentary": """Stil menaxherial efektiv dhe i orientuar drejt rritjes. Ka ndërtuar
një ekip të fortë menaxherial, por vendimet strategjike mbeten të centralizuara.""",
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": 90,
                "peerAverage": 78,
                "globalBenchmark": 80,
                "description": """Performanca Financiare: Suksesi financiar i grupit, rritja e
të ardhurave dhe fitimeve.""",
                "commentary": """Grupi BALFIN ka shënuar një rritje të qëndrueshme dhe është një nga
kontribuesit më të mëdhenj në ekonominë shqiptare. Performancë e lartë financiare.""",
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": 75,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": """Përgjegjësia Sociale e Korporatës (CSR): Angazhimi në kauza sociale,
mjedisore dhe komunitare.""",
                "commentary": """Ka rritur angazhimin në CSR vitet e fundit përmes fondacioneve, por
kritikohet se disa projekte kanë ndikim negativ mjedisor.""",
            },
            {
                "dimension": "Narrative & Communication",
                "score": 85,
                "peerAverage": 80,
                "globalBenchmark": 83,
                "description": """Reputacioni dhe Ndikimi Publik: Perceptimi publik dhe ndikimi në
politikëbërje dhe shoqëri.""",
                "commentary": """Një nga figurat më me ndikim në ekonominë shqiptare. Imazhi i tij është
ai i një biznesmeni të suksesshëm, por shpesh përflitet për lidhje të ngushta me
pushtetin.""",
            },
            {
                "dimension": "Accountability & Transparency",
                "score": 65,
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": """Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë
dhe respektimi i standardeve etike.""",
                "commentary": """Mungesa e transparencës për marrëdhëniet me qeverinë dhe përfitimet
nga partneritetet publike-private është një pikë e vazhdueshme kritike.""",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": 80,
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": """Stabiliteti Organizativ: Aftësia për të mbajtur një strukturë të
qëndrueshme dhe për të menaxhuar rritjen.""",
                "commentary": """Ka ndërtuar një perandori biznesi të qëndrueshme, duke treguar aftësi
të larta në menaxhimin e rritjes dhe diversifikimit.""",
            },
        ],
    },
    {
        "id": "vip33",
        "name": "Dr Alban Gj. THIKA",
        "imageUrl": "https://novaric.co/wp-content/uploads/2025/10/NOVARIC_Team-Member_A-THIKA_Small.png",
        "category": "Politikë & Biznes",
        "shortBio": """A Doctorate-level political and business strategist with over 20 years of
international experience spanning public administration, enterprise development,
campaign consultancy, and academic research across Albania, Malta, and Australia.""",
        "detailedBio": """### Professional Summary
A Doctorate-level political and business strategist with over 20 years of international
experience spanning public administration, enterprise development, campaign consultancy,
and academic research across Albania, Malta, and Australia. Combines rigorous academic
training in International Relations and Business Administration with an entrepreneurial
mindset to drive reform, innovation, and growth. Adept at navigating complex multicultural
and regulatory environments, with direct experience in EU project management and high-level
political advisory roles. Proven resilience and a consistent drive to initiate and lead
new ventures in challenging markets.

### Core Competencies
- **Political Strategy & Public Affairs:** Political Consulting, Campaign Strategy, Public
  Policy Analysis, International Relations, Public Administration, EU Project Management.
- **Business & Management:** Strategic Planning, Business Development & Start-ups,
  International Trade & Sourcing, Market Analysis, Operations Management, Change Management.
- **Communication & Leadership:** Cross-Cultural Communication, Public Speaking, Coalition
  Building, Negotiation & Conflict Resolution, Resilience & Adaptability.

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

