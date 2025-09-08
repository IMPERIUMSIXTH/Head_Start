"""
Content Management API Routes
Content ingestion, search, and management endpoints

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Handle content ingestion from various sources and content management
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, HttpUrl, validator
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Dict, Any, Optional
import structlog
import os
import uuid
from services.database import get_db
from services.models import ContentItem, User
from services.dependencies import get_current_active_user, get_current_verified_user, require_admin
from services.content_processing import content_processor
from services.exceptions import ContentProcessingError, ValidationError, NotFoundError
from config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter()
settings = get_settings()

# Pydantic models for request/response
class ContentIngestRequest(BaseModel):
    url: HttpUrl
    content_type: Optional[str] = None
    
    @validator('url')
    def validate_url(cls, v):
        url_str = str(v)
        if not (url_str.startswith('https://youtube.com/') or 
                url_str.startswith('https://youtu.be/') or
                url_str.startswith('https://arxiv.org/') or
                'arxiv' in url_str.lower()):
            raise ValueError('Only YouTube and arXiv URLs are supported')
        return v

class ContentResponse(BaseModel):
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
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True

class ContentSearchRequest(BaseModel):
    query: Optional[str] = None
    content_types: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    difficulty_levels: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    limit: int = 20
    offset: int = 0
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v

class ContentSearchResponse(BaseModel):
    items: List[ContentResponse]
    total: int
    limit: int
    offset: int

@router.post("/ingest", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_content(
    request: ContentIngestRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Ingest content from external sources (YouTube, arXiv)"""
    logger.info("Content ingestion request", url=str(request.url), user_id=str(current_user.id))
    
    try:
        url_str = str(request.url)
        
        # Check if content already exists
        existing_content = db.query(ContentItem).filter(
            ContentItem.url == url_str
        ).first()
        
        if existing_content:
            logger.info("Content already exists", content_id=str(existing_content.id))
            return ContentResponse(
                id=str(existing_content.id),
                title=existing_content.title,
                description=existing_content.description,
                content_type=existing_content.content_type,
                source=existing_content.source,
                url=existing_content.url,
                duration_minutes=existing_content.duration_minutes,
                difficulty_level=existing_content.difficulty_level,
                topics=existing_content.topics,
                language=existing_content.language,
                status=existing_content.status,
                created_at=existing_content.created_at.isoformat(),
                metadata=existing_content.metadata
            )
        
        # Process content based on source
        if 'youtube.com' in url_str or 'youtu.be' in url_str:
            content_data = await content_processor.process_youtube_content(url_str)
        elif 'arxiv.org' in url_str or 'arxiv' in url_str.lower():
            # Extract arXiv ID from URL
            arxiv_id = url_str.split('/')[-1].replace('.pdf', '')
            content_data = await content_processor.process_arxiv_content(arxiv_id)
        else:
            raise ValidationError("Unsupported content source")
        
        # Create content item
        content_item = ContentItem(
            title=content_data["title"],
            description=content_data["description"],
            content_type=content_data["content_type"],
            source=content_data["source"],
            source_id=content_data["source_id"],
            url=content_data["url"],
            duration_minutes=content_data["duration_minutes"],
            topics=content_data["topics"],
            language=content_data["language"],
            embedding=content_data["embedding"],
            metadata=content_data["metadata"],
            status="pending"  # Requires admin approval
        )
        
        db.add(content_item)
        db.commit()
        db.refresh(content_item)
        
        logger.info("Content ingested successfully", 
                   content_id=str(content_item.id), 
                   source=content_data["source"])
        
        return ContentResponse(
            id=str(content_item.id),
            title=content_item.title,
            description=content_item.description,
            content_type=content_item.content_type,
            source=content_item.source,
            url=content_item.url,
            duration_minutes=content_item.duration_minutes,
            difficulty_level=content_item.difficulty_level,
            topics=content_item.topics,
            language=content_item.language,
            status=content_item.status,
            created_at=content_item.created_at.isoformat(),
            metadata=content_item.metadata
        )
        
    except ContentProcessingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Content ingestion failed", error=str(e), url=str(request.url))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content ingestion failed"
        )

