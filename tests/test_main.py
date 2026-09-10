import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from main import reset_folders, send_all_active_codes_webhook


def test_reset_folders_creates_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    with patch("main.SCRAPERS", [
        MagicMock(game_folder="genshin"),
        MagicMock(game_folder="starrail"),
    ]):
        os.makedirs("genshin", exist_ok=True)
        with open("genshin/test.txt", "w") as f:
            f.write("old data")

        reset_folders()

        assert os.path.exists("genshin")
        assert os.path.exists("starrail")
        assert not os.path.exists("genshin/test.txt")


def test_send_all_active_codes_webhook_no_webhook_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

    with patch("main.SCRAPERS", []):
        send_all_active_codes_webhook()


def test_send_all_active_codes_webhook_with_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "http://example.com/webhook")

    os.makedirs("genshin", exist_ok=True)
    active_codes = [
        {
            "code": "TEST123",
            "server": "Global",
            "status": "active",
            "rewards": [{"name": "Primogem x100", "image": "http://example.com/gem.png"}],
            "duration": {
                "discovered": "2023-01-01",
                "valid": "2023-12-31",
                "expired": None,
                "notes": None,
            },
            "link": None,
        }
    ]

    with open("genshin/active.json", "w", encoding="utf-8") as f:
        json.dump(active_codes, f)

    mock_scraper = MagicMock()
    mock_scraper.game_folder = "genshin"
    mock_scraper.build_webhook_payload.return_value = {"embeds": [{"title": "TEST123"}]}

    with patch("main.SCRAPERS", [mock_scraper]), patch("main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        send_all_active_codes_webhook()

        assert mock_post.called
        assert mock_scraper.build_webhook_payload.called


def test_send_all_active_codes_webhook_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "http://example.com/webhook")

    mock_scraper = MagicMock()
    mock_scraper.game_folder = "nonexistent"

    with patch("main.SCRAPERS", [mock_scraper]):
        send_all_active_codes_webhook()


def test_send_all_active_codes_webhook_invalid_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "http://example.com/webhook")

    os.makedirs("genshin", exist_ok=True)
    with open("genshin/active.json", "w") as f:
        f.write("invalid json{")

    mock_scraper = MagicMock()
    mock_scraper.game_folder = "genshin"

    with patch("main.SCRAPERS", [mock_scraper]):
        send_all_active_codes_webhook()


def test_send_all_active_codes_webhook_empty_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "http://example.com/webhook")

    os.makedirs("genshin", exist_ok=True)
    active_codes: list[dict[str, object]] = [
        {
            "code": "",
            "server": "Global",
            "status": "active",
            "rewards": [],
            "duration": {},
            "link": None,
        }
    ]

    with open("genshin/active.json", "w", encoding="utf-8") as f:
        json.dump(active_codes, f)

    mock_scraper = MagicMock()
    mock_scraper.game_folder = "genshin"

    with patch("main.SCRAPERS", [mock_scraper]), patch("main.requests.post") as mock_post:
        send_all_active_codes_webhook()
        mock_post.assert_not_called()
