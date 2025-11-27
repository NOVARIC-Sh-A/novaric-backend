from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib

from mock_profiles import PROFILES

# ============================================================
# FastAPI APP SETUP
# ============================================================

app = FastAPI(
    title="NOVARIC Backend",
    description="Dynamic scoring API for NOVARIC® AI-Powered News",
    version="1.0.0",
)

# CORS – keep open for now; later restrict to your Cloud Run frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MODELS (mirror your TypeScript structure + AI metadata)
# ============================================================


class AiMeta(BaseModel):
    trend: float          # change vs previous period (e.g. +2.5)
    confidence: float     # 0–1 confidence in the score
    volatility: float     # 0–1 how unstable the score is
    summary: str          # short textual explanation
    sources: List[str]    # placeholder URLs – later: real scraped sources


class DimensionScore(BaseModel):
    dimension: str
    score: int
    peerAverage: int
    globalBenchmark: int
    description: str
    commentary: str
    ai: AiMeta


class ProfileBase(BaseModel):
    id: str
    name: str
    category: str
    type: str
    imageUrl: Optional[str] = None
    shortBio: Optional[str] = None
    detailedBio: Optional[str] = None
    zodiacSign: Optional[str] = None


class ProfileAnalysis(BaseModel):
    id: str
    name: str
    category: str
    type: str
    imageUrl: Optional[str] = None
    shortBio: Optional[str] = None
    detailedBio: Optional[str] = None
    zodiacSign: Optional[str] = None
    paragonAnalysis: List[DimensionScore]
    maragonAnalysis: List[DimensionScore]


# ============================================================
# HELPER FUNCTIONS – deterministic "random" numbers
# These give stable scores per (name, dimension)
# Later you will replace this with real scraping + models.
# ============================================================


def _normalized_hash(*parts: str) -> float:
    """
    Turn a list of strings into a deterministic float between 0 and 1.
    This keeps scores stable for the same profile/dimension across requests.
    """
    text = "::".join(parts)
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    # First 8 hex chars -> integer -> 0..1
    n = int(h[:8], 16)
    return n / 0xFFFFFFFF


def _scaled_int(min_val: int, max_val: int, *parts: str) -> int:
    x = _normalized_hash(*parts)
    return int(round(min_val + x * (max_val - min_val)))


def _scaled_float(min_val: float, max_val: float, *parts: str) -> float:
    x = _normalized_hash(*parts)
    return min_val + x * (max_val - min_val)


# ============================================================
# DIMENSION DEFINITIONS (labels + descriptions)
# ============================================================

PARAGON_DIMENSIONS = [
    {
        "key": "policy_engagement",
        "label": "Policy Engagement & Expertise",
        "description": (
            "Pjesëmarrja në hartimin, debatin dhe amendimin e legjislacionit; "
            "puna në komisione dhe ekspertiza në fusha specifike."
        ),
        "peer_avg": 68,
        "benchmark": 72,
    },
    {
        "key": "accountability_transparency",
        "label": "Accountability & Transparency",
        "description": (
            "Llogaridhënia ndaj publikut, transparenca në deklarimin e pasurisë "
            "dhe respektimi i standardeve etike."
        ),
        "peer_avg": 62,
        "benchmark": 70,
    },
    {
        "key": "representation_responsiveness",
        "label": "Representation & Responsiveness",
        "description": (
            "Cilësia e lidhjes me zonën zgjedhore dhe përgjigja ndaj nevojave të komunitetit."
        ),
        "peer_avg": 70,
        "benchmark": 75,
    },
    {
        "key": "assertiveness_influence",
        "label": "Assertiveness & Influence",
        "description": "Aftësia për të ndikuar në axhendën politike brenda dhe jashtë partisë.",
        "peer_avg": 65,
        "benchmark": 68,
    },
    {
        "key": "governance_institutions",
        "label": "Governance & Institutional Strength",
        "description": "Kontributi në forcimin e institucioneve demokratike dhe sundimit të ligjit.",
        "peer_avg": 67,
        "benchmark": 73,
    },
    {
        "key": "organization_cohesion",
        "label": "Organizational & Party Cohesion",
        "description": "Roli në ruajtjen e unitetit dhe disiplinës partiake/organizatës.",
        "peer_avg": 75,
        "benchmark": 78,
    },
    {
        "key": "narrative_communication",
        "label": "Narrative & Communication",
        "description": "Efektiviteti dhe qartësia e komunikimit publik.",
        "peer_avg": 71,
        "benchmark": 74,
    },
]

