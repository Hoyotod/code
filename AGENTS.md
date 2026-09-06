# AGENTS.md

## Project Overview

Python 3.13 web scraper that extracts promotional codes for Hoyoverse games (Genshin Impact, Honkai: Star Rail, Zenless Zone Zero) from fandom wikis and sends new codes to Discord via webhook.

## Commands

```bash
# Run scraper normally (use uv run since python may not be in PATH)
uv run python main.py

# Reset all data folders and scrape fresh (sends all active codes to webhook)
uv run python main.py --reset

# Install dependencies
uv sync

# Install with dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy .
```

## Architecture

### Core Structure

- `main.py` - Entry point with `SCRAPERS` registry, orchestrates scrapers, handles reset and webhook broadcast
- `utils/scraper_base.py` - Abstract base class with shared scraping, parsing, saving, and webhook logic
- `utils/genshin_scraper.py` - Genshin Impact scraper (fandom wiki tables)
- `utils/starrail_scraper.py` - Honkai: Star Rail scraper (fandom wiki tables)
- `utils/zzz_scraper.py` - Zenless Zone Zero scraper (fandom wiki tables)
- `utils/models.py` - Data models: `Code`, `Reward`, `Duration` (dataclasses)
- `utils/constants.py` - Shared constants (colors, timeouts, status strings, URLs)
- `tests/` - Test suite with basic unit tests for parsing logic

### Key Design Patterns

**Scraper Registry**: `main.py` defines `SCRAPERS = [GenshinScraper(), StarrailScraper(), ZZZScraper()]` as single source of truth. Adding a new game requires only adding one scraper instance to this list.

**Shared Parsing**: `ScraperBase` provides `_extract_rewards()`, `_extract_duration()`, and `_clean_code()` methods that all scrapers inherit. Game-specific scrapers override only what's different.

**Webhook Builder**: `ScraperBase.build_webhook_payload()` creates Discord embeds. Both incremental updates and batch resets reuse this method.

### Output Structure

- `genshin/`, `starrail/`, and `zzz/` folders with `all.json`, `active.json`, `expired.json`, `*.txt`

## Important Behaviors

### Anti-Bot Evasion
`ScraperBase.get_soup()` rotates through 6 browser impersonation profiles (defined in `constants.IMPERSONATE_PROFILES`) using `curl_cffi`. On 403, retries with different profile. Waits `PAGE_LOAD_WAIT` (5s) after successful 200 to let page load.

### Incremental Updates
`save_results()` compares normalized JSON before writing. Only updates changed files. Detects new active codes by diffing with previous `active.json` and sends webhook for each new code via `send_new_code_webhook()`.

### Webhook Behavior
- Normal run: sends webhook only for newly discovered active codes
- `--reset` flag: deletes all data folders, scrapes fresh, calls `send_all_active_codes_webhook()` which reuses `build_webhook_payload()` for every active code

### Code Normalization
Codes are cleaned with `_clean_code()`: `re.sub(r"[^A-Z0-9]", "", code.upper())` to remove special chars and force uppercase.

### Status Constants
Use `STATUS_ACTIVE` and `STATUS_EXPIRED` from `constants.py` instead of magic strings.

## Error Handling

- Narrow exception types: `json.JSONDecodeError`, `OSError`, `requests.exceptions.RequestException`
- All exceptions are logged (never silent `pass`)
- Stale data warning: if `save_results()` receives empty codes list, it logs a warning that existing data may be stale
- Top-level exception handler in `main()` catches unexpected errors

## Environment

- `.env` with `DISCORD_WEBHOOK_URL` (optional, skips webhook if missing)
- `.editorconfig` specifies 2-space indent, CRLF line endings

## Dependencies

- `curl_cffi` for browser impersonation
- `beautifulsoup4` for HTML parsing
- `rich` for console output
- Dev: `pytest`, `ruff`, `mypy`

## Testing

Run tests with `uv run pytest -v`. Current coverage:
- Code cleaning and normalization (`_clean_code`)
- Duration extraction from text (`_extract_duration`)
- Webhook payload building (`build_webhook_payload`)
- JSON normalization for diffing (`_normalize_code_data`)

All 4 tests pass. Tests use a mock scraper to verify base class functionality.

## Tooling

- **ruff**: Line length 100, Python 3.13 target, rules E/F/I/UP/W
- **mypy**: Python 3.13, warn on return any and unused configs
- **pytest**: Basic unit tests for parsing helpers

## Adding a New Game

1. Create `utils/{game}_scraper.py` extending `ScraperBase`
2. Implement `scrape()` method (use inherited `_extract_rewards()`, `_extract_duration()`, `_clean_code()`)
3. Add scraper instance to `SCRAPERS` list in `main.py`
4. Add corresponding asset image to `assets/{game}.jpg`

That's it - reset, webhook broadcast, and all orchestration automatically work.