@router.post("/upload", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def upload_content(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    topics: Optional[str] = Form(None),  # Comma-separated topics
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Upload custom content file"""
    logger.info("File upload request", filename=file.filename, user_id=str(current_user.id))
    
    try:
        # Validate file type
        allowed_extensions = ['.txt', '.md', '.pdf']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise ValidationError(f"File type {file_extension} not supported. Allowed: {allowed_extensions}")
        
        # Validate file size
        max_size = settings.get_upload_size_bytes()
        file_content = await file.read()
        
        if len(file_content) > max_size:
            raise ValidationError(f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE}")
        
        # Save file temporarily
        upload_dir = settings.UPLOAD_PATH
        os.makedirs(upload_dir, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Process uploaded file
        content_data = await content_processor.process_uploaded_file(
            file_path, file.filename, file.content_type
        )
        
        # Override with user-provided metadata if available
        if title:
            content_data["title"] = title
        if description:
            content_data["description"] = description
        if topics:
            content_data["topics"] = [t.strip() for t in topics.split(',')]
        
        # Create content item
        content_item = ContentItem(
            title=content_data["title"],
            description=content_data["description"],
            content_type=content_data["content_type"],
            source=content_data["source"],
            source_id=content_data["source_id"],
            url=file_path,  # Store local file path
            topics=content_data["topics"],
            language=content_data["language"],
            embedding=content_data["embedding"],
            metadata=content_data["metadata"],
            status="pending"  # Requires admin approval
        )
        
        db.add(content_item)
        db.commit()
        db.refresh(content_item)
        
        logger.info("File uploaded successfully", 
                   content_id=str(content_item.id), 
                   filename=file.filename)
        
        return ContentResponse(
            id=str(content_item.id),
            title=content_item.title,
            description=content_item.description,
            content_type=content_item.content_type,
            source=content_item.source,
            url=content_item.url,
            duration_minutes=content_item.duration_minutes,
            difficulty_level=content_item.difficulty_level,
            topics=content_item.topics,
            language=content_item.language,
            status=content_item.status,
            created_at=content_item.created_at.isoformat(),
            metadata=content_item.metadata
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ContentProcessingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error("File upload failed", error=str(e), filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )

@router.post("/search", response_model=ContentSearchResponse)
async def search_content(
    search_request: ContentSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search content with filters"""
    logger.info("Content search request", query=search_request.query, user_id=str(current_user.id))
    
    try:
        # Build query
        query = db.query(ContentItem).filter(ContentItem.status == 'approved')
        
        # Apply filters
        if search_request.query:
            # Text search in title and description
            search_term = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    ContentItem.title.ilike(search_term),
                    ContentItem.description.ilike(search_term)
                )
            )
        
        if search_request.content_types:
            query = query.filter(ContentItem.content_type.in_(search_request.content_types))
        
        if search_request.topics:
            # Filter by topics (array contains any of the specified topics)
            for topic in search_request.topics:
                query = query.filter(ContentItem.topics.contains([topic]))
        
        if search_request.difficulty_levels:
            query = query.filter(ContentItem.difficulty_level.in_(search_request.difficulty_levels))
        
        if search_request.languages:
            query = query.filter(ContentItem.language.in_(search_request.languages))
        
        if search_request.sources:
            query = query.filter(ContentItem.source.in_(search_request.sources))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        items = query.offset(search_request.offset).limit(search_request.limit).all()
        
        # Convert to response format
        content_items = []
        for item in items:
            content_items.append(ContentResponse(
                id=str(item.id),
                title=item.title,
                description=item.description,
                content_type=item.content_type,
                source=item.source,
                url=item.url,
                duration_minutes=item.duration_minutes,
                difficulty_level=item.difficulty_level,
                topics=item.topics,
                language=item.language,
                status=item.status,
                created_at=item.created_at.isoformat(),
                metadata=item.metadata
            ))
        
        logger.info("Content search completed", 
                   results_count=len(content_items), 
                   total=total)
        
        return ContentSearchResponse(
            items=content_items,
            total=total,
            limit=search_request.limit,
            offset=search_request.offset
        )
        
    except Exception as e:
        logger.error("Content search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content search failed"
        )

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific content item"""
    logger.info("Content retrieval request", content_id=content_id, user_id=str(current_user.id))
    
    try:
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Only show approved content to regular users
        if content.status != 'approved' and current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return ContentResponse(
            id=str(content.id),
            title=content.title,
            description=content.description,
            content_type=content.content_type,
            source=content.source,
            url=content.url,
            duration_minutes=content.duration_minutes,
            difficulty_level=content.difficulty_level,
            topics=content.topics,
            language=content.language,
            status=content.status,
            created_at=content.created_at.isoformat(),
            metadata=content.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Content retrieval failed", error=str(e), content_id=content_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content retrieval failed"
        )

@router.get("/sources/available")
async def get_available_sources(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get available content sources and their statistics"""
    logger.info("Available sources request", user_id=str(current_user.id))
    
    try:
        # Get source statistics
        source_stats = db.query(
            ContentItem.source,
            func.count(ContentItem.id).label('count'),
            func.count(ContentItem.id).filter(ContentItem.status == 'approved').label('approved_count')
        ).group_by(ContentItem.source).all()
        
        sources = []
        for stat in source_stats:
            sources.append({
                "source": stat.source,
                "total_content": stat.count,
                "approved_content": stat.approved_count,
                "supported": True
            })
        
        # Add supported sources that might not have content yet
        supported_sources = ['youtube', 'arxiv', 'upload']
        existing_sources = [s['source'] for s in sources]
        
        for source in supported_sources:
            if source not in existing_sources:
                sources.append({
                    "source": source,
                    "total_content": 0,
                    "approved_content": 0,
                    "supported": True
                })
        
        return {
            "sources": sources,
            "total_sources": len(sources)
        }
        
    except Exception as e:
        logger.error("Available sources retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available sources"
        )

# Updated 2025-09-05: Complete content management API with ingestion, upload, and search