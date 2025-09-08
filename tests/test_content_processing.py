"""
Content Processing Tests
Test content ingestion and processing functionality

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Test content processing pipeline components
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from services.content_processing import ContentProcessor
from services.exceptions import ContentProcessingError, ExternalServiceError

@pytest.fixture
def content_processor():
    """Create content processor instance for testing"""
    return ContentProcessor()

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI embedding response"""
    return {
        'data': [{'embedding': [0.1, 0.2, 0.3] * 512}]  # 1536 dimensions
    }

class TestContentProcessor:
    """Test content processor functionality"""
    
    def test_extract_youtube_id_standard_url(self, content_processor):
        """Test YouTube ID extraction from standard URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = content_processor.extract_youtube_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_youtube_id_short_url(self, content_processor):
        """Test YouTube ID extraction from short URL"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = content_processor.extract_youtube_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_youtube_id_embed_url(self, content_processor):
        """Test YouTube ID extraction from embed URL"""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = content_processor.extract_youtube_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_youtube_id_invalid_url(self, content_processor):
        """Test YouTube ID extraction from invalid URL"""
        url = "https://example.com/video"
        video_id = content_processor.extract_youtube_id(url)
        assert video_id is None
    
    def test_parse_youtube_duration(self, content_processor):
        """Test YouTube duration parsing"""
        # Test various duration formats
        assert content_processor._parse_youtube_duration("PT15M33S") == 16  # 15:33 -> 16 minutes
        assert content_processor._parse_youtube_duration("PT1H30M") == 90   # 1:30:00 -> 90 minutes
        assert content_processor._parse_youtube_duration("PT45S") == 1      # 45 seconds -> 1 minute
        assert content_processor._parse_youtube_duration("PT2H") == 120     # 2 hours -> 120 minutes
        assert content_processor._parse_youtube_duration("PT0S") == 0       # 0 seconds -> 0 minutes
    
    @patch('services.content_processing.openai.Embedding.acreate')
    async def test_generate_embedding_success(self, mock_openai, content_processor, mock_openai_response):
        """Test successful embedding generation"""
        mock_openai.return_value = mock_openai_response
        
        text = "This is a test text for embedding generation"
        embedding = await content_processor.generate_embedding(text)
        
        assert embedding == mock_openai_response['data'][0]['embedding']
        mock_openai.assert_called_once()
    
    @patch('services.content_processing.openai.Embedding.acreate')
    async def test_generate_embedding_failure(self, mock_openai, content_processor):
        """Test embedding generation failure"""
        mock_openai.side_effect = Exception("OpenAI API error")
        
        text = "This is a test text"
        
        with pytest.raises(ContentProcessingError):
            await content_processor.generate_embedding(text)
    
    def test_extract_topics_from_content(self, content_processor):
        """Test topic extraction from content"""
        content = "This is about machine learning and artificial intelligence in Python programming"
        topics = content_processor._extract_topics_from_content(content)
        
        assert "AI" in topics
        assert "Machine Learning" in topics
        assert "Programming" in topics
    
    def test_extract_topics_from_content_no_matches(self, content_processor):
        """Test topic extraction with no keyword matches"""
        content = "This is some random content about cooking recipes"
        topics = content_processor._extract_topics_from_content(content)
        
        assert "General" in topics
        assert len(topics) >= 1
    
    def test_map_arxiv_categories(self, content_processor):
        """Test arXiv category mapping"""
        categories = ['cs.AI', 'cs.LG', 'unknown.category']
        topics = content_processor._map_arxiv_categories(categories)
        
        assert "AI" in topics
        assert "Machine Learning" in topics
        assert "Research" in topics
        assert "Academic" in topics
        assert "Unknown Category" in topics  # Unknown category should be converted
    
    async def test_read_text_file_success(self, content_processor, tmp_path):
        """Test successful text file reading"""
        # Create temporary text file
        test_file = tmp_path / "test.txt"
        test_content = "This is test content for file reading"
        test_file.write_text(test_content)
        
        content = await content_processor._read_text_file(str(test_file))
        assert content == test_content
    
    async def test_read_text_file_not_found(self, content_processor):
        """Test text file reading with non-existent file"""
        with pytest.raises(ContentProcessingError):
            await content_processor._read_text_file("non_existent_file.txt")
    
    def test_extract_description_from_content_short(self, content_processor):
        """Test description extraction from short content"""
        content = "Short content"
        description = content_processor._extract_description_from_content(content)
        assert description == "Short content"
    
    def test_extract_description_from_content_long(self, content_processor):
        """Test description extraction from long content"""
        content = "A" * 300  # 300 character string
        description = content_processor._extract_description_from_content(content)
        assert len(description) <= 203  # 200 chars + "..."
        assert description.endswith("...")
    
    def test_extract_description_from_content_paragraphs(self, content_processor):
        """Test description extraction with multiple paragraphs"""
        content = "First paragraph content.\n\nSecond paragraph content."
        description = content_processor._extract_description_from_content(content)
        assert description == "First paragraph content."

