import argparse
import json
import os
import shutil

from curl_cffi import requests
from rich.console import Console
from rich.panel import Panel

from utils.constants import WEBHOOK_TIMEOUT
from utils.genshin_scraper import GenshinScraper
from utils.models import Code
from utils.starrail_scraper import StarrailScraper
from utils.zzz_scraper import ZZZScraper

console = Console()

SCRAPERS = [
    GenshinScraper(),
    StarrailScraper(),
    ZZZScraper(),
]


def reset_folders() -> None:
    """Menghapus dan membuat ulang folder data game."""
    console.print("[bold yellow]🔄 Mereset folder data...[/bold yellow]")
    for scraper in SCRAPERS:
        folder = scraper.game_folder
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
    console.print("[bold green]✅ Folder berhasil di-reset.[/bold green]")


def send_all_active_codes_webhook() -> None:
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
                    code_obj = Code.from_dict(code_dict)
                    if not code_obj:
                        continue

                    payload = scraper.build_webhook_payload(code_obj)

                    try:
                        resp = requests.post(webhook_url, json=payload, timeout=WEBHOOK_TIMEOUT)
                        if resp.status_code in (200, 201, 204):
                            total_sent += 1
                        else:
                            console.print(
                                f"[dim red]❌ Gagal mengirim {code_obj.code} "
                                f"(status: {resp.status_code})[/dim red]"
                            )
                    except requests.exceptions.RequestException as e:
                        console.print(f"[dim red]❌ Error mengirim {code_obj.code}: {e}[/dim red]")

                except Exception as e:
                    console.print(f"[dim red]❌ Error memproses kode: {e}[/dim red]")

        except (json.JSONDecodeError, OSError) as e:
            console.print(f"[dim red]❌ Error membaca {active_json}: {e}[/dim red]")

    console.print(
        f"[bold green]✅ Berhasil mengirim {total_sent} kode aktif ke Discord.[/bold green]"
    )


def send_all_active_codes_telegram() -> None:
    """Mengirim semua kode aktif ke channel Telegram setelah reset."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        console.print("[dim yellow]\u26a0\ufe0f Telegram tidak dikonfigurasi.[/dim yellow]")
        return

    console.print("[bold cyan]\U0001f4e4 Mengirim semua kode aktif ke Telegram...[/bold cyan]")
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
                    code_obj = Code.from_dict(code_dict)
                    if not code_obj:
                        continue

                    try:
                        scraper.send_new_code_telegram(code_obj)
                        total_sent += 1
                    except requests.exceptions.RequestException as e:
                        console.print(
                            f"[dim red]\u274c Error kirim Telegram {code_obj.code}: {e}[/dim red]"
                        )

                except Exception as e:
                    console.print(f"[dim red]\u274c Error memproses kode: {e}[/dim red]")

        except (json.JSONDecodeError, OSError) as e:
            console.print(f"[dim red]\u274c Error membaca {active_json}: {e}[/dim red]")

    console.print(
        f"[bold green]\u2705 Berhasil mengirim {total_sent} kode aktif ke Telegram.[/bold green]"
    )


def main(should_reset: bool = False) -> None:
    """Fungsi utama untuk menjalankan semua scraper secara berurutan."""

    console.print(
        Panel(
            "🚀 [bold white]Hoyo Code Scraper[/bold white]",
            style="bold cyan",
            title_align="center",
            subtitle="[dim]Automate get latest codes for Hoyo games[/dim]",
        )
    )

    if should_reset:
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

    if should_reset:
        console.print("")
        send_all_active_codes_webhook()
        send_all_active_codes_telegram()


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
