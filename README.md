# Hoyo Code Scraper

Automated scraper for promotional codes from Hoyoverse games (Genshin Impact, Honkai: Star Rail, Zenless Zone Zero). Extracts codes from fandom wikis and sends new active codes to Discord via webhook.

## Features

- Scrapes promotional codes from fandom wikis for three games:
  - **Genshin Impact** - Active & expired codes
  - **Honkai: Star Rail** - Active & expired codes
  - **Zenless Zone Zero** - Active & expired codes
- Detects active and expired codes automatically
- Sends Discord webhook notifications for new codes only
- Automatic deduplication and change detection
- Browser impersonation for anti-bot evasion (Cloudflare bypass)
- Incremental updates - only saves when data changes

## Requirements

- Python 3.13+
- uv (recommended) or pip

## Setup

### 1. Install dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file (optional):

```bash
DISCORD_WEBHOOK_URL=your_webhook_url_here
```

If not set, the scraper will skip webhook notifications.

## Usage

### Basic scraping

```bash
# Using uv (recommended)
uv run python main.py

# Or if python is in PATH
python main.py
```

Scrapes codes and saves to `genshin/`, `starrail/`, and `zzz/` folders. Sends webhook only for newly discovered active codes.

### Reset and resend all codes

```bash
# Using uv (recommended)
uv run python main.py --reset

# Or if python is in PATH
python main.py --reset
```

Deletes all data folders, scrapes fresh, and sends webhook for every active code.

## Output

Each game folder contains:
- `all.json` / `all.txt` - All codes
- `active.json` / `active.txt` - Active codes only
- `expired.json` / `expired.txt` - Expired codes only

## Development

### Install dev dependencies

```bash
uv sync --group dev
```

### Run tests

```bash
uv run pytest -v
```

### Format and lint

```bash
uv run ruff format .
uv run ruff check .
```

### Type check

```bash
uv run mypy .
```

## Architecture

- `main.py` - Entry point and scraper orchestration
- `utils/scraper_base.py` - Abstract base class with shared logic
- `utils/genshin_scraper.py` - Genshin Impact scraper
- `utils/starrail_scraper.py` - Honkai: Star Rail scraper
- `utils/zzz_scraper.py` - Zenless Zone Zero scraper
- `utils/models.py` - Data models
- `utils/constants.py` - Shared constants

## License

See [LICENSE](LICENSE)

