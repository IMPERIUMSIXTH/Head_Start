"""
Enhanced testing framework validation script
Validates all components of the enhanced unit testing framework

Author: HeadStart Development Team
Created: 2025-09-09
Purpose: Validate enhanced unit testing framework setup and functionality
"""

import pytest
import sys
import os
import importlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

class FrameworkValidator:
    """Validator for the enhanced testing framework"""
    
    def __init__(self):
        self.test_dir = Path("tests")
        self.validation_results = []
    
    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """Validate that all required dependencies are installed"""
        required_packages = [
            'pytest',
            'pytest-asyncio',
            'pytest-cov',
            'pytest-mock',
            'pytest-html',
            'pytest-json-report',
            'pytest-benchmark',
            'pytest-timeout',
            'pytest-rerunfailures',
            'hypothesis',
            'mutmut',
            'factory-boy',
            'faker'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                # Handle packages with hyphens
                import_name = package.replace('-', '_')
                importlib.import_module(import_name)
            except ImportError:
                try:
                    # Try alternative import names
                    if package == 'pytest-asyncio':
                        importlib.import_module('pytest_asyncio')
                    elif package == 'pytest-cov':
                        importlib.import_module('pytest_cov')
                    elif package == 'pytest-mock':
                        importlib.import_module('pytest_mock')
                    elif package == 'pytest-html':
                        importlib.import_module('pytest_html')
                    elif package == 'pytest-json-report':
                        importlib.import_module('pytest_jsonreport')
                    elif package == 'pytest-benchmark':
                        importlib.import_module('pytest_benchmark')
                    elif package == 'pytest-timeout':
                        importlib.import_module('pytest_timeout')
                    elif package == 'pytest-rerunfailures':
                        importlib.import_module('pytest_rerunfailures')
                    elif package == 'factory-boy':
                        importlib.import_module('factory')
                    else:
                        raise ImportError
                except ImportError:
                    missing_packages.append(package)
        
        success = len(missing_packages) == 0
        return success, missing_packages
    
    def validate_configuration_files(self) -> Tuple[bool, List[str]]:
        """Validate that configuration files exist and are properly formatted"""
        required_files = [
            'pytest.ini',
            'tests/conftest.py',
            'mutmut_config.py'
        ]
        
        missing_files = []
        
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        success = len(missing_files) == 0
        return success, missing_files
    
    def validate_test_structure(self) -> Tuple[bool, List[str]]:
        """Validate test directory structure"""
        required_test_files = [
            'tests/__init__.py',
            'tests/conftest.py',
            'tests/property_tests.py',
            'tests/async_tests.py',
            'tests/enhanced_unit_tests.py',
            'tests/mutation_testing.py',
            'tests/test_categorization.py',
            'tests/test_enhanced_framework_validation.py',
            'tests/fixtures/complex_fixtures.py'
        ]
        
        missing_files = []
        
        for file_path in required_test_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        success = len(missing_files) == 0
        return success, missing_files
    
    def validate_pytest_configuration(self) -> Tuple[bool, List[str]]:
        """Validate pytest configuration"""
        issues = []
        
        # Check pytest.ini exists and has required sections
        pytest_ini = Path('pytest.ini')
        if not pytest_ini.exists():
            issues.append("pytest.ini file not found")
            return False, issues
        
        try:
            with open(pytest_ini, 'r') as f:
                content = f.read()
            
            required_sections = [
                '[tool:pytest]',
                'addopts',
                'testpaths',
                'markers',
                'asyncio_mode'
            ]
            
            for section in required_sections:
                if section not in content:
                    issues.append(f"Missing section in pytest.ini: {section}")
            
            # Check for required markers
            required_markers = [
                'unit:', 'integration:', 'e2e:', 'slow:', 'security:',
                'performance:', 'smoke:', 'regression:', 'property:',
                'mutation:', 'asyncio:', 'celery:', 'auth:', 'content:',
                'api:', 'models:', 'fixtures:'
            ]
            
            for marker in required_markers:
                if marker not in content:
                    issues.append(f"Missing marker in pytest.ini: {marker}")
        
        except Exception as e:
            issues.append(f"Error reading pytest.ini: {e}")
        
        success = len(issues) == 0
        return success, issues
    
    def validate_fixtures(self) -> Tuple[bool, List[str]]:
        """Validate that fixtures are properly defined"""
        issues = []
        
        try:
            # Import conftest to check fixtures
            sys.path.insert(0, str(self.test_dir))
            import conftest
            
            required_fixtures = [
                'sample_user_factory',
                'content_factory',
                'mock_external_apis',
                'security_test_data',
                'learning_scenario_basic',
                'learning_scenario_advanced',
                'authentication_scenario_complex',
                'benchmark_config',
                'performance_test_data',
                'celery_app',
                'async_scenario_complex',
                'test_data_generators',
                'database_scenario_complex',
                'mutation_test_config'
            ]
            
            for fixture_name in required_fixtures:
                if not hasattr(conftest, fixture_name):
                    issues.append(f"Missing fixture: {fixture_name}")
        
        except ImportError as e:
            issues.append(f"Error importing conftest: {e}")
        except Exception as e:
            issues.append(f"Error validating fixtures: {e}")
        
        success = len(issues) == 0
        return success, issues
    
    def validate_test_categories(self) -> Tuple[bool, List[str]]:
        """Validate test categorization system"""
        issues = []
        
        try:
            # Run a simple pytest collection to check markers
            import subprocess
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                '--collect-only', '-q',
                str(self.test_dir)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                issues.append(f"Test collection failed: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            issues.append("Test collection timed out")
        except Exception as e:
            issues.append(f"Error validating test categories: {e}")
        
        success = len(issues) == 0
        return success, issues
    
    def validate_property_testing(self) -> Tuple[bool, List[str]]:
        """Validate property-based testing setup"""
        issues = []
        
        try:
            from hypothesis import given, strategies as st, settings
            
            # Test basic Hypothesis functionality
            @given(st.text())
            def test_hypothesis_works(text):
                assert isinstance(text, str)
            
            # Run a few examples to ensure it works
            test_hypothesis_works()
            
            # Check settings configuration
            current_settings = settings()
            if current_settings.max_examples < 10:
                issues.append("Hypothesis max_examples too low")
        
        except ImportError:
            issues.append("Hypothesis not properly installed")
        except Exception as e:
            issues.append(f"Error validating property testing: {e}")
        
        success = len(issues) == 0
        return success, issues
    
    def validate_async_testing(self) -> Tuple[bool, List[str]]:
        """Validate async testing setup"""
        issues = []
        
        try:
            import asyncio
            import pytest_asyncio
            
            # Test basic async functionality
            async def test_async_works():
                await asyncio.sleep(0.001)
                return True
            
            # Run the async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(test_async_works())
                if not result:
                    issues.append("Basic async test failed")
            finally:
                loop.close()
        
        except ImportError:
            issues.append("pytest-asyncio not properly installed")
        except Exception as e:
            issues.append(f"Error validating async testing: {e}")
        
        success = len(issues) == 0
        return success, issues
    
    def validate_mutation_testing(self) -> Tuple[bool, List[str]]:
        """Validate mutation testing setup"""
        issues = []
        
        try:
            import mutmut
            
            # Check mutmut configuration file
            config_file = Path('mutmut_config.py')
            if not config_file.exists():
                issues.append("mutmut_config.py not found")
            else:
                # Try to import the config
                sys.path.insert(0, '.')
                import mutmut_config
                
                required_functions = ['pre_mutation', 'post_mutation']
                for func in required_functions:
                    if not hasattr(mutmut_config, func):
                        issues.append(f"Missing function in mutmut_config.py: {func}")
        
        except ImportError:
            issues.append("mutmut not properly installed")
        except Exception as e:
            issues.append(f"Error validating mutation testing: {e}")
        
        success = len(issues) == 0
        return success, issues
    
    def run_sample_tests(self) -> Tuple[bool, List[str]]:
        """Run a sample of tests to ensure they work"""
        issues = []
        
        try:
            import subprocess
            
            # Run a small subset of tests
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                str(self.test_dir / 'test_categorization.py::TestCategorization::test_unit_marker_functionality'),
                '-v'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                issues.append(f"Sample test failed: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            issues.append("Sample test timed out")
        except Exception as e:
            issues.append(f"Error running sample tests: {e}")
        
        success = len(issues) == 0
        return success, issues
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validations and return comprehensive report"""
        validations = [
            ("Dependencies", self.validate_dependencies),
            ("Configuration Files", self.validate_configuration_files),
            ("Test Structure", self.validate_test_structure),
            ("Pytest Configuration", self.validate_pytest_configuration),
            ("Fixtures", self.validate_fixtures),
            ("Test Categories", self.validate_test_categories),
            ("Property Testing", self.validate_property_testing),
            ("Async Testing", self.validate_async_testing),
            ("Mutation Testing", self.validate_mutation_testing),
            ("Sample Tests", self.run_sample_tests)
        ]
        
        results = {}
        overall_success = True
        
        for name, validation_func in validations:
            try:
                success, issues = validation_func()
                results[name] = {
                    'success': success,
                    'issues': issues
                }
                if not success:
                    overall_success = False
            except Exception as e:
                results[name] = {
                    'success': False,
                    'issues': [f"Validation error: {e}"]
                }
                overall_success = False
        
        return {
            'overall_success': overall_success,
            'validations': results,
            'summary': self._generate_summary(results)
        }
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of validation results"""
        total_validations = len(results)
        successful_validations = sum(1 for r in results.values() if r['success'])
        total_issues = sum(len(r['issues']) for r in results.values())
        
        return {
            'total_validations': total_validations,
            'successful_validations': successful_validations,
            'failed_validations': total_validations - successful_validations,
            'total_issues': total_issues,
            'success_rate': (successful_validations / total_validations) * 100 if total_validations > 0 else 0
        }

def main():
    """Main function for command-line usage"""
    print("Enhanced Testing Framework Validation")
    print("=" * 50)
    
    validator = FrameworkValidator()
    results = validator.validate_all()
    
    # Print results
    for validation_name, validation_result in results['validations'].items():
        status = "✓ PASS" if validation_result['success'] else "✗ FAIL"
        print(f"{validation_name}: {status}")
        
        if validation_result['issues']:
            for issue in validation_result['issues']:
                print(f"  - {issue}")
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    summary = results['summary']
    print(f"Total Validations: {summary['total_validations']}")
    print(f"Successful: {summary['successful_validations']}")
    print(f"Failed: {summary['failed_validations']}")
    print(f"Total Issues: {summary['total_issues']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    
    overall_status = "✓ FRAMEWORK READY" if results['overall_success'] else "✗ FRAMEWORK NEEDS ATTENTION"
    print(f"\nOverall Status: {overall_status}")
    
    if results['overall_success']:
        print("\nThe enhanced testing framework is properly configured and ready to use!")
        print("\nNext steps:")
        print("1. Run unit tests: python -m pytest tests/ -m unit")
        print("2. Run property tests: python -m pytest tests/ -m property")
        print("3. Run async tests: python -m pytest tests/ -m asyncio")
        print("4. Run comprehensive suite: python tests/run_enhanced_tests.py --test-type all")
    else:
        print("\nPlease address the issues above before using the framework.")
    
    return 0 if results['overall_success'] else 1

if __name__ == "__main__":
    sys.exit(main())