#!/usr/bin/env python3
"""Command line interface for good-bots package."""

import argparse
import os
import sys

from .core import generate_bot_ips


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Fetch bot IP addresses and generate django-turnstile-site-protect configuration'
    )
    parser.add_argument(
        '-p',
        '--path',
        type=str,
        help='Directory to save the bot_ips_config.py file (default: current directory)',
    )

    args = parser.parse_args()

    # Determine output file path with security validation
    output_filename = 'bot_ips_config.py'
    if args.path:
        # Validate path for security (prevent directory traversal)
        if '..' in args.path:
            print(
                "Error: Path traversal detected. Use of '..' in paths is not allowed.",
                file=sys.stderr,
            )
            return 1

        # Resolve and normalize the path
        safe_path = os.path.realpath(os.path.expanduser(args.path))

        # Ensure the output directory exists
        os.makedirs(safe_path, exist_ok=True, mode=0o755)
        output_path = os.path.join(safe_path, output_filename)
    else:
        output_path = output_filename

    # Generate the bot IPs configuration
    return generate_bot_ips(output_path)


if __name__ == "__main__":
    sys.exit(main())
