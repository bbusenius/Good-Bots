# Bot IP Address Fetcher

This script fetches IP addresses from various search engine bots and crawlers to exclude them from Cloudflare Turnstile verification.

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/bbusenius/Good-Bots.git
```

## Usage

After installation, use the `good-bots` command:

```bash
# Generate config in current directory
good-bots

# Generate config in a specific directory
good-bots -p /path/to/output/directory
```

This will generate `bot_ips_config.py` with the IP ranges in the format compatible with [django-turnstile-site-protect](https://github.com/bbusenius/django-turnstile-site-protect).

**Notes:**
- The tool will automatically create the output directory if it doesn't exist
- Path traversal (using `..` in paths) is blocked for security reasons

### Development Installation

For development, clone the repository and install in editable mode:

```bash
git clone https://github.com/bbusenius/Good-Bots.git
cd Good-Bots
pip install -e .
```

## Integration with Django

Add the following to your Django settings:

```python
# Your existing Turnstile settings
TURNSTILE_SITEKEY = 'your-site-key'
TURNSTILE_SECRET = 'your-secret-key'

# Exclude bot IPs from Turnstile verification
try:
    from .bot_ips_config import GOOD_BOTS
    # If you have existing excluded IPs, concatenate them:
    TURNSTILE_EXCLUDED_IPS = TURNSTILE_EXCLUDED_IPS + GOOD_BOTS
    
    # Or if this is your only source of excluded IPs:
    # TURNSTILE_EXCLUDED_IPS = GOOD_BOTS
except ImportError:
    # bot_ips_config.py not found - this is normal before running good-bots command
    print("Warning: bot_ips_config.py not found. Run 'good-bots' to generate it.")
    # TURNSTILE_EXCLUDED_IPS will use existing values or default to empty list
```

## Data Sources

The script fetches IP ranges from:
- Google (Googlebot, Special Crawlers, User-triggered Fetchers)
- Bing (Bingbot)
- OpenAI (GPTBot, ChatGPT User, SearchBot)
- Apple (Applebot)
- Perplexity (PerplexityBot, User)
- Naver (Naverbot)
- Mistral (User IPs)
- DuckDuckGo (DuckDuckBot, DuckAssistBot)
- Common Crawl (CCBot)

## Output Format

The generated configuration contains IP ranges in `start_ip-end_ip` format, which is compatible with django-turnstile-site-protect's IP range handling.

## Automation

You can run this script periodically (e.g., via cron) to keep your bot IP exclusions up to date:

```bash
# Run daily at 2 AM
# Note: Make sure the virtual environment with good-bots is activated
0 2 * * * /path/to/venv/bin/good-bots -p /path/to/django/project/

# Or if installed system-wide:
0 2 * * * good-bots -p /path/to/django/project/
```

## Additional Bot Configuration

You can add custom bot IP ranges that aren't covered by the main API sources by creating an `additional_bots.json` file in your working directory:

```json
{
  "additional_bots": [
    {
      "name": "Your Custom Bot",
      "description": "Description of the bot",
      "ip_ranges": [
        "192.168.1.0/24",
        "10.0.0.0/8",
        "203.0.112.0-203.0.113.255"
      ]
    }
  ]
}
```

The package includes Archive-It Bot by default. IP ranges can be specified in CIDR notation (e.g., `192.168.1.0/24`) or range format (e.g., `192.168.1.0-192.168.1.255`).
