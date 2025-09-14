"""
Enhanced unit testing framework
Provides comprehensive testing capabilities including property-based testing,
async patterns, mutation testing, and advanced fixtures

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Enhanced unit testing framework initialization
"""

__version__ = "1.0.0"
__author__ = "HeadStart Development Team"

# Import key testing utilities for easy access
from .run_enhanced_tests import EnhancedTestRunner
from .validate_framework import FrameworkValidator

__all__ = [
    'EnhancedTestRunner',
    'FrameworkValidator'
]