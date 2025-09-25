"""tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import os

from visio_to_xml.core.config import Config


def test_config_default_values():
    """test default configuration values."""
    # set required env var for test
    os.environ['MISTRAL_API_KEY'] = 'test_key'
    
    config = Config()
    
    assert config.mistral_api_key == 'test_key'
    assert config.mistral_api_url == 'https://api.mistral.ai/v1'
    assert config.default_output_format == 'drawio'
    assert config.max_image_size == 1024
    assert config.ocr_confidence_threshold == 0.8
    assert config.enable_debug_logging is False
    
    # cleanup
    del os.environ['MISTRAL_API_KEY']


def test_config_from_env():
    """test configuration from environment variables."""
    test_env = {
        'MISTRAL_API_KEY': 'custom_key',
        'MISTRAL_API_URL': 'https://custom.api.com',
        'DEFAULT_OUTPUT_FORMAT': 'mermaid',
        'MAX_IMAGE_SIZE': '2048',
        'OCR_CONFIDENCE_THRESHOLD': '0.9',
        'ENABLE_DEBUG_LOGGING': 'true'
    }
    
    # set env vars
    for key, value in test_env.items():
        os.environ[key] = value
    
    try:
        config = Config()
        
        assert config.mistral_api_key == 'custom_key'
        assert config.mistral_api_url == 'https://custom.api.com'
        assert config.default_output_format == 'mermaid'
        assert config.max_image_size == 2048
        assert config.ocr_confidence_threshold == 0.9
        assert config.enable_debug_logging is True
        
    finally:
        # cleanup
        for key in test_env:
            if key in os.environ:
                del os.environ[key]


def test_output_directory_creation():
    """test that output directory is created automatically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'test_output'
        
        os.environ['MISTRAL_API_KEY'] = 'test_key'
        os.environ['OUTPUT_DIRECTORY'] = str(output_dir)
        
        try:
            config = Config()
            assert config.output_directory.exists()
            assert config.output_directory.is_dir()
            
        finally:
            del os.environ['MISTRAL_API_KEY']
            del os.environ['OUTPUT_DIRECTORY']
