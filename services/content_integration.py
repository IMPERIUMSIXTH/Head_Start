"""
Content Processing Integration Service
Orchestrates the complete content ingestion and processing workflow

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: High-level service to coordinate content processing from ingestion to embedding generation
"""

import structlog
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from services.content_processing import content_processor
from services.models import ContentItem
from services.tasks.content_tasks import process_content_embedding
from services.exceptions import ContentProcessingError, ValidationError
import asyncio

logger = structlog.get_logger()

class ContentIntegrationService:
    """Service to orchestrate complete content processing workflow"""
    
    def __init__(self):
        self.processor = content_processor
    
    async def ingest_and_process_content(
        self, 
        url: str, 
        db: Session,
        process_async: bool = True
    ) -> ContentItem:
        """
        Complete workflow for content ingestion and processing
        
        Args:
            url: Content URL to process
            db: Database session
            process_async: Whether to process embedding asynchronously
            
        Returns:
            ContentItem: Created content item
        """
        logger.info("Starting content ingestion workflow", url=url)
        
        try:
            # Check if content already exists
            existing_content = db.query(ContentItem).filter(
                ContentItem.url == url
            ).first()
            
            if existing_content:
                logger.info("Content already exists", content_id=str(existing_content.id))
                return existing_content
            
            # Determine content source and process
            content_data = await self._process_by_source(url)
            
            # Create content item
            content_item = ContentItem(
                title=content_data["title"],
                description=content_data["description"],
                content_type=content_data["content_type"],
                source=content_data["source"],
                source_id=content_data["source_id"],
                url=content_data["url"],
                duration_minutes=content_data.get("duration_minutes"),
                topics=content_data["topics"],
                language=content_data["language"],
                embedding=content_data["embedding"],
                content_metadata=content_data["metadata"],
                status="pending"  # Requires admin approval
            )
            
            db.add(content_item)
            db.commit()
            db.refresh(content_item)
            
            logger.info("Content ingestion completed", 
                       content_id=str(content_item.id),
                       source=content_data["source"])
            
            return content_item
            
        except Exception as e:
            logger.error("Content ingestion workflow failed", error=str(e), url=url)
            raise ContentProcessingError(f"Content ingestion failed: {str(e)}")
    
    async def _process_by_source(self, url: str) -> Dict[str, Any]:
        """Process content based on its source"""
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return await self.processor.process_youtube_content(url)
        elif 'arxiv.org' in url_lower or 'arxiv' in url_lower:
            # Extract arXiv ID from URL
            arxiv_id = url.split('/')[-1].replace('.pdf', '')
            return await self.processor.process_arxiv_content(arxiv_id)
        else:
            raise ValidationError(f"Unsupported content source: {url}")
    
    async def process_uploaded_file_complete(
        self,
        file_path: str,
        filename: str,
        content_type: str,
        db: Session,
        metadata_overrides: Optional[Dict[str, Any]] = None
    ) -> ContentItem:
        """
        Complete workflow for uploaded file processing
        
        Args:
            file_path: Path to uploaded file
            filename: Original filename
            content_type: MIME content type
            db: Database session
            metadata_overrides: Optional metadata to override
            
        Returns:
            ContentItem: Created content item
        """
        logger.info("Starting file processing workflow", filename=filename)
        
        try:
            # Process the uploaded file
            content_data = await self.processor.process_uploaded_file(
                file_path, filename, content_type
            )
            
            # Apply metadata overrides if provided
            if metadata_overrides:
                content_data.update(metadata_overrides)
            
            # Create content item
            content_item = ContentItem(
                title=content_data["title"],
                description=content_data["description"],
                content_type=content_data["content_type"],
                source=content_data["source"],
                source_id=content_data["source_id"],
                url=file_path,
                topics=content_data["topics"],
                language=content_data["language"],
                embedding=content_data["embedding"],
                content_metadata=content_data["metadata"],
                status="pending"
            )
            
            db.add(content_item)
            db.commit()
            db.refresh(content_item)
            
            logger.info("File processing completed", 
                       content_id=str(content_item.id),
                       filename=filename)
            
            return content_item
            
        except Exception as e:
            logger.error("File processing workflow failed", error=str(e), filename=filename)
            raise ContentProcessingError(f"File processing failed: {str(e)}")
    
    async def batch_process_content_list(
        self,
        content_urls: list[str],
        db: Session,
        batch_size: int = 5
    ) -> Dict[str, Any]:
        """
        Process multiple content items in batches
        
        Args:
            content_urls: List of URLs to process
            db: Database session
            batch_size: Number of items to process concurrently
            
        Returns:
            Dict with processing results
        """
        logger.info("Starting batch content processing", 
                   total_items=len(content_urls), 
                   batch_size=batch_size)
        
        results = {
            "processed": [],
            "failed": [],
            "skipped": []
        }
        
        # Process in batches to avoid overwhelming external APIs
        for i in range(0, len(content_urls), batch_size):
            batch = content_urls[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = []
            for url in batch:
                task = self.ingest_and_process_content(url, db)
                batch_tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for url, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error("Batch item failed", url=url, error=str(result))
                    results["failed"].append({"url": url, "error": str(result)})
                elif result:
                    results["processed"].append({
                        "url": url, 
                        "content_id": str(result.id)
                    })
                else:
                    results["skipped"].append({"url": url, "reason": "Already exists"})
        
        logger.info("Batch processing completed", 
                   processed=len(results["processed"]),
                   failed=len(results["failed"]),
                   skipped=len(results["skipped"]))
        
        return results
    
    def validate_content_source(self, url: str) -> bool:
        """Validate if content source is supported"""
        url_lower = url.lower()
        
        supported_sources = [
            'youtube.com',
            'youtu.be',
            'arxiv.org'
        ]
        
        return any(source in url_lower for source in supported_sources)
    
    def get_supported_file_types(self) -> list[str]:
        """Get list of supported file types for upload"""
        return ['.txt', '.md', '.pdf']
    
    def get_content_processing_stats(self, db: Session) -> Dict[str, Any]:
        """Get statistics about content processing"""
        try:
            # Get content counts by source
            from sqlalchemy import func
            
            source_stats = db.query(
                ContentItem.source,
                func.count(ContentItem.id).label('total'),
                func.count(ContentItem.id).filter(ContentItem.status == 'approved').label('approved'),
                func.count(ContentItem.id).filter(ContentItem.status == 'pending').label('pending'),
                func.count(ContentItem.id).filter(ContentItem.status == 'rejected').label('rejected')
            ).group_by(ContentItem.source).all()
            
            stats = {
                "sources": {},
                "total_content": 0,
                "approved_content": 0,
                "pending_content": 0,
                "rejected_content": 0
            }
            
            for stat in source_stats:
                stats["sources"][stat.source] = {
                    "total": stat.total,
                    "approved": stat.approved,
                    "pending": stat.pending,
                    "rejected": stat.rejected
                }
                
                stats["total_content"] += stat.total
                stats["approved_content"] += stat.approved
                stats["pending_content"] += stat.pending
                stats["rejected_content"] += stat.rejected
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get content processing stats", error=str(e))
            return {"error": str(e)}

# Global integration service instance
content_integration_service = ContentIntegrationService()

# Updated 2025-09-05: Content processing integration service