"""
Mutation testing configuration for mutmut
Defines mutation testing settings and exclusions

Author: HeadStart Development Team
Created: 2025-09-08
Purpose: Mutation testing configuration for test quality validation
"""

def pre_mutation(context):
    """
    Pre-mutation hook to filter out mutations we don't want to test
    """
    # Skip mutations in test files themselves
    if 'test_' in context.filename or '_test.py' in context.filename:
        return False
    
    # Skip mutations in configuration files
    if 'config' in context.filename.lower():
        return False
    
    # Skip mutations in migration files
    if 'alembic' in context.filename.lower() or 'migration' in context.filename.lower():
        return False
    
    # Skip mutations in __init__.py files (usually just imports)
    if context.filename.endswith('__init__.py'):
        return False
    
    # Skip mutations in specific lines that shouldn't be mutated
    line = context.current_source_line.strip()
    
    # Skip import statements
    if line.startswith('import ') or line.startswith('from '):
        return False
    
    # Skip logger definitions
    if 'logger' in line and ('getLogger' in line or 'Logger' in line):
        return False
    
    # Skip version strings and constants
    if line.startswith('__version__') or line.startswith('VERSION'):
        return False
    
    # Skip docstrings (triple quotes)
    if '"""' in line or "'''" in line:
        return False
    
    return True

def post_mutation(context):
    """
    Post-mutation hook to perform additional checks after mutation
    """
    return True

# Mutation testing settings
MUTMUT_SETTINGS = {
    # Paths to include in mutation testing
    'paths_to_mutate': [
        'services/',
        'api/',
    ],
    
    # Paths to exclude from mutation testing
    'paths_to_exclude': [
        'tests/',
        'alembic/',
        'scripts/',
        '__pycache__/',
        '.venv/',
        '.git/',
    ],
    
    # Test command to run for each mutation
    'test_command': 'python -m pytest tests/unit/ tests/test_authentication.py tests/test_content_processing.py -x --tb=no -q',
    
    # Timeout for each test run (in seconds)
    'test_timeout': 60,
    
    # Minimum test coverage required
    'coverage_threshold': 80,
    
    # Types of mutations to apply
    'mutation_types': [
        'string',      # String literal mutations
        'number',      # Number literal mutations
        'operator',    # Operator mutations (==, !=, <, >, etc.)
        'keyword',     # Keyword mutations (and, or, not, etc.)
        'exception',   # Exception handling mutations
    ],
    
    # Specific mutations to skip
    'skip_mutations': [
        # Skip mutations that would break imports
        'import',
        # Skip mutations in logging statements
        'logging',
        # Skip mutations in version checks
        'version',
    ]
}

# Custom mutation operators
CUSTOM_MUTATIONS = {
    # Authentication-specific mutations
    'auth_mutations': {
        'verify_password': [
            # Test what happens if password verification always returns True/False
            ('return True', 'return False'),
            ('return False', 'return True'),
        ],
        'hash_password': [
            # Test what happens if password hashing is bypassed
            ('return hashed_password', 'return password'),
        ],
    },
    
    # Security-specific mutations
    'security_mutations': {
        'detect_sql_injection': [
            # Test what happens if SQL injection detection is disabled
            ('return True', 'return False'),
            ('return False', 'return True'),
        ],
        'detect_xss_attempt': [
            # Test what happens if XSS detection is disabled
            ('return True', 'return False'),
            ('return False', 'return True'),
        ],
    },
    
    # Validation-specific mutations
    'validation_mutations': {
        'validate_email': [
            # Test what happens if email validation always passes/fails
            ('return True', 'return False'),
            ('return False', 'return True'),
        ],
        'validate_password_strength': [
            # Test what happens if password strength validation is bypassed
            ('score >= 5', 'score >= 0'),
            ('len(password) >= 8', 'len(password) >= 0'),
        ],
    }
}

# Mutation testing quality gates
QUALITY_GATES = {
    # Minimum mutation score (percentage of mutations that cause test failures)
    'min_mutation_score': 75,
    
    # Critical functions that must have high mutation scores
    'critical_functions': {
        'services.auth.hash_password': 90,
        'services.auth.verify_password': 90,
        'services.security.detect_sql_injection': 85,
        'services.security.detect_xss_attempt': 85,
        'services.auth.create_access_token': 80,
        'services.auth.verify_token': 80,
    },
    
    # Functions that can have lower mutation scores (less critical)
    'non_critical_functions': {
        'services.content_processing.extract_youtube_id': 60,
        'services.content_processing._parse_youtube_duration': 60,
    }
}

# Reporting configuration
REPORTING_CONFIG = {
    'output_format': 'html',
    'output_file': 'mutation_report.html',
    'include_source': True,
    'show_mutants': True,
    'show_times': True,
}

def get_mutation_config():
    """Get the complete mutation testing configuration"""
    return {
        'settings': MUTMUT_SETTINGS,
        'custom_mutations': CUSTOM_MUTATIONS,
        'quality_gates': QUALITY_GATES,
        'reporting': REPORTING_CONFIG,
    }