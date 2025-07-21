"""Test configuration and fixtures."""

import json
from unittest.mock import MagicMock, patch

import pytest

# Test data for additional bots
TEST_ADDITIONAL_BOTS = {"test_bot": ["192.0.2.0/24", "203.0.113.0/24"]}


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for testing."""
    with patch('requests.get') as mock_get:
        # Set up a default response
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_importlib_resources():
    """Mock importlib.resources.files for testing."""
    mock_file = MagicMock()
    mock_file.read_text.return_value = json.dumps(TEST_ADDITIONAL_BOTS)

    with patch('good_bots.core.files') as mock_files:
        mock_files.return_value.__truediv__.return_value = mock_file
        yield mock_files


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    return tmp_path


@pytest.fixture
def sample_endpoints_data():
    """Sample endpoints data for testing."""
    return {
        "data": [
            {
                "source": {
                    "id": "test-bot",
                    "type": "search",
                    "url": "https://example.com/test.json",
                }
            }
        ]
    }


@pytest.fixture
def sample_bot_data():
    """Sample bot IP data for testing."""
    return {
        "prefixes": [{"ipv4Prefix": "192.0.2.0/24"}, {"ipv4Prefix": "203.0.113.0/24"}]
    }