class TestContentProcessorIntegration:
    """Integration tests for content processor"""
    
    @patch('httpx.AsyncClient.get')
    @patch('services.content_processing.openai.Embedding.acreate')
    async def test_process_youtube_content_success(self, mock_openai, mock_http, content_processor, mock_openai_response):
        """Test successful YouTube content processing"""
        # Mock YouTube API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [{
                'snippet': {
                    'title': 'Test Video',
                    'description': 'Test description',
                    'tags': ['test', 'video'],
                    'channelTitle': 'Test Channel',
                    'publishedAt': '2023-01-01T00:00:00Z',
                    'defaultLanguage': 'en'
                },
                'contentDetails': {
                    'duration': 'PT15M33S'
                },
                'statistics': {
                    'viewCount': '1000',
                    'likeCount': '100'
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_http.return_value.__aenter__.return_value.get.return_value = mock_response
        
        # Mock OpenAI embedding
        mock_openai.return_value = mock_openai_response
        
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = await content_processor.process_youtube_content(url)
        
        assert result['title'] == 'Test Video'
        assert result['content_type'] == 'video'
        assert result['source'] == 'youtube'
        assert result['duration_minutes'] == 16
        assert 'embedding' in result
    
    @patch('httpx.AsyncClient.get')
    async def test_process_youtube_content_not_found(self, mock_http, content_processor):
        """Test YouTube content processing with video not found"""
        # Mock YouTube API response with no items
        mock_response = Mock()
        mock_response.json.return_value = {'items': []}
        mock_response.raise_for_status.return_value = None
        mock_http.return_value.__aenter__.return_value.get.return_value = mock_response
        
        url = "https://www.youtube.com/watch?v=invalid_id"
        
        with pytest.raises(ContentProcessingError, match="Video not found"):
            await content_processor.process_youtube_content(url)
    
    @patch('httpx.AsyncClient.get')
    @patch('services.content_processing.openai.Embedding.acreate')
    async def test_process_arxiv_content_success(self, mock_openai, mock_http, content_processor, mock_openai_response):
        """Test successful arXiv content processing"""
        # Mock arXiv API XML response
        xml_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Paper Title</title>
                <summary>Test paper abstract content</summary>
                <author><name>Test Author</name></author>
                <category term="cs.AI"/>
                <link type="application/pdf" href="https://arxiv.org/pdf/2301.00001.pdf"/>
            </entry>
        </feed>'''
        
        mock_response = Mock()
        mock_response.content = xml_response.encode()
        mock_response.raise_for_status.return_value = None
        mock_http.return_value.__aenter__.return_value.get.return_value = mock_response
        
        # Mock OpenAI embedding
        mock_openai.return_value = mock_openai_response
        
        arxiv_id = "2301.00001"
        result = await content_processor.process_arxiv_content(arxiv_id)
        
        assert result['title'] == 'Test Paper Title'
        assert result['content_type'] == 'paper'
        assert result['source'] == 'arxiv'
        assert 'AI' in result['topics']
        assert 'embedding' in result

# Updated 2025-09-05: Comprehensive content processing tests