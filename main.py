import argparse
import json
import os
import shutil
import time

from curl_cffi import requests
from rich.console import Console
from rich.panel import Panel
from utils.genshin_scraper import GenshinScraper
from utils.starrail_scraper import StarrailScraper
from utils.models import Code, Reward, Duration

console = Console()


def reset_folders():
    """Menghapus dan membuat ulang folder data game."""
    console.print("[bold yellow]🔄 Mereset folder data...[/bold yellow]")
    for folder in [
        "genshin",
        # "honkai",
        "starrail",
    ]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
    console.print("[bold green]✅ Folder berhasil di-reset.[/bold green]")


def send_all_active_codes_webhook():
    """Mengirim semua kode aktif ke Discord webhook setelah reset."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        console.print("[dim yellow]⚠️ Tidak ada DISCORD_WEBHOOK_URL, melewatkan pengiriman.[/dim yellow]")
        return

    console.print("[bold cyan]📤 Mengirim semua kode aktif ke Discord...[/bold cyan]")
    total_sent = 0

    for game_folder in ["genshin", "starrail"]:
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
                        except Exception:
                            pass

                    duration_dict = code_dict.get("duration") or {}
                    try:
                        duration_obj = Duration(**duration_dict) if isinstance(duration_dict, dict) else Duration()
                    except Exception:
                        duration_obj = Duration()

                    code_obj = Code(
                        code=code_dict.get("code", ""),
                        server=code_dict.get("server", ""),
                        status=code_dict.get("status", ""),
                        rewards=rewards_list,
                        duration=duration_obj,
                        link=code_dict.get("link"),
                    )

                    # Tentukan game name dari folder
                    game_name = "Genshin Impact" if game_folder == "genshin" else "Honkai: Star Rail"

                    # Kirim webhook
                    rewards = code_obj.rewards or []
                    if rewards:
                        rewards_text = "\n".join(f"- {r.name}" for r in rewards)
                    else:
                        rewards_text = "-"

                    color_active = 0x2ECC71
                    embed_color = color_active

                    embed = {
                        "author": {"name": game_name},
                        "title": f"{code_obj.code}",
                        "description": f"**Server:** {code_obj.server}\n**Link:** {code_obj.link}\n",
                        "url": code_obj.link or None,
                        "color": embed_color,
                        "fields": [
                            {"name": "Rewards", "value": rewards_text, "inline": False},
                        ],
                        "image": {"url": f"https://raw.githubusercontent.com/Hoyotod/code/main/assets/{game_folder}.jpg"},
                        "footer": {"text": "Hoyo Code"},
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                    }

                    payload = {"embeds": [embed]}

                    try:
                        resp = requests.post(webhook_url, json=payload, timeout=10)
                        if resp.status_code in (200, 201, 204):
                            total_sent += 1
                        else:
                            console.print(f"[dim red]❌ Gagal mengirim {code_dict.get('code')} (status: {resp.status_code})[/dim red]")
                    except Exception as e:
                        console.print(f"[dim red]❌ Error mengirim {code_dict.get('code')}: {e}[/dim red]")

                except Exception as e:
                    console.print(f"[dim red]❌ Error memproses kode: {e}[/dim red]")

        except Exception as e:
            console.print(f"[dim red]❌ Error membaca {active_json}: {e}[/dim red]")

    console.print(f"[bold green]✅ Berhasil mengirim {total_sent} kode aktif ke Discord.[/bold green]")



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

    scrapers = [
        GenshinScraper(),
        StarrailScraper(),
        # HonkaiScraper() # disable due to inconsistent site structure
    ]

    for scraper in scrapers:
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

    # Kirim semua kode aktif ke webhook jika reset flag digunakan
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
        console.print(
            "\n[bold red]⛔ Proses dihentikan paksa oleh pengguna.[/bold red]"
        )
