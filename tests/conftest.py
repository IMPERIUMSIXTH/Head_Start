"""
Enhanced pytest configuration and fixtures
Provides advanced testing capabilities including property-based testing,
async patterns, and complex test scenarios

Author: HeadStart Development Team
Created: 2025-09-08
Purpose: Enhanced testing framework configuration
"""

import pytest
import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from hypothesis import settings, Verbosity
from celery import Celery

from services.database import Base, get_db
from services.models import User, ContentItem, UserPreferences
from services.auth import AuthService
from services.content_processing import ContentProcessor
from main import app

# Configure Hypothesis for property-based testing
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=1000, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=10, verbosity=Verbosity.quiet)

# Load profile based on environment
profile = os.getenv("HYPOTHESIS_PROFILE", "default")
settings.load_profile(profile)

# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio