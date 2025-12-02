"""
PARAGON® HYBRID ENGINE (Methodology Master)
-------------------------------------------
1. Weights & Dimensions
2. Hybrid Scoring Logic (Flags -> Scores)
3. PIP Matrix Logic (Quadrants)
"""

# --- CONFIGURATION ---
PARAGON_WEIGHTS = {
    "political_engagement": 0.20,
    "integrity": 0.30,            # High Priority
    "governance": 0.20,
    "communication": 0.15,
    "influence": 0.15
}

# --- PART A: SCORING ALGORITHMS ---
def calculate_hybrid_score(ai_data_list):
    """
    Takes AI flags and converts them into 0-100 scores for the 5 Dimensions.
    """
    if not ai_data_list:
        return None

    # Buckets for accumulating scores
    raw_scores = {
        "political_engagement": [], 
        "integrity": [], 
        "governance": [], 
        "communication": [], 
        "influence": []
    }

    for data in ai_data_list:
        if not data.is_political_event:
            continue

        # 1. INTEGRITY (Dimension A)
        if data.has_corruption_allegation:
            raw_scores["integrity"].append(20.0) # Penalize heavily
        else:
            score = ((data.sentiment_score + 1) / 2) * 100
            raw_scores["integrity"].append(score)

        # 2. POLITICAL ENGAGEMENT (Dimension P)
        if data.has_international_endorsement:
            raw_scores["political_engagement"].append(95.0)
        elif data.has_legislative_action:
            raw_scores["political_engagement"].append(80.0)
        else:
            raw_scores["political_engagement"].append(50.0)

        # 3. GOVERNANCE (Dimension G)
        base_gov = ((data.sentiment_score + 1) / 2) * 100
        if data.has_public_outcry:
            base_gov -= 20
        raw_scores["governance"].append(max(0, base_gov))

        # 4. COMMUNICATION & INFLUENCE
        norm_score = ((data.sentiment_score + 1) / 2) * 100
        raw_scores["communication"].append(norm_score)
        raw_scores["influence"].append(norm_score)

    # Aggregate Averages
    final_metrics = {}
    for key, val_list in raw_scores.items():
        if val_list:
            final_metrics[key] = int(sum(val_list) / len(val_list))
        else:
            final_metrics[key] = 50 # Default Neutral

    # Calculate Weighted Overall Score
    overall = (
        final_metrics["political_engagement"] * PARAGON_WEIGHTS["political_engagement"] +
        final_metrics["integrity"] * PARAGON_WEIGHTS["integrity"] +
        final_metrics["governance"] * PARAGON_WEIGHTS["governance"] +
        final_metrics["communication"] * PARAGON_WEIGHTS["communication"] +
        final_metrics["influence"] * PARAGON_WEIGHTS["influence"]
    )

    return {
        "overall": int(overall),
        "breakdown": final_metrics
    }

# --- PART B: DIAGNOSTIC ALGORITHMS (PIP MATRIX) ---
# THIS IS THE FUNCTION THAT WAS MISSING
def calculate_pip_status(structural_vulnerability, behavioral_risk):
    """
    Determines the PIP Matrix Quadrant.
    """
    
    is_high_vuln = structural_vulnerability > 50
    is_high_risk = behavioral_risk > 50

    if not is_high_vuln and not is_high_risk:
        return {"quadrant": 1, "title": "Integritet i Qëndrueshëm", "color": "green"}
    
    elif is_high_vuln and not is_high_risk:
        return {"quadrant": 2, "title": "Rrezik i Fjetur", "color": "yellow"}

    elif not is_high_vuln and is_high_risk:
        return {"quadrant": 3, "title": "Prirje Shqetësuese", "color": "orange"}

    elif is_high_vuln and is_high_risk:
        return {"quadrant": 4, "title": "ALERT I LARTË INTEGRITETI", "color": "red"}