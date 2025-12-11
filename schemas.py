from pydantic import BaseModel, Field
from typing import List, Optional


# ============================================================
# EXPERIENCE MODEL
# ============================================================
class ExperienceItem(BaseModel):
    role: Optional[str]
    organization: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    description: Optional[str]


# ============================================================
# EDUCATION MODEL
# ============================================================
class EducationItem(BaseModel):
    institution: Optional[str]
    degree: Optional[str]
    field_of_study: Optional[str]
    start_year: Optional[int]
    end_year: Optional[int]


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
    gender: Optional[str]
    date_of_birth: Optional[str]
    nationality: Optional[str]

    # ----------------------------------------
    # PROFILE CONTENT
    # ----------------------------------------
    bio: Optional[str]
    headline: Optional[str]   # e.g. "Minister of Finance"

    # ----------------------------------------
    # CONTACT / URL FIELDS
    # ----------------------------------------
    linkedin_url: Optional[str]
    twitter_url: Optional[str]
    facebook_url: Optional[str]
    instagram_url: Optional[str]
    portfolio_url: Optional[str]
    official_website: Optional[str]

    # ----------------------------------------
    # SKILLS & ATTRIBUTES
    # ----------------------------------------
    skills: Optional[List[str]] = Field(default_factory=list)
    languages: Optional[List[str]] = Field(default_factory=list)

    # ----------------------------------------
    # EXPERIENCE & EDUCATION
    # ----------------------------------------
    experience: Optional[List[ExperienceItem]] = Field(default_factory=list)
    education: Optional[List[EducationItem]] = Field(default_factory=list)

    # ----------------------------------------
    # POLITICAL / PUBLIC-SECTOR METADATA
    # ----------------------------------------
    current_position: Optional[str]
    political_party: Optional[str]
    region: Optional[str]
    is_active_politician: Optional[bool]

    # ----------------------------------------
    # SYSTEM METADATA
    # ----------------------------------------
    created_at: Optional[str]
    updated_at: Optional[str]
    profile_image_url: Optional[str]
    verified: Optional[bool] = False

    # ----------------------------------------
    # AI ENRICHMENT OUTPUT
    # ----------------------------------------
    improvement_checklist: Optional[List[ChecklistItem]] = Field(
        default_factory=list,
        description="AI-generated improvement recommendations for the profile."
    )
