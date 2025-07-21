"""Unit tests for core functionality."""

import unittest
from unittest.mock import MagicMock, patch

from good_bots import core


def test_cidr_to_range():
    """Test CIDR to IP range conversion."""
    # Test valid IPv4 CIDR
    assert core.cidr_to_range("192.0.2.0/24") == "192.0.2.0-192.0.2.255"
    # Test valid IPv4 single IP
    assert core.cidr_to_range("192.0.2.1/32") == "192.0.2.1-192.0.2.1"
    # Test invalid CIDR
    assert core.cidr_to_range("invalid") is None


def test_extract_ipv4_addresses(capsys):
    """Test extraction of IPv4 addresses from data."""
    # Test with valid IPv4 and invalid entries
    test_data = {
        "prefixes": [
            {"ipv4Prefix": "192.0.2.0/24"},  # Valid IPv4
            {"ipv4Prefix": "2001:db8::/32"},  # Invalid IPv6
            {"invalid": "not_an_ip"},  # Missing ipv4Prefix
            "not_a_dict",  # Invalid entry type
        ]
    }

    # Call the function
    result = core.extract_ipv4_addresses(test_data)

    # Verify the result contains the expected IP range
    assert isinstance(result, list)
    assert "192.0.2.0-192.0.2.255" in result
    assert len(result) == 1  # Only one valid IPv4 range should be returned

    # Verify warnings were printed for invalid entries
    captured = capsys.readouterr()
    assert (
        "Invalid CIDR 2001:db8::/32: Expected 4 octets in '2001:db8::'" in captured.err
    )
    assert "Warning: Invalid prefix entry in API response" in captured.err

    # Test with no IPv4 addresses
    with patch('ipaddress.ip_network') as mock_ip_network:
        mock_ip_network.side_effect = [
            ValueError("Invalid IPv6 address"),
            ValueError("Invalid address"),
        ]
        data = {"prefixes": ["2001:db8::/32", "not_an_ip"]}
        result = core.extract_ipv4_addresses(data)
        assert result == []


@patch('good_bots.core.requests.get')
def test_fetch_json_success(mock_get):
    """Test successful JSON fetch."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"test": "data"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = core.fetch_json("https://example.com/api")
    assert result == {"test": "data"}
    mock_get.assert_called_once_with("https://example.com/api", timeout=30, verify=True)


@patch('good_bots.core.requests.get')
def test_fetch_json_failure(mock_get, capsys):
    """Test failed JSON fetch."""
    # Mock the request to raise a RequestException
    from requests.exceptions import RequestException

    mock_get.side_effect = RequestException("Connection error")

    # Call the function
    result = core.fetch_json("https://example.com/api")

    # Verify the function returns None on error
    assert result is None

    # Verify the error was logged to stderr
    captured = capsys.readouterr()
    assert "Error fetching https://example.com/api: Connection error" in captured.err

    # Verify the request was made with correct parameters
    mock_get.assert_called_once_with("https://example.com/api", timeout=30, verify=True)


@patch('good_bots.core.fetch_json')
@patch('good_bots.core.load_additional_bots')
@patch('builtins.open', new_callable=unittest.mock.mock_open)
@patch('os.path.basename')
@patch('os.path.splitext')
def test_generate_bot_ips(
    mock_splitext,
    mock_basename,
    mock_open,
    mock_load_additional,
    mock_fetch,
    tmp_path,
    capsys,
):
    """Test the main bot IP generation function."""
    # Setup mock responses
    mock_basename.return_value = 'bot_ips_config.py'
    mock_splitext.return_value = ('bot_ips_config', '.py')

    # Mock the main endpoint response
    mock_fetch.side_effect = [
        {
            'data': [
                {
                    'source': {
                        'id': 'test',
                        'type': 'bot',
                        'url': 'https://example.com/bots.json',
                    }
                }
            ]
        },
        {'prefixes': [{'ipv4Prefix': '192.0.2.0/24'}]},
    ]

    # Mock the additional bots
    mock_load_additional.return_value = {'test_bot': ['192.0.2.0/24']}

    # Create a mock file handle for the output file
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    # Create a temporary output file path
    output_file = tmp_path / "bot_ips_config.py"

    # Call the function
    result = core.generate_bot_ips(str(output_file))

    # Verify the result
    assert result == 0

    # Verify the file was opened for writing (convert Path to string for comparison)
    mock_open.assert_called_once_with(str(output_file), 'w')

    # Verify the file was written to
    assert mock_file.write.called, "No data was written to the output file"

    # Get the content that was written to the file
    written_content = "".join([call[0][0] for call in mock_file.write.call_args_list])

    # Verify the content
    assert "GOOD_BOTS = [" in written_content
    assert "192.0.2.0-192.0.2.255" in written_content

    # Verify the output messages
    captured = capsys.readouterr()
    assert "Fetching endpoint list" in captured.out
    assert "Generated " in captured.out


@patch('good_bots.core.generate_bot_ips')
def test_main_flow(mock_generate, capsys):
    """Test the main flow from CLI to file generation."""
    # Setup mock for generate_bot_ips
    mock_generate.return_value = 0

    # Import the main function
    from good_bots import __main__

    # Call the main function
    with patch('sys.argv', ['good_bots']):
        __main__.main()

    # Verify generate_bot_ips was called with the default output path
    mock_generate.assert_called_once_with('bot_ips_config.py')

    # Verify the output messages
    captured = capsys.readouterr()
    assert "Generating bot IP configuration..." in captured.out
    assert "Configuration generated successfully" in captured.out


@patch('good_bots.core.generate_bot_ips')
def test_main_flow_with_custom_path(mock_generate, tmp_path, capsys):
    """Test the main flow with a custom output path."""
    # Setup mock for generate_bot_ips
    mock_generate.return_value = 0

    # Create a temporary output file path
    output_file = tmp_path / "custom_bot_ips.py"

    # Import the main function
    from good_bots import __main__

    # Call the main function with custom path
    with patch('sys.argv', ['good_bots', '--output', str(output_file)]):
        __main__.main()

    # Verify generate_bot_ips was called with the custom output path
    mock_generate.assert_called_once_with(str(output_file))
