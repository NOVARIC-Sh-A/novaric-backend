# utils/paragon_engine.py

from __future__ import annotations

from typing import Dict, Any, List


# ============================================================
# PARAGON CONFIGURATION
# ============================================================

# Weights determine how important each metric is to the Pillar Score.
WEIGHTS: Dict[str, Dict[str, float]] = {
    "integrity": {"scandals": 0.60, "wealth": 0.40},
    "governance": {"projects": 0.50, "attendance": 0.30, "intl": 0.20},
    "influence": {"party": 0.60, "media": 0.40},
    "professionalism": {"legislative": 0.70, "independence": 0.30},
}

# Ranges determine min/max values for normalization.
# Example: 10 scandals is the "max bad" (score → 0).
RANGES: Dict[str, tuple[int, int]] = {
    "scandals": (0, 10),            # inverse
    "wealth": (0, 5),               # inverse
    "projects": (0, 50),
    "attendance": (0, 100),
    "intl": (0, 30),
    "party": (0, 10),
    "media": (0, 2000),
    "legislative": (0, 20),
    "independence": (0, 10),
}


# ============================================================
# PARAGON ENGINE
# ============================================================

class ParagonEngine:
    """
    The computational core of NOVARIC® PARAGON.

    Input:
      raw_data = {
        "metrics": { ... },
        "kapsh_profile": "Optional string"
      }

    Output:
      List of 7 PARAGON dimensions (frontend contract).
    """

    def __init__(self, raw_data: Dict[str, Any]):
        self.metrics: Dict[str, Any] = raw_data.get("metrics", {}) or {}
        self.kapsh_profile: str = raw_data.get("kapsh_profile", "Unknown")

    # --------------------------------------------------------
    # Normalization
    # --------------------------------------------------------

    def _norm(self, key: str, value: float | int, inverse: bool = False) -> float:
        """
        Normalize a raw metric to a 0–100 scale.

        inverse=True means lower raw value is better.
        """
        min_v, max_v = RANGES.get(key, (0, 100))

        if max_v <= min_v:
            return 0.0

        try:
            v = float(value)
        except Exception:
            v = 0.0

        clamped = max(min_v, min(v, max_v))
        score = ((clamped - min_v) / (max_v - min_v)) * 100.0

        return 100.0 - score if inverse else score

    # --------------------------------------------------------
    # Core computation
    # --------------------------------------------------------

    def calculate(self) -> List[Dict[str, Any]]:
        """
        Executes the PARAGON algorithm.
        Returns a list of 7 dimension objects (stable contract).
        """

        # 1. ACCOUNTABILITY & TRANSPARENCY (Integrity)
        s_scandals = self._norm(
            "scandals",
            self.metrics.get("scandals_flagged", 0),
            inverse=True,
        )
        s_wealth = self._norm(
            "wealth",
            self.metrics.get("wealth_declaration_issues", 0),
            inverse=True,
        )
        score_integrity = (
            s_scandals * WEIGHTS["integrity"]["scandals"]
            + s_wealth * WEIGHTS["integrity"]["wealth"]
        )

        # 2. GOVERNANCE & INSTITUTIONAL STRENGTH
        s_projects = self._norm(
            "projects",
            self.metrics.get("public_projects_completed", 0),
        )
        s_attendance = self._norm(
            "attendance",
            self.metrics.get("parliamentary_attendance", 0),
        )
        s_intl = self._norm(
            "intl",
            self.metrics.get("international_meetings", 0),
        )
        score_governance = (
            s_projects * WEIGHTS["governance"]["projects"]
            + s_attendance * WEIGHTS["governance"]["attendance"]
            + s_intl * WEIGHTS["governance"]["intl"]
        )

        # 3. ASSERTIVENESS & INFLUENCE
        s_party = self._norm(
            "party",
            self.metrics.get("party_control_index", 0),
        )
        s_media = self._norm(
            "media",
            self.metrics.get("media_mentions_monthly", 0),
        )
        score_influence = (
            s_party * WEIGHTS["influence"]["party"]
            + s_media * WEIGHTS["influence"]["media"]
        )

        # 4. POLICY ENGAGEMENT & EXPERTISE
        s_legislative = self._norm(
            "legislative",
            self.metrics.get("legislative_initiatives", 0),
        )
        s_independence = self._norm(
            "independence",
            self.metrics.get("independence_index", 0),
        )
        score_professionalism = (
            s_legislative * WEIGHTS["professionalism"]["legislative"]
            + s_independence * WEIGHTS["professionalism"]["independence"]
        )

        # ----------------------------------------------------
        # Diagnosis (PIP Matrix)
        # ----------------------------------------------------

        diagnosis = self._get_clinical_diagnosis(
            integrity=score_integrity,
            influence=score_influence,
        )

        # ----------------------------------------------------
        # Return structure (frontend contract)
        # ----------------------------------------------------

        return [
            {
                "dimension": "Accountability & Transparency",
                "score": int(score_integrity),
                "peerAverage": 62,
                "globalBenchmark": 70,
                "description": "Llogaridhënia ndaj publikut dhe transparenca.",
                "commentary": (
                    f"Diagnoza Klinike (PIP): {diagnosis}. "
                    "Bazuar në të dhënat e integritetit."
                ),
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": int(score_governance),
                "peerAverage": 67,
                "globalBenchmark": 73,
                "description": "Kontributi në forcimin e institucioneve.",
                "commentary": (
                    f"Efikasitet i bazuar në "
                    f"{self.metrics.get('public_projects_completed', 0)} projekte "
                    "dhe pjesëmarrje institucionale."
                ),
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": int(score_influence),
                "peerAverage": 65,
                "globalBenchmark": 68,
                "description": "Aftësia për të ndikuar në axhendën politike.",
                "commentary": (
                    "Ndikim i llogaritur nga kontrolli partiak dhe "
                    "prezenca mediatike."
                ),
            },
            {
                "dimension": "Policy Engagement & Expertise",
                "score": int(score_professionalism),
                "peerAverage": 68,
                "globalBenchmark": 72,
                "description": "Pjesëmarrja në hartimin e legjislacionit.",
                "commentary": (
                    f"Vlerësim bazuar në "
                    f"{self.metrics.get('legislative_initiatives', 0)} nisma ligjore "
                    "dhe pavarësinë në votim."
                ),
            },
            {
                "dimension": "Representation & Responsiveness",
                "score": int((score_influence + score_professionalism) / 2),
                "peerAverage": 70,
                "globalBenchmark": 75,
                "description": "Lidhja me zonën zgjedhore.",
                "commentary": "Indikator i derivuar nga aktiviteti publik dhe legjislativ.",
            },
            {
                "dimension": "Organizational & Party Cohesion",
                "score": int(self.metrics.get("party_control_index", 5) * 10),
                "peerAverage": 75,
                "globalBenchmark": 78,
                "description": "Roli në ruajtjen e unitetit partiak.",
                "commentary": "Reflekton autoritetin e brendshëm politik.",
            },
            {
                "dimension": "Narrative & Communication",
                "score": int(
                    self._norm(
                        "media",
                        self.metrics.get("media_mentions_monthly", 0),
                    )
                ),
                "peerAverage": 71,
                "globalBenchmark": 74,
                "description": "Efektiviteti i komunikimit publik.",
                "commentary": "Matje sasiore e dominimit të diskursit publik.",
            },
        ]

    # --------------------------------------------------------
    # Diagnosis logic (PIP Matrix)
    # --------------------------------------------------------

    def _get_clinical_diagnosis(self, *, integrity: float, influence: float) -> str:
        """
        Integrity vs Power diagnostic matrix.
        """
        if integrity < 50 and influence > 80:
            return "RREZIK I LARTË (Kapje Shteti)"
        if integrity < 50:
            return "Vulnerabël ndaj Korrupsionit"
        if integrity > 75 and influence > 75:
            return "Lider Model (Balancë e Lartë)"
        if integrity > 75:
            return "Integritet i Qëndrueshëm"
        return "Profil Standard (Nën Monitorim)"
