# mock_profiles.py
"""
Single source of truth for profile fixtures (PROFILES) with optional PARAGON hydration.

Design goals:
- Keep seeding stable: set MOCK_PROFILES_NO_HYDRATE=1 to guarantee NO ETL calls.
- Avoid "mis-ordered" failures: datasets are imported from a dedicated module
  (mock_profiles_data.py) or defined as safe empty lists with a clear warning.
- Option A hydration: engine wins when metric bundles exist.

Required (recommended):
- Create a sibling file: mock_profiles_data.py
  and define:
    mock_political_profiles_data: List[VipProfile]
    mock_media_profiles_data: List[VipProfile]
    mock_business_profiles_data: List[VipProfile]
  (copy/paste your existing large dataset blocks there unchanged)
"""

from __future__ import annotations

import logging
import os
import random
import re
from typing import Any, Dict, List, Optional, Union

# =============================================================================
# EXPORT / DEV FLAGS
# =============================================================================
MOCK_PROFILES_QUIET = os.getenv("MOCK_PROFILES_QUIET") == "1"
MOCK_PROFILES_NO_HYDRATE = os.getenv("MOCK_PROFILES_NO_HYDRATE") == "1"

# Type aliases
VipProfile = Dict[str, Any]
ParagonEntry = Dict[str, Any]

# =============================================================================
# ARCHITECTURE IMPORTS: "Bridge" to the PARAGON engine (OPTION A = engine wins)
# =============================================================================
ENGINE_AVAILABLE = False
RAW_EVIDENCE: Dict[Union[str, int], Any] = {}

if not MOCK_PROFILES_NO_HYDRATE:
    try:
        # NEW engine paths (as per your project)
        from etl.metric_loader import load_metrics_for  # type: ignore
        from etl.scoring_engine import score_metrics  # type: ignore

        ENGINE_AVAILABLE = True
        if not MOCK_PROFILES_QUIET:
            print("PARAGON System: New loader + scoring engine active.")
    except ImportError:
        ENGINE_AVAILABLE = False
        if not MOCK_PROFILES_QUIET:
            print("PARAGON System: Engine files not found. Running in Offline Mode.")
    except Exception as e:
        ENGINE_AVAILABLE = False
        if not MOCK_PROFILES_QUIET:
            print(f"PARAGON System: Error loading metrics: {e}")

# =============================================================================
# INTERNAL HELPERS (ID NORMALIZATION FOR PARAGON ETL)
# =============================================================================


def _id_to_int(pid: Union[str, int, None]) -> Optional[int]:
    """
    Convert ids like 'vip1', 'vip29', 'mp49' -> int(1, 29, 49).
    If already int, return it. If no trailing digits exist, return None.
    """
    if pid is None:
        return None
    if isinstance(pid, int):
        return pid
    s = str(pid).strip()
    m = re.search(r"(\d+)$", s)
    return int(m.group(1)) if m else None


# =============================================================================
# HELPER GENERATORS
# =============================================================================


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


def generate_paragon_analysis(name: str) -> List[ParagonEntry]:
    """Generates generic Political analysis (fallback only)."""
    return [
        {
            "dimension": "Policy Engagement & Expertise",
            "score": generate_random_score(),
            "peerAverage": 68,
            "globalBenchmark": 72,
            "description": (
                "Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit; puna në komisione."
            ),
            "commentary": (
                f"Të dhënat për performancën legjislative të {name} do të mblidhen dhe analizohen gjatë mandatit aktual."
            ),
        },
        {
            "dimension": "Accountability & Transparency",
            "score": generate_random_score(),
            "peerAverage": 62,
            "globalBenchmark": 70,
            "description": "Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë.",
            "commentary": (
                f"Transparenca dhe llogaridhënia për {name} do të vlerësohen bazuar në veprimtarinë publike."
            ),
        },
        {
            "dimension": "Representation & Responsiveness",
            "score": generate_random_score(),
            "peerAverage": 70,
            "globalBenchmark": 75,
            "description": (
                "Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave të komunitetit."
            ),
            "commentary": (
                f"Angazhimi i {name} me zonën zgjedhore dhe komunitetin do të monitorohet."
            ),
        },
        {
            "dimension": "Assertiveness & Influence",
            "score": generate_random_score(),
            "peerAverage": 65,
            "globalBenchmark": 68,
            "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
            "commentary": (
                f"Ndikimi politik i {name} do të matet përmes nismave dhe rolit në debatet kyçe."
            ),
        },
        {
            "dimension": "Governance & Institutional Strength",
            "score": generate_random_score(),
            "peerAverage": 67,
            "globalBenchmark": 73,
            "description": (
                "Kontributi në forcimin e institucioneve demokratike dhe sundimit të ligjit."
            ),
            "commentary": (
                f"Veprimtaria e {name} në lidhje me qeverisjen dhe reformat institucionale do të jetë objekt analize."
            ),
        },
        {
            "dimension": "Organizational & Party Cohesion",
            "score": generate_random_score(),
            "peerAverage": 75,
            "globalBenchmark": 78,
            "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake.",
            "commentary": (
                f"Qëndrimet dhe votimet e {name} do të analizohen në raport me linjën zyrtare të partisë."
            ),
        },
        {
            "dimension": "Narrative & Communication",
            "score": generate_random_score(),
            "peerAverage": 71,
            "globalBenchmark": 74,
            "description": "Efektiveti dhe qartësia e komunikimit publik.",
            "commentary": (
                f"Aftësitë komunikuese dhe diskursi publik i {name} do të vlerësohen në vazhdimësi."
            ),
        },
    ]


