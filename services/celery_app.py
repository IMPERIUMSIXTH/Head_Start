"""
Celery Application Configuration
Background task processing for content ingestion

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Configure Celery for background content processing tasks
"""

from celery import Celery
import structlog
from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "headstart",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "services.tasks.content_tasks",
        "services.tasks.recommendation_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "services.tasks.content_tasks.*": {"queue": "content"},
    "services.tasks.recommendation_tasks.*": {"queue": "recommendations"},
}

# Updated 2025-09-05: Celery application configuration for background tasks