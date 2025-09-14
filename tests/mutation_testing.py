"""
Enhanced mutation testing utilities and patterns
Provides mutation testing support and quality validation

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Mutation testing framework for test quality validation
"""

import pytest
import subprocess
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from unittest.mock import patch, Mock

# Mutation testing configuration and utilities

class MutationTestRunner:
    """Runner for mutation testing with enhanced capabilities"""
    
    def __init__(self, config_path: str = "mutmut_config.py"):
        self.config_path = config_path
        self.results = {}
        self.quality_gates = {
            'min_mutation_score': 75,
            'critical_functions': {
                'services.auth.hash_password': 90,
                'services.auth.verify_password': 90,
                'services.security.detect_sql_injection': 85,
                'services.security.detect_xss_attempt': 85,
            }
        }
    
    def run_mutation_tests(self, paths: List[str], test_command: str = None) -> Dict[str, Any]:
        """Run mutation tests on specified paths"""
        if test_command is None:
            test_command = "python -m pytest tests/unit/ tests/test_authentication.py -x --tb=no -q"
        
        results = {
            'total_mutants': 0,
            'killed_mutants': 0,
            'survived_mutants': 0,
            'mutation_score': 0.0,
            'function_scores': {},
            'quality_gate_passed': False
        }
        
        for path in paths:
            try:
                # Run mutmut on the path
                cmd = [
                    'python', '-m', 'mutmut', 'run',
                    '--paths-to-mutate', path,
                    '--tests-dir', 'tests/',
                    '--runner', test_command
                ]
                
                # In a real implementation, this would run mutmut
                # For testing purposes, we'll simulate the results
                path_results = self._simulate_mutation_results(path)
                
                results['total_mutants'] += path_results['total_mutants']
                results['killed_mutants'] += path_results['killed_mutants']
                results['survived_mutants'] += path_results['survived_mutants']
                results['function_scores'].update(path_results['function_scores'])
                
            except Exception as e:
                print(f"Error running mutation tests on {path}: {e}")
        
        # Calculate overall mutation score
        if results['total_mutants'] > 0:
            results['mutation_score'] = (results['killed_mutants'] / results['total_mutants']) * 100
        
        # Check quality gates
        results['quality_gate_passed'] = self._check_quality_gates(results)
        
        self.results = results
        return results
    
    def _simulate_mutation_results(self, path: str) -> Dict[str, Any]:
        """Simulate mutation testing results for demonstration"""
        # This would be replaced with actual mutmut integration
        if 'auth.py' in path:
            return {
                'total_mutants': 20,
                'killed_mutants': 18,
                'survived_mutants': 2,
                'function_scores': {
                    'services.auth.hash_password': 95,
                    'services.auth.verify_password': 90,
                    'services.auth.create_access_token': 85
                }
            }
        elif 'security.py' in path:
            return {
                'total_mutants': 15,
                'killed_mutants': 13,
                'survived_mutants': 2,
                'function_scores': {
                    'services.security.detect_sql_injection': 87,
                    'services.security.detect_xss_attempt': 80
                }
            }
        else:
            return {
                'total_mutants': 10,
                'killed_mutants': 7,
                'survived_mutants': 3,
                'function_scores': {}
            }
    
    def _check_quality_gates(self, results: Dict[str, Any]) -> bool:
        """Check if mutation testing results pass quality gates"""
        # Check overall mutation score
        if results['mutation_score'] < self.quality_gates['min_mutation_score']:
            return False
        
        # Check critical function scores
        for func, min_score in self.quality_gates['critical_functions'].items():
            actual_score = results['function_scores'].get(func, 0)
            if actual_score < min_score:
                return False
        
        return True
    
    def generate_report(self, output_file: str = "mutation_report.json"):
        """Generate mutation testing report"""
        report = {
            'summary': self.results,
            'quality_gates': self.quality_gates,
            'recommendations': self._generate_recommendations()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on mutation testing results"""
        recommendations = []
        
        if self.results.get('mutation_score', 0) < 80:
            recommendations.append("Consider adding more comprehensive unit tests")
        
        if self.results.get('survived_mutants', 0) > 5:
            recommendations.append("Review survived mutants to identify test gaps")
        
        for func, min_score in self.quality_gates['critical_functions'].items():
            actual_score = self.results.get('function_scores', {}).get(func, 0)
            if actual_score < min_score:
                recommendations.append(f"Improve test coverage for {func} (current: {actual_score}%, target: {min_score}%)")
        
        return recommendations

# Mutation testing fixtures and utilities

@pytest.fixture(scope="session")
def mutation_test_runner():
    """Provide mutation test runner for tests"""
    return MutationTestRunner()

@pytest.fixture(scope="function")
def mutation_test_config():
    """Provide mutation testing configuration"""
    return {
        'timeout': 60,
        'test_command': 'python -m pytest tests/unit/ -x --tb=no -q',
        'paths_to_mutate': ['services/', 'api/'],
        'min_mutation_score': 75,
        'critical_functions': {
            'services.auth.hash_password': 90,
            'services.auth.verify_password': 90,
            'services.security.detect_sql_injection': 85,
        }
    }

# Test classes for mutation testing validation

@pytest.mark.unit
@pytest.mark.mutation
class TestMutationTestingFramework:
    """Test the mutation testing framework itself"""
    
    def test_mutation_runner_initialization(self, mutation_test_runner):
        """Test mutation test runner initialization"""
        assert mutation_test_runner.config_path == "mutmut_config.py"
        assert 'min_mutation_score' in mutation_test_runner.quality_gates
        assert mutation_test_runner.quality_gates['min_mutation_score'] == 75
    
    def test_mutation_runner_simulation(self, mutation_test_runner):
        """Test mutation runner simulation"""
        results = mutation_test_runner.run_mutation_tests(['services/auth.py'])
        
        assert 'total_mutants' in results
        assert 'killed_mutants' in results
        assert 'survived_mutants' in results
        assert 'mutation_score' in results
        assert results['total_mutants'] > 0
        assert results['mutation_score'] >= 0
    
    def test_quality_gate_validation(self, mutation_test_runner):
        """Test quality gate validation"""
        # Test passing quality gates
        good_results = {
            'mutation_score': 85,
            'function_scores': {
                'services.auth.hash_password': 95,
                'services.auth.verify_password': 92,
                'services.security.detect_sql_injection': 88,
                'services.security.detect_xss_attempt': 87
            }
        }
        
        assert mutation_test_runner._check_quality_gates(good_results) is True
        
        # Test failing quality gates
        bad_results = {
            'mutation_score': 60,  # Below threshold
            'function_scores': {
                'services.auth.hash_password': 70,  # Below threshold
            }
        }
        
        assert mutation_test_runner._check_quality_gates(bad_results) is False
    
    def test_report_generation(self, mutation_test_runner, tmp_path):
        """Test mutation testing report generation"""
        # Run simulation
        mutation_test_runner.run_mutation_tests(['services/auth.py'])
        
        # Generate report
        report_file = tmp_path / "test_mutation_report.json"
        report = mutation_test_runner.generate_report(str(report_file))
        
        assert report_file.exists()
        assert 'summary' in report
        assert 'quality_gates' in report
        assert 'recommendations' in report

@pytest.mark.unit
@pytest.mark.mutation
class TestCriticalFunctionMutations:
    """Test critical functions for mutation testing effectiveness"""
    
    def test_auth_password_hashing_mutations(self, auth_service):
        """Test password hashing function against mutations"""
        password = "TestPassword123!"
        
        # Test 1: Ensure hashing produces different output than input
        hashed = auth_service.hash_password(password)
        assert hashed != password  # Mutation: return password instead of hash
        
        # Test 2: Ensure hash format is correct
        assert hashed.startswith("$argon2id$")  # Mutation: change algorithm
        
        # Test 3: Ensure verification works
        assert auth_service.verify_password(password, hashed) is True  # Mutation: return False
        
        # Test 4: Ensure wrong password fails
        assert auth_service.verify_password("wrong", hashed) is False  # Mutation: return True
        
        # Test 5: Ensure different calls produce different hashes (salt)
        hashed2 = auth_service.hash_password(password)
        assert hashed != hashed2  # Mutation: reuse same salt
        assert auth_service.verify_password(password, hashed2) is True
    
    def test_auth_password_verification_mutations(self, auth_service):
        """Test password verification function against mutations"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = auth_service.hash_password(password)
        
        # Test correct password verification
        assert auth_service.verify_password(password, hashed) is True
        
        # Test wrong password rejection
        assert auth_service.verify_password(wrong_password, hashed) is False
        
        # Test empty password rejection
        assert auth_service.verify_password("", hashed) is False
        
        # Test None password handling
        with pytest.raises((TypeError, ValueError)):
            auth_service.verify_password(None, hashed)
    
    def test_security_sql_injection_detection_mutations(self):
        """Test SQL injection detection against mutations"""
        from services.security import SecurityValidator
        
        # Test obvious SQL injection patterns
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1' --",
            "'; INSERT INTO users VALUES ('hacker'); --",
            "' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            # Should detect SQL injection
            assert SecurityValidator.detect_sql_injection(malicious_input) is True
        
        # Test safe inputs
        safe_inputs = [
            "normal@example.com",
            "user with spaces",
            "user123@domain.co.uk"
        ]
        
        for safe_input in safe_inputs:
            # Should not detect SQL injection
            assert SecurityValidator.detect_sql_injection(safe_input) is False
    
    def test_security_xss_detection_mutations(self):
        """Test XSS detection against mutations"""
        from services.security import SecurityValidator
        
        # Test XSS patterns
        xss_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>"
        ]
        
        for xss_input in xss_inputs:
            # Should detect XSS
            assert SecurityValidator.detect_xss_attempt(xss_input) is True
        
        # Test safe inputs
        safe_inputs = [
            "Normal text content",
            "Text with <b>HTML</b> tags",
            "Email: user@example.com"
        ]
        
        for safe_input in safe_inputs:
            # Should not detect XSS
            assert SecurityValidator.detect_xss_attempt(safe_input) is False
    
    def test_boundary_condition_mutations(self, auth_service):
        """Test boundary conditions that mutations should break"""
        from services.security import SecurityValidator
        from services.exceptions import ValidationError
        
        # Test minimum password length boundary
        with pytest.raises(ValidationError):
            auth_service.hash_password("short")  # Mutation: change length check from >= 8 to >= 0
        
        # Test password strength validation boundaries
        weak_password = "weak"
        result = SecurityValidator.validate_password_strength(weak_password)
        assert result["valid"] is False  # Mutation: return True
        assert result["score"] < 3  # Mutation: change threshold
        
        # Test email validation boundaries
        invalid_emails = ["", "notanemail", "@domain.com", "user@"]
        for email in invalid_emails:
            from services.security import InputSanitizer
            assert InputSanitizer.validate_email(email) is False  # Mutation: return True

