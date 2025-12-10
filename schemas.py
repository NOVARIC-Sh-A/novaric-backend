from pydantic import BaseModel, Field
from typing import List, Optional


class ExperienceItem(BaseModel):
    role: Optional[str]
    organization: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    description: Optional[str]


class EducationItem(BaseModel):
    institution: Optional[str]
    degree: Optional[str]
    field_of_study: Optional[str]
    start_year: Optional[int]
    end_year: Optional[int]


class ChecklistItem(BaseModel):
    id: str
    category: str
    task: str
    academic_ref: str
    is_completed: bool
    priority: str


class VipProfileResponse(BaseModel):
    """
    Final enriched VIP profile schema used by GET /profile/{profile_id}.
    This schema consolidates all fields referenced in the DB + enrichment layer.
    """

    # Core identity
    id: str
    name: str
    gender: Optional[str]
    date_of_birth: Optional[str]
    nationality: Optional[str]

    # Profile content
    bio: Optional[str]
    headline: Optional[str]  # short tagline, e.g., "Minister of Finance"

    # Contact / URLs
    linkedin_url: Optional[str]
    twitter_url: Optional[str]
    facebook_url: Optional[str]
    instagram_url: Optional[str]
    portfolio_url: Optional[str]
    official_website: Optional[str]

    # Skills & Attributes
    skills: Optional[List[str]] = Field(default_factory=list)
    languages: Optional[List[str]] = Field(default_factory=list)

    # Experience & Education
    experience: Optional[List[ExperienceItem]] = Field(default_factory=list)
    education: Optional[List[EducationItem]] = Field(default_factory=list)

    # Political / Public-sector fields
    current_position: Optional[str]
    political_party: Optional[str]
    region: Optional[str]
    is_active_politician: Optional[bool]

    # Metadata
    created_at: Optional[str]
    updated_at: Optional[str]
    profile_image_url: Optional[str]
    verified: Optional[bool] = False

    # AI enrichment output (new)
    improvement_checklist: Optional[List[ChecklistItem]] = Field(
        default_factory=list,
        description="AI-generated improvement recommendations for the profile."
    )