MARAGON_DIMENSIONS = [
    {
        "key": "ethical_compliance",
        "label": "Pajtueshmëria Etike",
        "description": (
            "Pajtueshmëria me Kodin e Standardeve dhe praktikat bazë të etikës mediatike."
        ),
        "peer_avg": 75,
        "benchmark": 92,
    },
    {
        "key": "crisis_professionalism",
        "label": "Profesionalizmi në Kriza",
        "description": (
            "Aftësia për të ruajtur standardet profesionale gjatë ngjarjeve kritike dhe debateve."
        ),
        "peer_avg": 78,
        "benchmark": 85,
    },
    {
        "key": "factual_accuracy",
        "label": "Saktësia Faktike & Verifikimi",
        "description": (
            "Rigoroziteti në verifikimin e informacionit dhe dallimi i qartë midis faktit dhe opinionit."
        ),
        "peer_avg": 72,
        "benchmark": 88,
    },
    {
        "key": "impartiality_balance",
        "label": "Paanshmëria, Balanca & Anshmëria",
        "description": (
            "Balancimi i perspektivave, shmangia e anshmërisë dhe menaxhimi i kohës së fjalës."
        ),
        "peer_avg": 65,
        "benchmark": 90,
    },
    {
        "key": "depth_of_analysis",
        "label": "Thellësia e Analizës/Pyetjeve",
        "description": (
            "Nivel i pyetjeve analitike, ndjekja e përgjigjeve dhe njohuri e thellë mbi temën."
        ),
        "peer_avg": 75,
        "benchmark": 88,
    },
    {
        "key": "clarity_coherence",
        "label": "Qartësia & Koherenca",
        "description": (
            "Qartësia e të folurit dhe aftësia për të menaxhuar rrjedhën logjike të debatit."
        ),
        "peer_avg": 80,
        "benchmark": 90,
    },
    {
        "key": "critical_thinking",
        "label": "Promovimi i të Menduarit Kritik",
        "description": (
            "Sa shumë inkurajon audiencën të mendojë kritikisht dhe të konsiderojë perspektiva të shumëfishta."
        ),
        "peer_avg": 70,
        "benchmark": 85,
    },
]


def generate_dimension_scores(
    profile: dict, dimensions: List[dict], min_score: int = 40, max_score: int = 95
) -> List[DimensionScore]:
    """Generate dynamic scores + AI metadata for each dimension."""
    results: List[DimensionScore] = []
    name = profile["name"]
    pid = profile["id"]

    for dim in dimensions:
        key = dim["key"]
        label = dim["label"]
        desc = dim["description"]
        peer_avg = dim["peer_avg"]
        benchmark = dim["benchmark"]

        score = _scaled_int(min_score, max_score, pid, key, name)
        trend = _scaled_float(-5.0, 5.0, pid, key, "trend")
        confidence = _scaled_float(0.6, 0.98, pid, key, "confidence")
        volatility = _scaled_float(0.05, 0.35, pid, key, "volatility")

        commentary = (
            f"Vlerësim i përkohshëm për {name} në dimensionin '{label}'. "
            "Këto rezultate do të rafinohen më tej sapo të lidhen burimet e "
            "reja të të dhënave dhe analizat automatike."
        )

        ai_summary = (
            f"{name} paraqet një nivel rreth {score} pikë në '{label}'. "
            f"Tendenca aktuale është {'pozitive' if trend >= 0 else 'negative'}, "
            f"me besueshmëri rreth {confidence:.2f} dhe luhatshmëri {volatility:.2f}."
        )

        ai_meta = AiMeta(
            trend=round(trend, 2),
            confidence=round(confidence, 2),
            volatility=round(volatility, 2),
            summary=ai_summary,
            sources=[
                "https://media.novaric.al",          # placeholder – later: real links
                "https://parlament.al",              # placeholder
            ],
        )

        results.append(
            DimensionScore(
                dimension=label,
                score=score,
                peerAverage=peer_avg,
                globalBenchmark=benchmark,
                description=desc,
                commentary=commentary,
                ai=ai_meta,
            )
        )

    return results


# ============================================================
# UTILS
# ============================================================


def _find_profile(profile_id: str) -> dict:
    for p in PROFILES:
        if p["id"] == profile_id:
            return p
    raise HTTPException(status_code=404, detail="Profile not found")


# ============================================================
# ENDPOINTS
# ============================================================


@app.get("/")
def root():
    """Simple health-check endpoint."""
    return {"message": "NOVARIC Backend is running"}


@app.get("/api/profiles", response_model=List[ProfileBase])
def get_all_profiles():
    """Return all profiles (metadata only, no scores)."""
    return PROFILES


@app.get("/api/profiles/{profile_id}", response_model=ProfileBase)
def get_profile(profile_id: str):
    """Return a single profile (metadata only)."""
    profile = _find_profile(profile_id)
    return profile


@app.get("/api/profiles/{profile_id}/analysis", response_model=ProfileAnalysis)
def get_profile_analysis(profile_id: str):
    """
    Return full analysis for a profile:
    - PARAGON (political-style framework)
    - MARAGON (media-style framework)
    Output uses hybrid structure (Option C).
    """
    profile = _find_profile(profile_id)

    # political, media, business etc all get PARAGON.
    paragon_scores = generate_dimension_scores(profile, PARAGON_DIMENSIONS)

    # MARAGON mainly makes sense for media & showbiz, but we can expose it for all.
    maragon_scores = generate_dimension_scores(profile, MARAGON_DIMENSIONS, 60, 95)

    return ProfileAnalysis(
        id=profile["id"],
        name=profile["name"],
        category=profile["category"],
        type=profile["type"],
        imageUrl=profile.get("imageUrl"),
        shortBio=profile.get("shortBio"),
        detailedBio=profile.get("detailedBio"),
        zodiacSign=profile.get("zodiacSign"),
        paragonAnalysis=paragon_scores,
        maragonAnalysis=maragon_scores,
    )
