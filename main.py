import argparse
import json
import os
import shutil

from curl_cffi import requests
from rich.console import Console
from rich.panel import Panel

from utils.constants import WEBHOOK_TIMEOUT
from utils.genshin_scraper import GenshinScraper
from utils.models import Code, Duration, Reward
from utils.starrail_scraper import StarrailScraper
from utils.zzz_scraper import ZZZScraper

console = Console()

SCRAPERS = [
    GenshinScraper(),
    StarrailScraper(),
    ZZZScraper(),
]


def reset_folders():
    """Menghapus dan membuat ulang folder data game."""
    console.print("[bold yellow]🔄 Mereset folder data...[/bold yellow]")
    for scraper in SCRAPERS:
        folder = scraper.game_folder
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
    console.print("[bold green]✅ Folder berhasil di-reset.[/bold green]")


def send_all_active_codes_webhook():
    """Mengirim semua kode aktif ke Discord webhook setelah reset."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        console.print(
            "[dim yellow]⚠️ Tidak ada DISCORD_WEBHOOK_URL, melewatkan pengiriman.[/dim yellow]"
        )
        return

    console.print("[bold cyan]📤 Mengirim semua kode aktif ke Discord...[/bold cyan]")
    total_sent = 0

    scraper_map = {scraper.game_folder: scraper for scraper in SCRAPERS}

    for game_folder, scraper in scraper_map.items():
        active_json = os.path.join(game_folder, "active.json")

        if not os.path.exists(active_json):
            continue

        try:
            with open(active_json, encoding="utf-8") as f:
                codes_data = json.load(f)

            for code_dict in codes_data:
                try:
                    rewards_list = []
                    for r in code_dict.get("rewards", []) or []:
                        try:
                            rewards_list.append(Reward(**r))
                        except Exception as e:
                            console.print(f"[dim yellow]⚠️ Error parsing reward: {e}[/dim yellow]")

                    duration_dict = code_dict.get("duration") or {}
                    try:
                        duration_obj = (
                            Duration(**duration_dict)
                            if isinstance(duration_dict, dict)
                            else Duration()
                        )
                    except Exception as e:
                        console.print(f"[dim yellow]⚠️ Error parsing duration: {e}[/dim yellow]")
                        duration_obj = Duration()

                    code_str = code_dict.get("code", "")
                    if not code_str:
                        continue

                    code_obj = Code(
                        code=code_str,
                        server=code_dict.get("server", ""),
                        status=code_dict.get("status", ""),
                        rewards=rewards_list,
                        duration=duration_obj,
                        link=code_dict.get("link"),
                    )

                    payload = scraper.build_webhook_payload(code_obj)

                    try:
                        resp = requests.post(webhook_url, json=payload, timeout=WEBHOOK_TIMEOUT)
                        if resp.status_code in (200, 201, 204):
                            total_sent += 1
                        else:
                            console.print(
                                f"[dim red]❌ Gagal mengirim {code_str} "
                                f"(status: {resp.status_code})[/dim red]"
                            )
                    except requests.exceptions.RequestException as e:
                        console.print(f"[dim red]❌ Error mengirim {code_str}: {e}[/dim red]")

                except Exception as e:
                    console.print(f"[dim red]❌ Error memproses kode: {e}[/dim red]")

        except (json.JSONDecodeError, OSError) as e:
            console.print(f"[dim red]❌ Error membaca {active_json}: {e}[/dim red]")

    console.print(
        f"[bold green]✅ Berhasil mengirim {total_sent} kode aktif ke Discord.[/bold green]"
    )


def main(should_reset=False):
    """Fungsi utama untuk menjalankan semua scraper secara berurutan."""

    console.print(
        Panel(
            "🚀 [bold white]Hoyo Code Scraper[/bold white]",
            style="bold cyan",
            title_align="center",
            subtitle="[dim]Automate get latest codes for Hoyo games[/dim]",
        )
    )

    if should_reset is True:
        reset_folders()
        console.print("")

    for scraper in SCRAPERS:
        console.print(
            Panel(
                f"▶️ Memulai Scraper: [bold]{scraper.game_name}[/bold]",
                border_style=scraper.game_color,
            )
        )
        scraper.scrape()
        console.print("")

    console.print(
        Panel(
            "✨ [bold green]Semua tugas scraping selesai![/bold green]",
            style="green",
        )
    )

    if should_reset is True:
        console.print("")
        send_all_active_codes_webhook()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hoyo Code Scraper")
    parser.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="Hapus dan reset folder data sebelum scraping.",
    )
    args = parser.parse_args()

    try:
        main(should_reset=args.reset)
    except KeyboardInterrupt:
        console.print("\n[bold red]⛔ Proses dihentikan paksa oleh pengguna.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Error tidak terduga: {e}[/bold red]")
