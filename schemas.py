# schemas.py
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


# ============================================================
# EXPERIENCE MODEL
# ============================================================
class ExperienceItem(BaseModel):
    role: Optional[str] = None
    organization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


# ============================================================
# EDUCATION MODEL
# ============================================================
class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None


# ============================================================
# CHECKLIST / AI IMPROVEMENT MODEL
# ============================================================
class ChecklistItem(BaseModel):
    id: str
    category: str
    task: str
    academic_ref: str
    is_completed: bool
    priority: str


# ============================================================
# VIP PROFILE RESPONSE (MAIN MODEL)
# ============================================================
class VipProfileResponse(BaseModel):
    """
    Final enriched VIP profile schema.

    Used by:
        GET /api/profile/{profile_id}

    Includes:
        - User identity
        - Social/Professional metadata
        - Education & Experience
        - Political attributes (optional)
        - AI enrichment output (checklist)
    """

    # ----------------------------------------
    # CORE IDENTITY
    # ----------------------------------------
    id: str
    name: str
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None

    # ----------------------------------------
    # PROFILE CONTENT
    # ----------------------------------------
    bio: Optional[str] = None
    headline: Optional[str] = None  # e.g. "Minister of Finance"

    # ----------------------------------------
    # CONTACT / URL FIELDS
    # ----------------------------------------
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    official_website: Optional[str] = None

    # ----------------------------------------
    # SKILLS & ATTRIBUTES
    # ----------------------------------------
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

    # ----------------------------------------
    # EXPERIENCE & EDUCATION
    # ----------------------------------------
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)

    # ----------------------------------------
    # POLITICAL / PUBLIC-SECTOR METADATA
    # ----------------------------------------
    current_position: Optional[str] = None
    political_party: Optional[str] = None
    region: Optional[str] = None
    is_active_politician: Optional[bool] = None

    # ----------------------------------------
    # SYSTEM METADATA
    # ----------------------------------------
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    profile_image_url: Optional[str] = None
    verified: bool = False

    # ----------------------------------------
    # AI ENRICHMENT OUTPUT
    # ----------------------------------------
    improvement_checklist: List[ChecklistItem] = Field(
        default_factory=list,
        description="AI-generated improvement recommendations for the profile.",
    )


# ============================================================
# POLITICIAN CARD RESPONSE (PoliticiansPage)
# ============================================================
class PoliticianCardResponse(BaseModel):
    """
    Lightweight card schema for Politicians page.

    Used by:
        GET /api/politicians/cards
    """

    id: str
    name: str
    imageUrl: Optional[str] = None
    category: str
    shortBio: Optional[str] = None
    dynamicScore: int = 0
    clickCount: Optional[int] = None
    audienceRating: Optional[int] = None
    slug: Optional[str] = None
