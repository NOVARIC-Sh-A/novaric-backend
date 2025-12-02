import math

# --- CONFIGURATION: The "Rules of the Game" for Albanian Politics ---
WEIGHTS = {
    "integrity": {"scandals": 0.60, "wealth": 0.40},
    "governance": {"projects": 0.50, "attendance": 0.30, "intl": 0.20},
    "influence": {"party": 0.60, "media": 0.40},
    "professionalism": {"legislative": 0.70, "independence": 0.30}
}

RANGES = {
    "scandals": (0, 10),       "wealth": (0, 5),          # Inverse (Lower is better)
    "projects": (0, 50),       "attendance": (0, 100),    # Direct
    "intl": (0, 30),           "party": (0, 10),
    "media": (0, 2000),        "legislative": (0, 20),
    "independence": (0, 10)
}

class ParagonEngine:
    def __init__(self, raw_data):
        self.metrics = raw_data.get('metrics', {})
        self.kapsh_profile = raw_data.get('kapsh_profile', 'Unknown')

    def _norm(self, key, value, inverse=False):
        """Normalizes raw data to 0-100 scale."""
        min_v, max_v = RANGES.get(key, (0, 100))
        clamped = max(min_v, min(value, max_v))
        score = ((clamped - min_v) / (max_v - min_v)) * 100
        return 100 - score if inverse else score

    def calculate(self):
        # 1. PILLAR: ACCOUNTABILITY (Integrity)
        s_scandals = self._norm("scandals", self.metrics.get("scandals_flagged", 0), inverse=True)
        s_wealth = self._norm("wealth", self.metrics.get("wealth_declaration_issues", 0), inverse=True)
        score_integrity = (s_scandals * WEIGHTS["integrity"]["scandals"]) + \
                          (s_wealth * WEIGHTS["integrity"]["wealth"])

        # 2. PILLAR: GOVERNANCE (Institutional Strength)
        s_proj = self._norm("projects", self.metrics.get("public_projects_completed", 0))
        s_att = self._norm("attendance", self.metrics.get("parliamentary_attendance", 0))
        s_intl = self._norm("intl", self.metrics.get("international_meetings", 0))
        score_governance = (s_proj * WEIGHTS["governance"]["projects"]) + \
                           (s_att * WEIGHTS["governance"]["attendance"]) + \
                           (s_intl * WEIGHTS["governance"]["intl"])

        # 3. PILLAR: INFLUENCE (Assertiveness)
        s_party = self._norm("party", self.metrics.get("party_control_index", 0))
        s_media = self._norm("media", self.metrics.get("media_mentions_monthly", 0))
        score_influence = (s_party * WEIGHTS["influence"]["party"]) + \
                          (s_media * WEIGHTS["influence"]["media"])

        # 4. PILLAR: POLICY (Engagement)
        s_leg = self._norm("legislative", self.metrics.get("legislative_initiatives", 0))
        s_ind = self._norm("independence", self.metrics.get("independence_index", 0))
        score_prof = (s_leg * WEIGHTS["professionalism"]["legislative"]) + \
                     (s_ind * WEIGHTS["professionalism"]["independence"])

        # GENERATE DIAGNOSIS TEXT
        diagnosis = self._get_clinical_diagnosis(score_integrity, score_influence)

        return [
            {
                "dimension": "Accountability & Transparency",
                "score": int(score_integrity),
                "peerAverage": 62, "globalBenchmark": 70,
                "description": "Llogaridhënia dhe transparenca.",
                "commentary": f"Diagnoza PIP: {diagnosis}"
            },
            {
                "dimension": "Governance & Institutional Strength",
                "score": int(score_governance),
                "peerAverage": 67, "globalBenchmark": 73,
                "description": "Forca institucionale dhe projektet.",
                "commentary": f"Efikasiteti i qeverisjes bazuar në {self.metrics.get('public_projects_completed')} projekte."
            },
            {
                "dimension": "Assertiveness & Influence",
                "score": int(score_influence),
                "peerAverage": 65, "globalBenchmark": 68,
                "description": "Ndikimi politik dhe mediatik.",
                "commentary": f"Indeksi i kontrollit partiak: {self.metrics.get('party_control_index')}/10."
            },
            {
                "dimension": "Policy Engagement & Expertise",
                "score": int(score_prof),
                "peerAverage": 68, "globalBenchmark": 72,
                "description": "Angazhimi legjislativ.",
                "commentary": f"Nisma ligjore të ndërmarra: {self.metrics.get('legislative_initiatives')}."
            }
        ]

    def _get_clinical_diagnosis(self, integrity, influence):
        if integrity < 50 and influence > 80:
            return "RREZIK I LARTË (Kapje Shteti)"
        elif integrity < 50:
            return "Vulnerabël ndaj Korrupsionit"
        elif integrity > 75:
            return "Integritet i Qëndrueshëm"
        else:
            return "Profil Standard (Nën Monitorim)"