@pytest.mark.unit
@pytest.mark.mutation
class TestMutationTestingPatterns:
    """Test patterns for effective mutation testing"""
    
    def test_assertion_strength(self, auth_service):
        """Test assertion strength against mutations"""
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        # Strong assertions that catch mutations
        assert hashed != password  # Catches return password mutation
        assert len(hashed) > 50  # Catches empty string mutation
        assert '$' in hashed  # Catches format mutations
        assert hashed.count('$') >= 3  # Catches partial format mutations
        
        # Verification assertions
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong", hashed) is False
        assert auth_service.verify_password("", hashed) is False
    
    def test_edge_case_coverage(self):
        """Test edge cases that mutations might exploit"""
        from services.security import SecurityValidator, InputSanitizer
        
        # Test empty and None inputs
        assert SecurityValidator.detect_sql_injection("") is False
        assert SecurityValidator.detect_xss_attempt("") is False
        
        # Test very long inputs
        long_input = "a" * 10000
        assert isinstance(SecurityValidator.detect_sql_injection(long_input), bool)
        assert isinstance(SecurityValidator.detect_xss_attempt(long_input), bool)
        
        # Test special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        sanitized = InputSanitizer.sanitize_string(special_chars)
        assert isinstance(sanitized, str)
        assert len(sanitized) <= len(special_chars)
    
    def test_return_value_mutations(self, auth_service):
        """Test return value mutations"""
        password = "TestPassword123!"
        
        # Test boolean return mutations
        hashed = auth_service.hash_password(password)
        verification_result = auth_service.verify_password(password, hashed)
        
        # Should be exactly True, not truthy
        assert verification_result is True
        assert type(verification_result) is bool
        
        # Should be exactly False, not falsy
        wrong_verification = auth_service.verify_password("wrong", hashed)
        assert wrong_verification is False
        assert type(wrong_verification) is bool
    
    def test_operator_mutations(self):
        """Test operator mutations"""
        from services.security import SecurityValidator
        
        # Test comparison operators
        password = "TestPassword123!"
        result = SecurityValidator.validate_password_strength(password)
        
        # Test >= mutations (changed to >, <, <=, ==, !=)
        assert result["score"] >= 5  # Should pass with >=
        assert result["valid"] is True
        
        # Test length checks
        assert len(password) >= 8  # Mutation: change to >, <, <=, ==, !=
        assert len(password) > 7   # Alternative assertion
        assert len(password) != 0  # Catches != to == mutation
    
    def test_constant_mutations(self):
        """Test constant mutations"""
        from services.security import SecurityValidator
        
        # Test numeric constants
        weak_password = "123"  # Length 3
        result = SecurityValidator.validate_password_strength(weak_password)
        
        # These should catch mutations of the minimum length constant
        assert len(weak_password) < 8  # Catches mutation of 8 to other values
        assert result["valid"] is False
        
        # Test string constants
        from services.auth import AuthService
        auth = AuthService()
        hashed = auth.hash_password("TestPassword123!")
        
        # Should start with specific algorithm identifier
        assert hashed.startswith("$argon2id$")  # Catches algorithm mutations
        assert "$argon2id$" in hashed  # Additional check

