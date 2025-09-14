"""
Content Management API Routes
Content CRUD operations and management endpoints

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Content management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import structlog

from services.database import get_db
from services.models import ContentItem, User, UserInteraction
from services.dependencies import get_current_active_user, get_current_admin_user
from services.exceptions import NotFoundError, ValidationError
from services.ai_client import get_ai_client

logger = structlog.get_logger()
router = APIRouter()

class ContentResponse(BaseModel):
    """Content response model"""
    id: str
    title: str
    description: Optional[str]
    content_type: str
    source: str
    url: Optional[str]
    duration_minutes: Optional[int]
    difficulty_level: Optional[str]
    topics: List[str]
    language: str
    status: str
    created_at: str
    
    class Config:
        from_attributes = True

class ContentCreateRequest(BaseModel):
    """Request model for creating new content resource"""
    title: str
    description: Optional[str] = None
    content_type: str
    source: str
    url: Optional[str] = None
    duration_minutes: Optional[int] = None
    difficulty_level: Optional[str] = None
    topics: List[str] = []
    language: str = "en"

@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def add_content_resource(
    content_data: ContentCreateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Add new learning resource with embedding vector stored in DB"""
    logger.info("Add content resource request", user_id=str(current_user.id), title=content_data.title)
    
    try:
        ai_client = get_ai_client()
        
        # Generate embedding for the resource title + description
        text_to_embed = content_data.title
        if content_data.description:
            text_to_embed += " " + content_data.description
        
        embedding = await ai_client.generate_embedding(text_to_embed)
        
        # Create new ContentItem
        new_content = ContentItem(
            title=content_data.title,
            description=content_data.description,
            content_type=content_data.content_type,
            source=content_data.source,
            url=content_data.url,
            duration_minutes=content_data.duration_minutes,
            difficulty_level=content_data.difficulty_level,
            topics=content_data.topics,
            language=content_data.language,
            embedding=embedding,
            status="pending"  # Admin approval workflow
        )
        
        db.add(new_content)
        db.commit()
        db.refresh(new_content)
        
        logger.info("Content resource added", content_id=str(new_content.id))
        
        return ContentResponse(
            id=str(new_content.id),
            title=new_content.title,
            description=new_content.description,
            content_type=new_content.content_type,
            source=new_content.source,
            url=new_content.url,
            duration_minutes=new_content.duration_minutes,
            difficulty_level=new_content.difficulty_level,
            topics=new_content.topics or [],
            language=new_content.language,
            status=new_content.status,
            created_at=new_content.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to add content resource", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add content resource"
        )

class InteractionCreateRequest(BaseModel):
    """Request model for recording user interactions"""
    content_id: str
    interaction_type: str
    rating: Optional[int] = None
    feedback_text: Optional[str] = None
    time_spent_minutes: Optional[int] = None
    completion_percentage: Optional[float] = None

@router.post("/interactions", status_code=status.HTTP_201_CREATED)
async def record_user_interaction(
    interaction_data: InteractionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Record user interactions with resources (views, likes, completions)"""
    logger.info("Record interaction request",
               user_id=str(current_user.id),
               content_id=interaction_data.content_id,
               interaction_type=interaction_data.interaction_type)

    try:
        # Verify content exists
        content = db.query(ContentItem).filter(ContentItem.id == interaction_data.content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )

        # Create new interaction
        new_interaction = UserInteraction(
            user_id=current_user.id,
            content_id=interaction_data.content_id,
            interaction_type=interaction_data.interaction_type,
            rating=interaction_data.rating,
            feedback_text=interaction_data.feedback_text,
            time_spent_minutes=interaction_data.time_spent_minutes,
            completion_percentage=interaction_data.completion_percentage
        )

        db.add(new_interaction)
        db.commit()
        db.refresh(new_interaction)

        logger.info("User interaction recorded",
                   interaction_id=str(new_interaction.id),
                   user_id=str(current_user.id),
                   content_id=interaction_data.content_id)

        return {
            "message": "Interaction recorded successfully",
            "interaction_id": str(new_interaction.id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to record interaction", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record interaction"
        )
