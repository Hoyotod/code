from .constants import STATUS_ACTIVE, STATUS_EXPIRED
from .scraper_base import ScraperBase


class ZZZScraper(ScraperBase):
    def __init__(self) -> None:
        super().__init__(game_name="Zenless Zone Zero", game_color="yellow", folder_name="zzz")
        self.active_url = "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code"
        self.history_url = "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code/History"

    def scrape(self) -> None:
        all_results = []

        self.log("🔍 Memulai scraping kode AKTIF...")
        soup_active = self.get_soup(self.active_url)
        if soup_active:
            codes = self._parse_table(soup_active, STATUS_ACTIVE)
            self.log(f"Ditemukan {len(codes)} kode aktif.")
            all_results.extend(codes)

        self.log("🔍 Memulai scraping kode HISTORY (Expired)...")
        soup_expired = self.get_soup(self.history_url)
        if soup_expired:
            codes = self._parse_table(soup_expired, STATUS_EXPIRED)
            self.log(f"Ditemukan {len(codes)} kode kadaluarsa.")
            all_results.extend(codes)

        self.save_results(all_results)
