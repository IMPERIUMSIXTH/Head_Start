"""
AI Client Service
OpenAI integration for LLM and embeddings

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Handle OpenAI API calls for gpt-4o-mini and text-embedding-3-small models
"""

import structlog
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

class AIClient:
    """OpenAI client wrapper for LLM and embeddings"""

    def __init__(self):
        if not settings.OPENAI_API_KEY or not settings.GPT_API_KEY:
            logger.warning("OpenAI API keys not configured, AI features will be disabled")
            self.client = None
            self.gpt_client = None
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.gpt_client = OpenAI(api_key=settings.GPT_API_KEY)
        self.llm_model = "gpt-4o-mini"
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 1536

    async def get_relevance_score(self, user_prompt: str, content_description: str) -> float:
        """
        Get relevance score for a user and content item using the new GPT API.
        """
        if self.gpt_client is None:
            return 0.0
        try:
            system_message = """You are a relevance scoring assistant.
            Given a user's interest and a content description, provide a relevance score from 0.0 to 1.0.
            Only output a single floating point number.
            """

            prompt = f"User interest: {user_prompt}\n\nContent description: {content_description}"

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]

            response = self.gpt_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=10,
                temperature=0.2
            )

            score_text = response.choices[0].message.content.strip()
            score = float(score_text)

            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.error("Failed to get relevance score", error=str(e))
            return 0.0

    async def generate_explanation(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Generate personalized explanation using gpt-4o-mini

        Args:
            prompt: The explanation request
            context: Additional context for the explanation

        Returns:
            Generated explanation text
        """
        if self.client is None:
            return "AI not configured"
        try:
            system_message = """You are a learning assistant providing personalized explanations.
            Be clear, concise, and adapt your language to the learner's level.
            Focus on practical understanding and real-world applications."""

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]

            if context:
                context_str = f"Context: {context}"
                messages.insert(1, {"role": "user", "content": context_str})

            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            explanation = response.choices[0].message.content.strip()
            logger.info("Generated explanation", prompt_length=len(prompt))

            return explanation

        except Exception as e:
            logger.error("Failed to generate explanation", error=str(e))
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate semantic embedding using text-embedding-3-small

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if self.client is None:
            raise ValueError("AI not configured")
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")

            # Truncate text if too long (OpenAI has token limits)
            text = text[:8000]  # Conservative limit

            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            embedding = response.data[0].embedding

            if len(embedding) != self.embedding_dimensions:
                raise ValueError(f"Unexpected embedding dimensions: {len(embedding)}")

            logger.info("Generated embedding", text_length=len(text))
            return embedding

        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            raise

    async def generate_multiple_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self.client is None:
            return []
        try:
            if not texts:
                return []

            # Filter out empty texts
            valid_texts = [text for text in texts if text and text.strip()]

            if not valid_texts:
                return []

            # Truncate texts if needed
            valid_texts = [text[:8000] for text in valid_texts]

            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=valid_texts
            )

            embeddings = [data.embedding for data in response.data]

            logger.info("Generated multiple embeddings", count=len(embeddings))
            return embeddings

        except Exception as e:
            logger.error("Failed to generate multiple embeddings", error=str(e))
            raise

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        try:
            import numpy as np

            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, similarity))

        except Exception as e:
            logger.error("Failed to calculate similarity", error=str(e))
            return 0.0

# Global AI client instance
_ai_client = None

def get_ai_client() -> AIClient:
    """Get AI client instance (singleton)"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client

# Updated 2025-09-09: OpenAI integration service with gpt-4o-mini and text-embedding-3-small
