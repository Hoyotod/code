# utils/scraper_base.py
import dataclasses
import json
import os
import random
import re
import time
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup
from curl_cffi import requests
from rich.console import Console

from .constants import (
    COLOR_ACTIVE,
    COLOR_EXPIRED,
    DISCORD_EMBED_FOOTER,
    GITHUB_ASSETS_URL_TEMPLATE,
    IMPERSONATE_PROFILES,
    PAGE_LOAD_WAIT,
    REQUEST_TIMEOUT,
    RETRY_DELAY_MEDIUM,
    RETRY_DELAY_SHORT,
    STATUS_ACTIVE,
    STATUS_EXPIRED,
    WEBHOOK_TIMEOUT,
)
from .models import Code, Duration, Reward

console = Console()


class ScraperBase(ABC):
    def __init__(self, game_name: str, game_color: str, folder_name: str):
        self.game_name = game_name
        self.game_color = game_color
        self.game_folder = folder_name
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self._last_impersonate: str | None = None

        os.makedirs(self.game_folder, exist_ok=True)

    def log(self, message: str, style: str = "white"):
        """Helper untuk logging dengan warna spesifik game."""
        console.print(
            f"[{self.game_color}][{self.game_name}][/{self.game_color}] {message}",
            style=style,
        )

    def get_soup(self, url: str) -> BeautifulSoup | None:
        """
        Alur: Request (requests.get) -> Tunggu -> Parse
        """
        self.log(f"Mengambil data dari: [bold]{url}[/bold]")

        try:
            tried: set[str] = set()
            max_attempts = len(IMPERSONATE_PROFILES)

            for _attempt in range(max_attempts):
                available = [
                    c
                    for c in IMPERSONATE_PROFILES
                    if c not in tried and c != self._last_impersonate
                ]
                if not available:
                    available = [c for c in IMPERSONATE_PROFILES if c not in tried]
                if not available:
                    available = IMPERSONATE_PROFILES

                opt_impersonate = random.choice(available)
                tried.add(opt_impersonate)
                self._last_impersonate = opt_impersonate
                self.log(f"🔍 Menggunakan impersonate: [bold cyan]{opt_impersonate}[/bold cyan]")

                try:
                    response = requests.get(
                        url, impersonate=opt_impersonate, timeout=REQUEST_TIMEOUT
                    )
                except requests.exceptions.RequestException as e:
                    self.log(
                        f"❌ Error koneksi dengan impersonate {opt_impersonate}: {e}",
                        style="bold red",
                    )
                    time.sleep(RETRY_DELAY_SHORT)
                    continue

                if response.status_code == 200:
                    self.log(
                        "✅ Koneksi berhasil (200 OK). Menunggu halaman termuat...",
                        style="bold green",
                    )

                    time.sleep(PAGE_LOAD_WAIT)

                    soup = BeautifulSoup(response.content, "html.parser")
                    return soup

                if response.status_code == 403:
                    self.log(
                        f"❌ Akses Ditolak (403) dengan impersonate {opt_impersonate}. "
                        f"Mencoba impersonate lain...",
                        style="yellow",
                    )
                    time.sleep(RETRY_DELAY_MEDIUM)
                    continue

                self.log(
                    f"⚠️ Gagal memuat halaman. Status: {response.status_code}",
                    style="yellow",
                )
                break

        except Exception as e:
            self.log(f"❌ Error koneksi: {e}", style="bold red")

        return None

    def _load_existing_json(self, json_path: str) -> list[dict]:
        if not os.path.exists(json_path):
            return []

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError) as e:
            self.log(f"❌ Error membaca {json_path}: {e}", style="bold red")

        return []

    def _normalize_code_data(self, code_dicts: list[dict]) -> list[str]:
        return sorted(
            json.dumps(code_dict, sort_keys=True, ensure_ascii=False) for code_dict in code_dicts
        )

    def save_results(self, codes: list[Code]):
        """Menyimpan data ke JSON dan TXT."""
        if not codes:
            self.log(
                "⚠️ Tidak ada kode untuk disimpan - data lama tetap ada (mungkin basi).",
                style="dim yellow",
            )
            return

        active_codes = [c for c in codes if c.status == STATUS_ACTIVE]
        expired_codes = [c for c in codes if c.status == STATUS_EXPIRED]

        data_map = {"all": codes, "active": active_codes, "expired": expired_codes}

        self.log(
            f"Menyimpan data... (Active: {len(active_codes)} | Expired: {len(expired_codes)})",
        )

        for key, data_list in data_map.items():
            json_path = os.path.join(self.game_folder, f"{key}.json")
            txt_path = os.path.join(self.game_folder, f"{key}.txt")
            new_data = [dataclasses.asdict(c) for c in data_list]
            old_data = self._load_existing_json(json_path)

            if not new_data and old_data:
                self.log(
                    f"Tidak ada kode baru untuk '{key}', menyimpan data lama tetap.",
                    style="dim yellow",
                )
                continue

            if old_data and self._normalize_code_data(old_data) == self._normalize_code_data(
                new_data
            ):
                self.log(
                    f"Data '{key}' tidak berubah. Menjaga file lama agar tetap utuh.",
                    style="dim yellow",
                )
                continue

            if key == "active":
                try:
                    if old_data:
                        old_codes = {d.get("code") for d in old_data}
                        new_codes = {d.get("code") for d in new_data}
                        added = new_codes - old_codes
                        for d in new_data:
                            code_str = d.get("code")
                            if not code_str or code_str not in added:
                                continue

                            rewards_list = []
                            for r in d.get("rewards", []) or []:
                                try:
                                    rewards_list.append(Reward(**r))
                                except Exception as e:
                                    self.log(
                                        f"⚠️ Error parsing reward: {e}",
                                        style="dim yellow",
                                    )

                            duration_dict = d.get("duration") or {}
                            try:
                                duration_obj = (
                                    Duration(**duration_dict)
                                    if isinstance(duration_dict, dict)
                                    else Duration()
                                )
                            except Exception as e:
                                self.log(f"⚠️ Error parsing duration: {e}", style="dim yellow")
                                duration_obj = Duration()

                            code_obj = Code(
                                code=code_str,
                                server=d.get("server", ""),
                                status=d.get("status", ""),
                                rewards=rewards_list,
                                duration=duration_obj,
                                link=d.get("link"),
                            )

                            try:
                                self.send_new_code_webhook(code_obj)
                            except requests.exceptions.RequestException as e:
                                self.log(
                                    f"❌ Error saat memanggil webhook untuk {code_str}: {e}",
                                    style="bold red",
                                )
                except Exception as e:
                    self.log(
                        f"❌ Error saat memeriksa kode baru untuk webhook: {e}",
                        style="bold red",
                    )

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(c.code for c in data_list))

            self.log(f"✅ File '{key}' berhasil diperbarui.", style="bold green")

        self.log("✅ Proses penyimpanan selesai.", style="bold green")

    def build_webhook_payload(self, code: Code) -> dict:
        """Build Discord embed payload for a code."""
        rewards = code.rewards or []
        if rewards:
            rewards_text = "\n".join(f"- {r.name}" for r in rewards)
        else:
            rewards_text = "-"

        embed_color = COLOR_ACTIVE if code.status == STATUS_ACTIVE else COLOR_EXPIRED

        embed = {
            "author": {"name": self.game_name},
            "title": f"{code.code}",
            "description": f"**Server:** {code.server}\n**Link:** {code.link}\n",
            "color": embed_color,
            "fields": [
                {"name": "Rewards", "value": rewards_text, "inline": False},
            ],
            "image": {"url": GITHUB_ASSETS_URL_TEMPLATE.format(game_folder=self.game_folder)},
            "footer": {"text": DISCORD_EMBED_FOOTER},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        }

        return {"embeds": [embed]}

    def send_new_code_webhook(self, code: Code, webhook_url: str | None = None):
        """Kirim embed ke Discord webhook untuk kode baru.

        Builds a simple embed containing the code, server, status, rewards and link.
        If `webhook_url` is not provided, `self.discord_webhook_url` will be used.
        """
        webhook = webhook_url or self.discord_webhook_url
        if not webhook:
            self.log(
                "Tidak ada `DISCORD_WEBHOOK_URL` dikonfigurasi; melewatkan pengiriman webhook.",
                style="dim yellow",
            )
            return

        payload = self.build_webhook_payload(code)

        try:
            resp = requests.post(webhook, json=payload, timeout=WEBHOOK_TIMEOUT)
            if resp.status_code in (200, 201, 204):
                self.log(f"✅ Webhook berhasil dikirim untuk kode {code.code}.", style="bold green")
            else:
                self.log(
                    f"❌ Gagal mengirim webhook (status: {resp.status_code}): {resp.text}",
                    style="bold red",
                )
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Error saat mengirim webhook: {e}", style="bold red")

    def _extract_rewards(self, cell) -> list[Reward]:
        """Extract rewards from a fandom wiki table cell."""
        rewards = []
        items = cell.find_all("span", class_="item")
        for item in items:
            name_tag = item.find("span", class_="item-text")
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            img_tag = item.find("img")
            img_url = ""
            if img_tag:
                src = img_tag.get("data-src") or img_tag.get("src")
                if src:
                    img_url = src.split(".png")[0] + ".png"
            rewards.append(Reward(name=name, image=img_url))
        return rewards

    def _extract_duration(self, text: str) -> Duration:
        """Extract duration info from text using regex patterns."""
        discovered_match = re.search(r"Discovered: (.*?)(?:$|Valid|Expired|Note)", text)
        valid_match = re.search(r"Valid(?: until)?: (.*?)(?:$|Discovered|Expired|Note)", text)
        expired_match = re.search(r"Expired: (.*?)(?:$|Discovered|Valid|Note)", text)
        notes_match = re.search(r"Note(?:s)?: (.*?)(?:$|Discovered|Valid|Expired)", text)

        return Duration(
            discovered=discovered_match.group(1).strip() if discovered_match else None,
            valid=valid_match.group(1).strip() if valid_match else None,
            expired=expired_match.group(1).strip() if expired_match else None,
            notes=notes_match.group(1).strip() if notes_match else None,
        )

    def _clean_code(self, code_text: str) -> str:
        """Clean and normalize a code string."""
        return re.sub(r"[^A-Z0-9]", "", code_text.upper())

    @abstractmethod
    def scrape(self):
        """Implementasi spesifik tiap game."""
        pass
