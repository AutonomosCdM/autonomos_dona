"""Test to verify CI environment is properly configured."""

import os
import sys
import pytest


class TestCIEnvironment:
    """Tests to ensure CI environment is properly set up."""
    
    def test_python_version(self):
        """Test Python version is supported."""
        version = sys.version_info
        assert version.major == 3
        assert version.minor in [9, 10, 11]
    
    def test_environment_variables(self):
        """Test required environment variables are set."""
        required_vars = [
            'SLACK_BOT_TOKEN',
            'SLACK_APP_TOKEN', 
            'SLACK_SIGNING_SECRET',
            'SUPABASE_URL',
            'SUPABASE_KEY'
        ]
        
        for var in required_vars:
            assert os.getenv(var) is not None, f"Environment variable {var} is not set"
    
    def test_imports(self):
        """Test that all main modules can be imported."""
        try:
            import src
            import src.handlers.commands
            import src.handlers.events
            import src.services.slack_client
            import src.services.supabase_client
            import src.models.schemas
            import src.utils.config
        except ImportError as e:
            pytest.fail(f"Failed to import module: {e}")
    
    def test_dependencies(self):
        """Test that all required dependencies are installed."""
        required_packages = [
            'slack_bolt',
            'slack_sdk',
            'supabase',
            'pydantic',
            'dotenv',
            'pytest'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                pytest.fail(f"Required package '{package}' is not installed")