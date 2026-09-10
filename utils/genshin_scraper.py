from bs4 import BeautifulSoup

from .constants import STATUS_ACTIVE, STATUS_EXPIRED
from .models import Code
from .scraper_base import ScraperBase


class GenshinScraper(ScraperBase):
    def __init__(self) -> None:
        super().__init__(game_name="Genshin Impact", game_color="blue", folder_name="genshin")
        self.active_url = "https://genshin-impact.fandom.com/wiki/Promotional_Code"
        self.history_url = "https://genshin-impact.fandom.com/wiki/Promotional_Code/History"

    def _parse_table(self, soup: BeautifulSoup | None, status: str) -> list[Code]:
        codes: list[Code] = []
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

            duration_cell = cols[3]
            for mobile_elem in duration_cell.find_all(class_="mobile-only"):
                mobile_elem.decompose()
            duration_txt = duration_cell.get_text(separator=" ", strip=True)
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
