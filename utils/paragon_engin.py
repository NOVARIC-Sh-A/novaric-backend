# utils/paragon_engine.py
import math

# --- 1. CONFIGURATION (The "Weights" & "Ranges") ---
# Adapted for Albanian Context (AGIB/KAPSH)

METRIC_RANGES = {
    # AGIB (Structural/Integrity)
    "scandals_flagged": {"min": 0, "max": 10}, # Inverse (0 is best)
    "wealth_declaration_issues": {"min": 0, "max": 5}, # Inverse
    "years_in_power": {"min": 0, "max": 20}, # Vulnerability factor
    
    # Professional / Legislative
    "parliamentary_attendance": {"min": 0, "max": 100}, # %
    "legislative_initiatives": {"min": 0, "max": 20},
    "independence_index": {"min": 0, "max": 10}, # Voted against party line
    
    # Influence / KAPSH
    "party_control_index": {"min": 0, "max": 10}, # 10 = Absolute Leader
    "media_mentions_monthly": {"min": 0, "max": 2000},
    "social_sentiment": {"min": -1.0, "max": 1.0},
    
    # Governance
    "public_projects_completed": {"min": 0, "max": 50},
    "international_meetings": {"min": 0, "max": 30}
}

WEIGHTS = {
    "integrity": {
        "scandals_flagged": 0.60,       # High weight due to 'State Capture' risk
        "wealth_declaration_issues": 0.40
    },
    "governance": {
        "public_projects_completed": 0.50,
        "parliamentary_attendance": 0.30,
        "international_meetings": 0.20
    },
    "influence": {
        "party_control_index": 0.60,    # In Albania, party control is power
        "media_mentions_monthly": 0.40
    },
    "professionalism": {
        "legislative_initiatives": 0.70,
        "independence_index": 0.30
    }
}

# --- 2. HELPER FUNCTIONS ---

def normalize(value, min_v, max_v, inverse=False):
    """Normalizes a raw number to a 0-100 score."""
    if max_v == min_v: return 0
    
    # Clamp
    value = max(min_v, min(value, max_v))
    
    if inverse:
        # For corruption: 0 scandals = 100 score
        return ((max_v - value) / (max_v - min_v)) * 100
    else:
        # For projects: 50 projects = 100 score
        return ((value - min_v) / (max_v - min_v)) * 100

# --- 3. THE CORE ENGINE ---

class ParagonEngine:
    def __init__(self, raw_metrics):
        self.raw = raw_metrics

    def _get_metric_score(self, key, inverse=False):
        val = self.raw.get(key, 0)
        cfg = METRIC_RANGES.get(key, {"min": 0, "max": 100})
        return normalize(val, cfg['min'], cfg['max'], inverse)

    def compute_scores(self):
        # 1. Calculate Dimension Scores
        
        # INTEGRITY (PIP)
        m_scandals = self._get_metric_score("scandals_flagged", inverse=True)
        m_wealth = self._get_metric_score("wealth_declaration_issues", inverse=True)
        
        score_integrity = (m_scandals * WEIGHTS['integrity']['scandals_flagged']) + \
                          (m_wealth * WEIGHTS['integrity']['wealth_declaration_issues'])

        # GOVERNANCE (Institutional Strength)
        m_projects = self._get_metric_score("public_projects_completed")
        m_attend = self._get_metric_score("parliamentary_attendance") # Assuming input is already % or 0-100
        m_intl = self._get_metric_score("international_meetings")
        
        score_governance = (m_projects * WEIGHTS['governance']['public_projects_completed']) + \
                           (m_attend * WEIGHTS['governance']['parliamentary_attendance']) + \
                           (m_intl * WEIGHTS['governance']['international_meetings'])

        # INFLUENCE (Assertiveness)
        m_party = self._get_metric_score("party_control_index")
        m_media = self._get_metric_score("media_mentions_monthly")
        
        score_influence = (m_party * WEIGHTS['influence']['party_control_index']) + \
                          (m_media * WEIGHTS['influence']['media_mentions_monthly'])

        # PROFESSIONALISM (Policy Engagement)
        m_legis = self._get_metric_score("legislative_initiatives")
        m_indep = self._get_metric_score("independence_index")
        
        score_prof = (m_legis * WEIGHTS['professionalism']['legislative_initiatives']) + \
                     (m_indep * WEIGHTS['professionalism']['independence_index'])

        # 2. Compute Overall PARAGON Score
        # Weights: Integrity 35% (Critical), Governance 25%, Influence 20%, Prof 20%
        overall = (score_integrity * 0.35) + \
                  (score_governance * 0.25) + \
                  (score_influence * 0.20) + \
                  (score_prof * 0.20)

        # 3. Generate Clinical Diagnosis (Text)
        diagnosis = self._generate_diagnosis(score_integrity, score_influence)

        return {
            "overall": int(overall),
            "dimensions": {
                "Accountability & Transparency": int(score_integrity),
                "Governance & Institutional Strength": int(score_governance),
                "Assertiveness & Influence": int(score_influence),
                "Policy Engagement & Expertise": int(score_prof)
            },
            "diagnosis": diagnosis
        }

    def _generate_diagnosis(self, integrity, influence):
        """Generates the clinical summary text based on the 2x2 Matrix logic."""
        if integrity < 50 and influence > 70:
            return "ALERT I LARTË: Profil me ndikim të lartë por rrezik të theksuar integriteti (Kuadranti 4 - Kapje Shteti)."
        elif integrity < 50:
            return "VULNERABËL: Tregues të ulët transparence dhe llogaridhënie."
        elif integrity > 80 and influence > 80:
            return "LIDER MODEL: Balancë e shkëlqyer midis fuqisë politike dhe integritetit etik."
        else:
            return "STABËL: Profil brenda normave standarde të performancës."

# --- TEST IT ---
if __name__ == "__main__":
    # Mock Data for Edi Rama
    sample_metrics = {
        "scandals_flagged": 4,          # High scandals
        "wealth_declaration_issues": 1,
        "public_projects_completed": 45, # High governance
        "parliamentary_attendance": 45,  # Low attendance
        "party_control_index": 9.5,      # Absolute control
        "media_mentions_monthly": 1200,
        "legislative_initiatives": 12
    }
    
    engine = ParagonEngine(sample_metrics)
    result = engine.compute_scores()
    print(result)
