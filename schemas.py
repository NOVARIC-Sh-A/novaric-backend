from pydantic import BaseModel, Field
from typing import List, Optional

class AI_Extraction_Output(BaseModel):
    """
    The strict contract for what the AI must return from a news article.
    """
    # 1. Relevance Filter
    is_political_event: bool = Field(..., description="True if this is about politics/governance")
    
    # 2. Sentiment (The Raw Signal)
    sentiment_score: float = Field(..., description="Sentiment from -1.0 (Very Negative) to 1.0 (Very Positive)")
    
    # 3. Categorization
    primary_topic: str = Field(..., description="e.g., 'Economy', 'Corruption', 'Diplomacy', 'Public Works'")
    
    # 4. Critical Flags (The Hybrid Triggers - Mapped to PARAGON Dimensions)
    has_corruption_allegation: bool = Field(False, description="True if article mentions bribery, abuse of office, SPAK")
    has_legislative_action: bool = Field(False, description="True if politician proposed/voted on law")
    has_international_endorsement: bool = Field(False, description="True if supported by EU/USA/NATO representatives")
    has_public_outcry: bool = Field(False, description="True if article mentions protests or public anger")
    
    # 5. Summary
    brief_summary: str = Field(..., description="1-sentence summary of the event")