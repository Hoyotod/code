from .constants import STATUS_ACTIVE, STATUS_EXPIRED
from .models import Code
from .scraper_base import ScraperBase


class ZZZScraper(ScraperBase):
    def __init__(self):
        super().__init__(game_name="Zenless Zone Zero", game_color="yellow", folder_name="zzz")
        self.active_url = "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code"
        self.history_url = "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code/History"

    def _parse_table(self, soup, status: str) -> list[Code]:
        codes = []
        if not soup:
            return codes

        content = soup.find("div", class_="mw-parser-output")
        if not content:
            return codes

        table = content.find("table", class_="wikitable")
        if not table:
            return codes

        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            code_tags = cols[0].find_all("code")
            if not code_tags:
                continue

            server = cols[1].get_text(strip=True)
            rewards = self._extract_rewards(cols[2])
            duration_txt = cols[3].get_text(separator=" ", strip=True)
            duration = self._extract_duration(duration_txt)

            for code_tag in code_tags:
                code_txt = code_tag.get_text(strip=True)
                code_clean = self._clean_code(code_txt)

                if not code_clean:
                    continue

                codes.append(
                    Code(
                        code=code_clean,
                        server=server,
                        status=status,
                        rewards=rewards,
                        duration=duration,
                    )
                )

        return codes

    def scrape(self):
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
