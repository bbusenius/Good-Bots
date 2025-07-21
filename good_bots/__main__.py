"""Command-line interface for Good-Bots."""

import argparse
import sys

from good_bots import core


def main():
    """Run the Good-Bots CLI."""
    parser = argparse.ArgumentParser(
        description='Generate bot IP configuration for django-turnstile-site-protect'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='bot_ips_config.py',
        help='Output file path (default: bot_ips_config.py)',
    )

    args = parser.parse_args()

    print("Generating bot IP configuration...")
    result = core.generate_bot_ips(args.output)

    if result == 0:
        print("Configuration generated successfully")
    else:
        print("Failed to generate configuration", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