def generate_maragon_analysis(name: str) -> List[ParagonEntry]:
    """Generates generic Media analysis (fallback only)."""
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
            "description": (
                "Aftësia për të ruajtur qetësinë dhe standardet profesionale gjatë lajmeve të fundit."
            ),
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
            "description": (
                "Aftësia për të bërë pyetje të thelluara dhe për të ndjekur përgjigjet."
            ),
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Qartësia & Koherenca",
            "score": generate_random_score(80, 95),
            "peerAverage": 80,
            "globalBenchmark": 90,
            "description": (
                "Qartësia e të folurit, artikulimi dhe aftësia për të menaxhuar rrjedhën logjike."
            ),
            "commentary": f"Analiza e detajuar për {name} është në proces e sipër.",
        },
        {
            "dimension": "Promovimi i të Menduarit Kritik",
            "score": generate_random_score(65, 85),
            "peerAverage": 70,
            "globalBenchmark": 85,
            "description": (
                "Inkurajimi i audiencës për të konsideruar perspektiva të shumëfishta."
            ),
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
    """Helper to generate generic MPs (fallback only)."""
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


# =============================================================================
# DATASETS (imported to avoid mis-ordering and keep this file maintainable)
# =============================================================================

# Recommended: put your large dataset blocks in mock_profiles_data.py
# and keep them "unchanged" there.
try:
    from mock_profiles_data import (  # type: ignore
        mock_business_profiles_data,
        mock_media_profiles_data,
        mock_political_profiles_data,
    )
except Exception as e:
    # Safe fallback: the module isn't present or failed to import.
    # We do NOT hard-crash here because you may want to run the app without fixtures.
    mock_political_profiles_data: List[VipProfile] = []
    mock_media_profiles_data: List[VipProfile] = []
    mock_business_profiles_data: List[VipProfile] = []

    if not MOCK_PROFILES_QUIET:
        logging.warning(
            "mock_profiles_data.py not available or failed to import (%s). "
            "PROFILES will be empty until datasets are provided.",
            e,
        )


# =============================================================================
# HYDRATION LOGIC (OPTION A = ENGINE WINS)
# =============================================================================


def hydrate_profiles_with_engine(profiles: List[VipProfile]) -> None:
    """
    Overwrite static paragonAnalysis with engine results when available.

    Behavior:
    - If MOCK_PROFILES_NO_HYDRATE=1 -> skip hydration entirely (seeding safe mode).
    - If engine is available -> attempt hydration using integer ids (vip1 -> 1).
    - Profiles without trailing numeric ids (e.g., 'vip_nn') are skipped.
    """
    if MOCK_PROFILES_NO_HYDRATE:
        if not MOCK_PROFILES_QUIET:
            print(
                "PARAGON Hydration: disabled (MOCK_PROFILES_NO_HYDRATE=1). Using static mock data."
            )
        return

    if not ENGINE_AVAILABLE:
        return

    count_updated = 0

    for profile in profiles:
        raw_pid = profile.get("id")
        pid_int = _id_to_int(raw_pid)

        # If we can't map to an int, we cannot call ETL that expects integer ids
        if pid_int is None:
            continue

        metrics_bundle = None

        # 1) Prefer preloaded RAW_EVIDENCE (support both raw string id and int id keys)
        if raw_pid in RAW_EVIDENCE:
            metrics_bundle = RAW_EVIDENCE[raw_pid]
        elif pid_int in RAW_EVIDENCE:
            metrics_bundle = RAW_EVIDENCE[pid_int]
        else:
            # 2) Load evidence on demand via metric_loader (expects int id)
            try:
                metrics_bundle = load_metrics_for(pid_int)  # type: ignore[name-defined]
            except Exception as e:
                logging.warning(
                    "PARAGON: Error loading metrics for %s -> %s: %s", raw_pid, pid_int, e
                )
                continue

        if not metrics_bundle:
            continue

        # 3) Score metrics
        try:
            new_analysis = score_metrics(metrics_bundle)  # type: ignore[name-defined]
        except Exception as e:
            logging.warning(
                "PARAGON: Error scoring metrics for %s -> %s: %s", raw_pid, pid_int, e
            )
            continue

        if not new_analysis:
            continue

        profile["paragonAnalysis"] = new_analysis
        count_updated += 1

    if count_updated > 0 and not MOCK_PROFILES_QUIET:
        print(f"PARAGON Engine: hydrated {count_updated} profiles.")


# =============================================================================
# FINAL EXPORT (MUST BE LAST)
# =============================================================================

PROFILES: List[VipProfile] = (
    list(mock_political_profiles_data)
    + list(mock_media_profiles_data)
    + list(mock_business_profiles_data)
)

# Option A: hydrate only when explicitly allowed
if not MOCK_PROFILES_NO_HYDRATE and PROFILES:
    hydrate_profiles_with_engine(PROFILES)
