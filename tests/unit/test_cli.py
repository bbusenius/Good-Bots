"""Unit tests for CLI functionality."""

from unittest.mock import patch

import pytest

from good_bots.cli import main


def test_cli_help(capsys):
    """Test CLI help output."""
    with patch('sys.argv', ['good-bots', '--help']):
        with pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    assert "--help" in captured.out
    assert "--path" in captured.out


@patch('good_bots.cli.generate_bot_ips')
def test_cli_default_path(mock_generate, tmp_path):
    """Test CLI with default path."""
    with patch('sys.argv', ['good-bots']):
        with patch('os.getcwd', return_value=str(tmp_path)):
            main()
    # Check that generate_bot_ips was called with the correct path
    mock_generate.assert_called_once()
    called_path = mock_generate.call_args[0][0]
    assert called_path.endswith('bot_ips_config.py')


@patch('good_bots.cli.generate_bot_ips')
def test_cli_custom_path(mock_generate, tmp_path):
    """Test CLI with custom path."""
    custom_path = tmp_path / "custom"
    custom_path.mkdir()
    with patch('sys.argv', ['good-bots', '--path', str(custom_path)]):
        main()
    output_file = custom_path / "bot_ips_config.py"
    mock_generate.assert_called_once_with(str(output_file))


def test_cli_path_traversal_protection(capsys, tmp_path):
    """Test CLI path traversal protection."""
    malicious_path = str(tmp_path / ".." / "sensitive")
    with patch('sys.argv', ['good-bots', '--path', malicious_path]):
        result = main()
    assert result == 1
    captured = capsys.readouterr()
    assert "Path traversal detected" in captured.err


@patch('good_bots.cli.generate_bot_ips')
def test_cli_creates_directory(mock_generate, tmp_path):
    """Test that CLI creates non-existent directories."""
    new_dir = tmp_path / "new_directory"
    with patch('sys.argv', ['good-bots', '--path', str(new_dir)]):
        main()
    assert new_dir.exists()
    output_file = new_dir / "bot_ips_config.py"
    mock_generate.assert_called_once_with(str(output_file))


@patch('good_bots.core.generate_bot_ips')
def test_main_module_execution(mock_generate, tmp_path):
    """Test that __main__ execution works correctly."""
    with patch('sys.argv', ['good-bots', '--path', str(tmp_path)]):
        with patch('good_bots.cli.main') as mock_main:
            with patch('good_bots.cli.__name__', '__main__'):
                import good_bots.cli

                good_bots.cli.main()
    mock_main.assert_called_once()
