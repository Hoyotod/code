import argparse
import os
import shutil

from rich.console import Console
from rich.panel import Panel
from utils.genshin_scraper import GenshinScraper
from utils.starrail_scraper import StarrailScraper

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
