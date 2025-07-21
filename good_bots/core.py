#!/usr/bin/env python3
"""
Core functionality to fetch bot IP addresses from various sources and generate a configuration
file compatible with django-turnstile-site-protect.
"""

import ipaddress
import json
import os
import sys
from datetime import datetime
from typing import List

try:
    from importlib.resources import files
except ImportError:
    # Fallback for Python < 3.9
    from importlib_resources import files

import requests


def fetch_json(url: str) -> dict:
    """Fetch JSON data from a URL with SSL verification."""
    try:
        response = requests.get(url, timeout=30, verify=True)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None


def cidr_to_range(cidr: str) -> str:
    """Convert CIDR notation to start_ip-end_ip format."""
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
        start_ip = str(network.network_address)
        end_ip = str(network.broadcast_address)
        return f"{start_ip}-{end_ip}"
    except ValueError as e:
        print(f"Invalid CIDR {cidr}: {e}", file=sys.stderr)
        return None


def extract_ipv4_addresses(data: dict) -> List[str]:
    """Extract IPv4 addresses from JSON data and convert to range format."""
    ipv4_ranges = []

    # Basic validation of API response structure
    if not isinstance(data, dict):
        print("Warning: API response is not a valid JSON object", file=sys.stderr)
        return ipv4_ranges

    if 'prefixes' not in data:
        print("Warning: API response missing 'prefixes' field", file=sys.stderr)
        return ipv4_ranges

    if not isinstance(data['prefixes'], list):
        print("Warning: API response 'prefixes' field is not a list", file=sys.stderr)
        return ipv4_ranges

    for prefix in data['prefixes']:
        if not isinstance(prefix, dict):
            print("Warning: Invalid prefix entry in API response", file=sys.stderr)
            continue

        if 'ipv4Prefix' in prefix:
            cidr = prefix['ipv4Prefix']
            if isinstance(cidr, str):
                ip_range = cidr_to_range(cidr)
                if ip_range:
                    ipv4_ranges.append(ip_range)
            else:
                print(f"Warning: Invalid ipv4Prefix format: {cidr}", file=sys.stderr)

    return ipv4_ranges


def load_additional_bots(config_file: str = None) -> dict:
    """Load additional bot IP ranges from configuration file."""
    if config_file is None:
        # Try to load from package data first
        try:
            config_content = (files('good_bots') / 'additional_bots.json').read_text()
            config = json.loads(config_content)
        except (FileNotFoundError, ImportError, json.JSONDecodeError):
            # Fall back to local file if package data not available
            config_file = 'additional_bots.json'
            if not os.path.exists(config_file):
                return {}
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(
                    f"Warning: Could not load additional bots config: {e}",
                    file=sys.stderr,
                )
                return {}
    else:
        if not os.path.exists(config_file):
            return {}
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(
                f"Warning: Could not load additional bots config: {e}", file=sys.stderr
            )
            return {}

    additional_ranges = {}
    for bot in config.get('additional_bots', []):
        bot_name = bot.get('name', 'Unknown Bot')
        ip_ranges = []

        for ip_range in bot.get('ip_ranges', []):
            if '/' in ip_range:  # CIDR notation
                converted_range = cidr_to_range(ip_range)
                if converted_range:
                    ip_ranges.append(converted_range)
            else:  # Already in range format or single IP
                ip_ranges.append(ip_range)

        if ip_ranges:
            additional_ranges[bot_name] = sorted(set(ip_ranges))

    return additional_ranges


def generate_bot_ips(output_path: str = None) -> int:
    """Generate bot IP configuration file."""
    if output_path is None:
        output_path = 'bot_ips_config.py'

    # Fetch the main endpoint list
    main_url = "https://search-engine-ip-tracker.merj.com/status"
    print(f"Fetching endpoint list from {main_url}...")

    main_data = fetch_json(main_url)
    if not main_data or 'data' not in main_data:
        print("Failed to fetch main endpoint list", file=sys.stderr)
        return 1

    # Load additional bot ranges from config file
    additional_bots = load_additional_bots()

    # Dictionary to organize IP ranges by bot
    bot_ip_ranges = additional_bots.copy()  # Start with additional bots
    total_ranges = sum(len(ranges) for ranges in additional_bots.values())

    # Process each endpoint
    for item in main_data['data']:
        if 'source' not in item or 'url' not in item['source']:
            continue

        endpoint_url = item['source']['url']
        source_id = item['source'].get('id', 'unknown')
        source_type = item['source'].get('type', 'unknown')

        print(f"Processing {source_type}/{source_id}: {endpoint_url}")

        endpoint_data = fetch_json(endpoint_url)
        if endpoint_data:
            ipv4_ranges = extract_ipv4_addresses(endpoint_data)
            if ipv4_ranges:
                # Create a readable bot name
                bot_name = (
                    f"{source_type.title()} - {source_id.replace('-', ' ').title()}"
                )
                bot_ip_ranges[bot_name] = sorted(
                    set(ipv4_ranges)
                )  # Remove duplicates and sort
                total_ranges += len(ipv4_ranges)
                print(f"  Found {len(ipv4_ranges)} IPv4 ranges")
            else:
                print("  No IPv4 ranges found")
        else:
            print("  Failed to fetch data")

    # Print summary of additional bots if any were loaded
    if additional_bots:
        print("\nAdditional bots loaded from config:")
        for bot_name, ranges in additional_bots.items():
            print(f"  {bot_name}: {len(ranges)} ranges")

    # Generate the Python configuration
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_content = f'''# Bot IP addresses for django-turnstile-site-protect
# Generated on {current_time}
# Source: https://search-engine-ip-tracker.merj.com/status

GOOD_BOTS = [
'''

    # Add IP ranges organized by bot
    for bot_name, ip_ranges in sorted(bot_ip_ranges.items()):
        output_content += f"    # {bot_name}\n"
        for ip_range in ip_ranges:
            output_content += f"    '{ip_range}',\n"
        output_content += "\n"  # Add blank line between bots

    output_content += f"""]

# Total IP ranges: {total_ranges}
"""

    # Write to file
    try:
        with open(output_path, 'w') as f:
            f.write(output_content)

        output_filename = os.path.basename(output_path)
        print(f"\nGenerated {output_path} with {total_ranges} IP ranges")
        print("You can now import this in your Django settings:")
        print(f"from .{os.path.splitext(output_filename)[0]} import GOOD_BOTS")
        print("Then concatenate to your existing TURNSTILE_EXCLUDED_IPS:")
        print("TURNSTILE_EXCLUDED_IPS = TURNSTILE_EXCLUDED_IPS + GOOD_BOTS")

        return 0
    except IOError as e:
        print(f"Error writing to {output_path}: {e}", file=sys.stderr)
        return 1
