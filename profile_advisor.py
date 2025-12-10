"""
profile_advisor.py
------------------

This module defines the ProfileAdvisor class, responsible for analyzing
raw user profile data and generating improvement recommendations.

The logic can evolve into a full AI/ML-driven system, but this provides
a clean, extensible, production-safe foundation.
"""

from typing import Dict, List, Any


class ProfileAdvisor:
    """
    ProfileAdvisor analyzes a user's profile and produces
    a structured improvement checklist.

    Example use:
        advisor = ProfileAdvisor(profile_data)
        checklist = advisor.generate_checklist()
    """

    def __init__(self, profile_data: Dict[str, Any]):
        self.profile = profile_data

    def generate_checklist(self) -> List[Dict[str, Any]]:
        """
        Generates an actionable improvement checklist based on
        observed gaps or opportunities in the profile.

        Returns
        -------
        List[Dict[str, Any]]
            A list of recommendation objects.
        """

        checklist = []

        # Example dimensions to evaluate
        self._evaluate_bio(checklist)
        self._evaluate_experience(checklist)
        self._evaluate_skills(checklist)
        self._evaluate_social_presence(checklist)

        return checklist

    # -------------------------------------------------------
    # INTERNAL ANALYSIS HELPERS
    # -------------------------------------------------------

    def _evaluate_bio(self, checklist: List[Dict[str, Any]]):
        bio = self.profile.get("bio", "")

        if not bio or len(bio.strip()) < 50:
            checklist.append({
                "area": "bio",
                "issue": "Short or missing profile biography",
                "recommendation": "Expand the biography with background, achievements, and career goals.",
                "priority": "medium"
            })

    def _evaluate_experience(self, checklist: List[Dict[str, Any]]):
        experience = self.profile.get("experience", [])

        if not experience:
            checklist.append({
                "area": "experience",
                "issue": "No work experience listed",
                "recommendation": "Add previous roles, responsibilities, and accomplishments.",
                "priority": "high"
            })
        else:
            for entry in experience:
                if not entry.get("description"):
                    checklist.append({
                        "area": "experience",
                        "issue": f"Experience entry missing description (role: {entry.get('role', 'unknown')})",
                        "recommendation": "Provide details for each role to highlight responsibilities and results.",
                        "priority": "medium"
                    })

    def _evaluate_skills(self, checklist: List[Dict[str, Any]]):
        skills = self.profile.get("skills", [])

        if not skills:
            checklist.append({
                "area": "skills",
                "issue": "No skills listed",
                "recommendation": "Add core skills and competencies relevant to the industry.",
                "priority": "medium"
            })

    def _evaluate_social_presence(self, checklist: List[Dict[str, Any]]):
        linkedin = self.profile.get("linkedin_url")
        portfolio = self.profile.get("portfolio_url")

        if not linkedin:
            checklist.append({
                "area": "social_presence",
                "issue": "Missing LinkedIn profile",
                "recommendation": "Add a LinkedIn URL to improve professional visibility.",
                "priority": "low"
            })

        if not portfolio and self.profile.get("role") in ["developer", "designer", "creative"]:
            checklist.append({
                "area": "social_presence",
                "issue": "No portfolio provided",
                "recommendation": "Add a personal website or portfolio to showcase your work.",
                "priority": "medium"
            })
