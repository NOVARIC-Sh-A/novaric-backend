"""
PARAGON® UNIFIED METHODOLOGY ENGINE
-----------------------------------
This module implements the mathematical rules defined in the NOVARIC methodology.
It covers:
1. P.A.G. Analysis (Engagement, Accountability, Governance)
2. PIP (Political Integrity Profile) Matrix
3. Weighted Scoring Algorithm
"""

# --- CONFIGURATION: DIMENSION WEIGHTS ---
# Based on the "Contextual Adaptation" section:
# "Peshat... janë kalibruar posaçërisht për të reflektuar realitetet shqiptare."
PARAGON_WEIGHTS = {
    "political_engagement": 0.15, # P - Angazhimi & Ekspertiza
    "integrity": 0.30,            # A - Llogaridhënia & Transparenca (Highest Priority)
    "governance": 0.20,           # G - Qeverisja & Forca Institucionale
    "communication": 0.15,        # Narrativa & Komunikimi
    "influence": 0.20             # Ndikimi & Rrjetëzimi (Network Centrality)
}

def normalize_score(raw_value, min_val, max_val):
    """
    "Të gjitha të dhënat e papërpunuara normalizohen në një shkallë standarde nga 0 në 100."
    """
    if raw_value > max_val: return 100
    if raw_value < min_val: return 0
    return int(((raw_value - min_val) / (max_val - min_val)) * 100)

def calculate_paragon_score(metrics):
    """
    Faza 3: Ponderimi dhe Agregimi i Pikëzimit
    Calculates the final weighted score based on the 5 Dimensions.
    """
    final_score = 0
    
    # 1. Political Engagement (P)
    final_score += metrics['political_engagement'] * PARAGON_WEIGHTS['political_engagement']
    
    # 2. Integrity (A) - The "Veto" Factor
    # If integrity is dangerously low (<30), it drags the whole score down disproportionately
    final_score += metrics['integrity'] * PARAGON_WEIGHTS['integrity']
    
    # 3. Governance (G)
    final_score += metrics['governance'] * PARAGON_WEIGHTS['governance']
    
    # 4. Communication
    final_score += metrics['communication'] * PARAGON_WEIGHTS['communication']
    
    # 5. Influence (Network)
    final_score += metrics['influence'] * PARAGON_WEIGHTS['influence']

    return int(final_score)

def calculate_pip_status(structural_vulnerability, behavioral_risk):
    """
    PROFILI I INTEGRITETIT POLITIK (PIP) - MATRIX 2x2
    
    Input:
    - structural_vulnerability (0-100): From Component A (AGIB)
    - behavioral_risk (0-100): From Component B (CRI)
    
    Output: Quadrant Name & Description
    """
    
    # Logic defining the 4 Quadrants
    is_high_vuln = structural_vulnerability > 50
    is_high_risk = behavioral_risk > 50

    if not is_high_vuln and not is_high_risk:
        return {
            "quadrant": 1,
            "title": "Integritet i Qëndrueshëm",
            "status": "Rrezik i Ulët",
            "color": "green"
        }
    
    elif is_high_vuln and not is_high_risk:
        return {
            "quadrant": 2,
            "title": "Rrezik i Fjetur",
            "status": "Kërkon Monitorim",
            "color": "yellow"
        }

    elif not is_high_vuln and is_high_risk:
        return {
            "quadrant": 3,
            "title": "Prirje Shqetësuese",
            "status": "Rrezik i Moderuar",
            "color": "orange"
        }

    elif is_high_vuln and is_high_risk:
        return {
            "quadrant": 4,
            "title": "ALERT I LARTË INTEGRITETI",
            "status": "Rrezik i Lartë - Kapje e Shtetit",
            "color": "red"
        }
