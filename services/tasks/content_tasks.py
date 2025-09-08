"""
Content Processing Celery Tasks
Background tasks for content ingestion and processing

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Background tasks for content processing, embedding generation, and batch operations
"""

from celery import current_task
from sqlalchemy.orm import Session
import structlog
from services.celery_app import celery_app
from services.database import SessionLocal
from services.models import ContentItem
from services.content_processing import content_processor
from services.exceptions import ContentProcessingError

logger = structlog.get_logger()

def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_content_embedding(self, content_id: str):
    """Generate embedding for content item"""
    logger.info("Processing content embedding", content_id=content_id, task_id=self.request.id)
    
    db = get_db_session()
    try:
        # Get content item
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        if not content:
            logger.error("Content not found", content_id=content_id)
            return {"status": "error", "message": "Content not found"}
        
        # Skip if embedding already exists
        if content.embedding:
            logger.info("Embedding already exists", content_id=content_id)
            return {"status": "skipped", "message": "Embedding already exists"}
        
        # Generate embedding
        text_content = f"{content.title} {content.description or ''}"
        embedding = await content_processor.generate_embedding(text_content)
        
        # Update content with embedding
        content.embedding = embedding
        db.commit()
        
        logger.info("Embedding generated successfully", content_id=content_id)
        return {"status": "success", "message": "Embedding generated"}
        
    except Exception as e:
        logger.error("Embedding generation failed", error=str(e), content_id=content_id)
        
        # Retry on failure
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for embedding generation", content_id=content_id)
            return {"status": "failed", "message": str(e)}
    
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def batch_process_youtube_playlist(self, playlist_url: str, user_id: str):
    """Process entire YouTube playlist"""
    logger.info("Processing YouTube playlist", playlist_url=playlist_url, user_id=user_id)
    
    db = get_db_session()
    try:
        # TODO: Implement YouTube playlist processing
        # This would involve:
        # 1. Extract playlist ID from URL
        # 2. Get all video URLs from playlist
        # 3. Process each video individually
        # 4. Create content items for each video
        
        logger.info("Playlist processing completed", playlist_url=playlist_url)
        return {"status": "success", "message": "Playlist processed"}
        
    except Exception as e:
        logger.error("Playlist processing failed", error=str(e), playlist_url=playlist_url)
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for playlist processing", playlist_url=playlist_url)
            return {"status": "failed", "message": str(e)}
    
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def batch_update_content_metadata(self, source: str):
    """Batch update metadata for content from specific source"""
    logger.info("Batch updating content metadata", source=source)
    
    db = get_db_session()
    try:
        # Get content items that need metadata updates
        content_items = db.query(ContentItem).filter(
            ContentItem.source == source,
            ContentItem.status == 'approved'
        ).limit(100).all()  # Process in batches of 100
        
        updated_count = 0
        for content in content_items:
            try:
                if source == 'youtube' and content.source_id:
                    # Re-fetch YouTube metadata
                    updated_data = await content_processor.process_youtube_content(content.url)
                    
                    # Update metadata
                    content.metadata = updated_data["metadata"]
                    content.topics = updated_data["topics"]
                    updated_count += 1
                    
                elif source == 'arxiv' and content.source_id:
                    # Re-fetch arXiv metadata
                    updated_data = await content_processor.process_arxiv_content(content.source_id)
                    
                    # Update metadata
                    content.metadata = updated_data["metadata"]
                    content.topics = updated_data["topics"]
                    updated_count += 1
                
            except Exception as e:
                logger.warning("Failed to update content metadata", 
                             content_id=str(content.id), error=str(e))
                continue
        
        db.commit()
        
        logger.info("Batch metadata update completed", 
                   source=source, updated_count=updated_count)
        return {"status": "success", "updated_count": updated_count}
        
    except Exception as e:
        logger.error("Batch metadata update failed", error=str(e), source=source)
        
        try:
            self.retry(countdown=300 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for batch metadata update", source=source)
            return {"status": "failed", "message": str(e)}
    
    finally:
        db.close()

@celery_app.task(bind=True)
def cleanup_failed_uploads(self):
    """Clean up failed or orphaned file uploads"""
    logger.info("Cleaning up failed uploads")
    
    db = get_db_session()
    try:
        # Find content items with upload source that are older than 24 hours and still pending
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        failed_uploads = db.query(ContentItem).filter(
            ContentItem.source == 'upload',
            ContentItem.status == 'pending',
            ContentItem.created_at < cutoff_time
        ).all()
        
        cleaned_count = 0
        for content in failed_uploads:
            try:
                # Remove file if it exists
                import os
                if content.url and os.path.exists(content.url):
                    os.remove(content.url)
                
                # Remove database record
                db.delete(content)
                cleaned_count += 1
                
            except Exception as e:
                logger.warning("Failed to clean up upload", 
                             content_id=str(content.id), error=str(e))
                continue
        
        db.commit()
        
        logger.info("Upload cleanup completed", cleaned_count=cleaned_count)
        return {"status": "success", "cleaned_count": cleaned_count}
        
    except Exception as e:
        logger.error("Upload cleanup failed", error=str(e))
        return {"status": "failed", "message": str(e)}
    
    finally:
        db.close()

@celery_app.task(bind=True)
def generate_content_difficulty_levels(self):
    """Analyze content and assign difficulty levels"""
    logger.info("Generating content difficulty levels")
    
    db = get_db_session()
    try:
        # Get content items without difficulty levels
        content_items = db.query(ContentItem).filter(
            ContentItem.difficulty_level.is_(None),
            ContentItem.status == 'approved'
        ).limit(50).all()  # Process in batches
        
        updated_count = 0
        for content in content_items:
            try:
                # Simple heuristic for difficulty level
                difficulty = _analyze_content_difficulty(content)
                content.difficulty_level = difficulty
                updated_count += 1
                
            except Exception as e:
                logger.warning("Failed to analyze content difficulty", 
                             content_id=str(content.id), error=str(e))
                continue
        
        db.commit()
        
        logger.info("Difficulty level generation completed", updated_count=updated_count)
        return {"status": "success", "updated_count": updated_count}
        
    except Exception as e:
        logger.error("Difficulty level generation failed", error=str(e))
        return {"status": "failed", "message": str(e)}
    
    finally:
        db.close()

def _analyze_content_difficulty(content: ContentItem) -> str:
    """Analyze content and determine difficulty level"""
    # Simple heuristic based on content characteristics
    
    # Check for beginner keywords
    beginner_keywords = [
        'introduction', 'basics', 'getting started', 'beginner', 'tutorial',
        'fundamentals', 'overview', 'primer', '101'
    ]
    
    # Check for advanced keywords
    advanced_keywords = [
        'advanced', 'expert', 'deep dive', 'optimization', 'architecture',
        'performance', 'scalability', 'research', 'cutting-edge'
    ]
    
    text_content = f"{content.title} {content.description or ''}".lower()
    
    # Count keyword matches
    beginner_score = sum(1 for keyword in beginner_keywords if keyword in text_content)
    advanced_score = sum(1 for keyword in advanced_keywords if keyword in text_content)
    
    # Determine difficulty based on scores and other factors
    if beginner_score > advanced_score:
        return 'beginner'
    elif advanced_score > beginner_score:
        return 'advanced'
    else:
        # Default to intermediate
        return 'intermediate'

# Updated 2025-09-05: Comprehensive content processing Celery tasks