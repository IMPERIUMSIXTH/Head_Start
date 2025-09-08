"""
Content Processing Service
Handle content ingestion, embedding generation, and processing

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Process content from various sources and generate embeddings
"""

import httpx
import openai
from typing import List, Dict, Any, Optional
import structlog
from sqlalchemy.orm import Session
from services.models import ContentItem
from services.exceptions import ExternalServiceError, ContentProcessingError
from config.settings import get_settings
import re
import hashlib
import os
from urllib.parse import urlparse, parse_qs
import xml.etree.ElementTree as ET

logger = structlog.get_logger()
settings = get_settings()

# Initialize OpenAI client
openai.api_key = settings.OPENAI_API_KEY

class ContentProcessor:
    """Content processing service"""
    
    def __init__(self):
        self.youtube_api_key = settings.YOUTUBE_API_KEY
        self.arxiv_base_url = settings.ARXIV_API_BASE_URL
        self.max_text_length = 8000  # OpenAI embedding limit
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        try:
            # Truncate text if too long
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length]
            
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=text
            )
            
            embedding = response['data'][0]['embedding']
            logger.info("Embedding generated", text_length=len(text))
            return embedding
            
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            raise ContentProcessingError(f"Failed to generate embedding: {str(e)}")
    
    def extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def process_youtube_content(self, url: str) -> Dict[str, Any]:
        """Process YouTube video content"""
        try:
            video_id = self.extract_youtube_id(url)
            if not video_id:
                raise ContentProcessingError("Invalid YouTube URL")
            
            if not self.youtube_api_key:
                raise ContentProcessingError("YouTube API key not configured")
            
            # Fetch video metadata from YouTube API
            async with httpx.AsyncClient() as client:
                api_url = f"https://www.googleapis.com/youtube/v3/videos"
                params = {
                    'id': video_id,
                    'part': 'snippet,contentDetails,statistics',
                    'key': self.youtube_api_key
                }
                
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get('items'):
                    raise ContentProcessingError("Video not found")
                
                video_data = data['items'][0]
                snippet = video_data['snippet']
                content_details = video_data['contentDetails']
                
                # Parse duration (PT15M33S format)
                duration_str = content_details.get('duration', 'PT0S')
                duration_minutes = self._parse_youtube_duration(duration_str)
                
                # Extract topics from tags and description
                tags = snippet.get('tags', [])
                description = snippet.get('description', '')
                topics = self._extract_topics_from_text(f"{' '.join(tags)} {description}")
                
                # Create embedding text
                embedding_text = f"{snippet['title']} {description}"
                embedding = await self.generate_embedding(embedding_text)
                
                return {
                    'title': snippet['title'],
                    'description': description,
                    'content_type': 'video',
                    'source': 'youtube',
                    'source_id': video_id,
                    'url': url,
                    'duration_minutes': duration_minutes,
                    'topics': topics,
                    'language': snippet.get('defaultLanguage', 'en'),
                    'embedding': embedding,
                    'metadata': {
                        'channel_title': snippet.get('channelTitle'),
                        'published_at': snippet.get('publishedAt'),
                        'view_count': video_data.get('statistics', {}).get('viewCount'),
                        'like_count': video_data.get('statistics', {}).get('likeCount'),
                        'tags': tags
                    }
                }
                
        except httpx.HTTPError as e:
            logger.error("YouTube API request failed", error=str(e))
            raise ExternalServiceError("YouTube API unavailable")
        except Exception as e:
            logger.error("YouTube content processing failed", error=str(e))
            raise ContentProcessingError(f"Failed to process YouTube content: {str(e)}")
    
    def _parse_youtube_duration(self, duration_str: str) -> int:
        """Parse YouTube duration format (PT15M33S) to minutes"""
        import re
        
        # Extract hours, minutes, seconds
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 60 + minutes + (1 if seconds > 0 else 0)  # Round up seconds
    
    async def process_arxiv_content(self, arxiv_id: str) -> Dict[str, Any]:
        """Process arXiv paper content"""
        try:
            # Clean arXiv ID (remove version if present)
            clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
            
            # Fetch paper metadata from arXiv API
            async with httpx.AsyncClient() as client:
                api_url = f"{self.arxiv_base_url}?id_list={clean_id}"
                
                response = await client.get(api_url)
                response.raise_for_status()
                
                # Parse XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                # Find the entry
                entry = root.find('{http://www.w3.org/2005/Atom}entry')
                if entry is None:
                    raise ContentProcessingError("Paper not found")
                
                # Extract metadata
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                
                # Extract authors
                authors = []
                for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                    name = author.find('{http://www.w3.org/2005/Atom}name').text
                    authors.append(name)
                
                # Extract categories (topics)
                categories = []
                for category in entry.findall('{http://www.w3.org/2005/Atom}category'):
                    categories.append(category.get('term'))
                
                # Map arXiv categories to readable topics
                topics = self._map_arxiv_categories(categories)
                
                # Create embedding from title and abstract
                embedding_text = f"{title} {summary}"
                embedding = await self.generate_embedding(embedding_text)
                
                # Get PDF URL
                pdf_url = None
                for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                    if link.get('type') == 'application/pdf':
                        pdf_url = link.get('href')
                        break
                
                return {
                    'title': title,
                    'description': summary,
                    'content_type': 'paper',
                    'source': 'arxiv',
                    'source_id': clean_id,
                    'url': pdf_url or f"https://arxiv.org/abs/{clean_id}",
                    'topics': topics,
                    'language': 'en',
                    'embedding': embedding,
                    'metadata': {
                        'authors': authors,
                        'categories': categories,
                        'arxiv_id': clean_id,
                        'pdf_url': pdf_url
                    }
                }
                
        except httpx.HTTPError as e:
            logger.error("arXiv API request failed", error=str(e))
            raise ExternalServiceError("arXiv API unavailable")
        except Exception as e:
            logger.error("arXiv content processing failed", error=str(e))
            raise ContentProcessingError(f"Failed to process arXiv content: {str(e)}")
    
    def _map_arxiv_categories(self, categories: List[str]) -> List[str]:
        """Map arXiv categories to readable topics"""
        category_mapping = {
            'cs.AI': 'AI',
            'cs.LG': 'Machine Learning',
            'cs.CV': 'Computer Vision',
            'cs.NLP': 'Natural Language Processing',
            'cs.RO': 'Robotics',
            'cs.DB': 'Database',
            'cs.SE': 'Software Engineering',
            'cs.SY': 'Systems and Control',
            'cs.CR': 'Cybersecurity',
            'cs.DC': 'Distributed Computing',
            'cs.DS': 'Data Structures',
            'stat.ML': 'Machine Learning',
            'math.ST': 'Statistics',
            'physics.data-an': 'Data Science'
        }
        
        topics = set()
        for category in categories:
            if category in category_mapping:
                topics.add(category_mapping[category])
            else:
                # Add the category itself if not mapped
                topics.add(category.replace('.', ' ').title())
        
        # Add general topics
        topics.add('Research')
        topics.add('Academic')
        
        return list(topics)[:10]  # Limit to 10 topics
    
    async def process_uploaded_file(self, file_path: str, filename: str, content_type: str) -> Dict[str, Any]:
        """Process uploaded file and extract metadata"""
        try:
            # Determine file type
            file_extension = filename.split('.')[-1].lower()
            
            # Read file content based on type
            if file_extension in ['txt', 'md']:
                content = await self._read_text_file(file_path)
            elif file_extension == 'pdf':
                content = await self._extract_pdf_content(file_path)
            else:
                raise ContentProcessingError(f"Unsupported file type: {file_extension}")
            
            # Generate title from filename
            title = filename.replace(f'.{file_extension}', '').replace('_', ' ').replace('-', ' ').title()
            
            # Extract first paragraph as description
            description = self._extract_description_from_content(content)
            
            # Generate embedding
            embedding = await self.generate_embedding(content)
            
            # Extract topics from content
            topics = self._extract_topics_from_content(content)
            
            # Generate content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            return {
                "title": title,
                "description": description,
                "content_type": "document",
                "source": "upload",
                "source_id": content_hash,
                "url": file_path,
                "duration_minutes": None,
                "topics": topics,
                "language": "en",  # TODO: Implement language detection
                "embedding": embedding,
                "metadata": {
                    "filename": filename,
                    "file_type": file_extension,
                    "file_size": len(content),
                    "content_hash": content_hash
                }
            }
            
        except Exception as e:
            logger.error("File processing failed", error=str(e), filename=filename)
            raise ContentProcessingError(f"Failed to process uploaded file: {str(e)}")
    
    async def _read_text_file(self, file_path: str) -> str:
        """Read text file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ContentProcessingError(f"Failed to read text file: {str(e)}")
    
    async def _extract_pdf_content(self, file_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            import PyPDF2
            
            text_content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
            
            # Clean up the text
            text_content = text_content.strip()
            
            if not text_content:
                raise ContentProcessingError("No text content found in PDF")
            
            return text_content
            
        except ImportError:
            logger.warning("PyPDF2 not installed, using fallback")
            # Fallback: read filename and return basic info
            filename = os.path.basename(file_path)
            return f"PDF document: {filename}. Text extraction requires PyPDF2 library."
        except Exception as e:
            raise ContentProcessingError(f"Failed to extract PDF content: {str(e)}")
    
    def _extract_description_from_content(self, content: str) -> str:
        """Extract description from content"""
        # Get first paragraph or first 200 characters
        paragraphs = content.split('\n\n')
        if paragraphs:
            description = paragraphs[0].strip()
            if len(description) > 200:
                description = description[:200] + "..."
            return description
        
        return content[:200] + "..." if len(content) > 200 else content
    
    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract topics from text using keyword matching"""
        return self._extract_topics_from_content(text)
    
    def _extract_topics_from_content(self, content: str) -> List[str]:
        """Extract topics from content using keyword matching"""
        topics = set()
        content_lower = content.lower()
        
        # Tech topics keyword mapping
        topic_keywords = {
            'AI': ['artificial intelligence', 'ai', 'machine learning', 'neural network'],
            'Machine Learning': ['machine learning', 'ml', 'deep learning', 'algorithm'],
            'Data Science': ['data science', 'data analysis', 'statistics', 'analytics'],
            'Web Development': ['web development', 'html', 'css', 'javascript', 'react', 'vue'],
            'Mobile Development': ['mobile development', 'android', 'ios', 'react native', 'flutter'],
            'DevOps': ['devops', 'docker', 'kubernetes', 'ci/cd', 'deployment'],
            'Database': ['database', 'sql', 'mongodb', 'postgresql', 'mysql'],
            'Programming': ['programming', 'coding', 'software development', 'python', 'java']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.add(topic)
        
        # Add generic topic if no specific topics found
        if not topics:
            topics.add('General')
        
        return list(topics)[:10]  # Limit to 10 topics

# Global content processor instance
content_processor = ContentProcessor()

# Updated 2025-09-05: Comprehensive content processing service with YouTube, arXiv, and file upload support