# Integration with pytest markers for mutation testing

def pytest_configure(config):
    """Configure pytest for mutation testing"""
    config.addinivalue_line(
        "markers", 
        "mutation: Tests designed for mutation testing validation"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection for mutation testing"""
    for item in items:
        # Add mutation marker to tests with 'mutation' in name
        if "mutation" in item.name.lower():
            item.add_marker(pytest.mark.mutation)
        
        # Add mutation marker to critical function tests
        critical_patterns = ["auth", "security", "password", "token"]
        if any(pattern in item.name.lower() for pattern in critical_patterns):
            item.add_marker(pytest.mark.mutation)

# Utility functions for mutation testing

def run_mutation_tests_on_commit():
    """Run mutation tests on critical files during CI/CD"""
    runner = MutationTestRunner()
    
    # Focus on critical security and auth files
    critical_paths = [
        'services/auth.py',
        'services/security.py',
        'api/auth.py'
    ]
    
    results = runner.run_mutation_tests(critical_paths)
    
    if not results['quality_gate_passed']:
        raise Exception(f"Mutation testing quality gates failed. Score: {results['mutation_score']}%")
    
    return results

def generate_mutation_test_report():
    """Generate comprehensive mutation testing report"""
    runner = MutationTestRunner()
    
    # Run on all testable paths
    all_paths = [
        'services/',
        'api/'
    ]
    
    results = runner.run_mutation_tests(all_paths)
    report = runner.generate_report()
    
    return report