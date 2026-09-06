# utils/starrail_scraper.py
from .constants import STATUS_ACTIVE, STATUS_EXPIRED
from .models import Code
from .scraper_base import ScraperBase


class StarrailScraper(ScraperBase):
    def __init__(self):
        super().__init__(game_name="Honkai Starrail", game_color="magenta", folder_name="starrail")
        self.url = "https://honkai-star-rail.fandom.com/wiki/Redemption_Code"

    def scrape(self):
        self.log("🔍 Memulai scraping...")
        soup = self.get_soup(self.url)
        results = []

        if soup:
            content = soup.find("div", class_="mw-parser-output")
            if content:
                table = content.find("table", class_="wikitable")

                if table:
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

                        duration_raw_txt = cols[3].get_text(strip=True)
                        duration = self._extract_duration(duration_raw_txt)

                        status = STATUS_ACTIVE

                        if duration.expired:
                            status = STATUS_EXPIRED
                        elif duration.valid and "Unknown" in duration.valid:
                            status = STATUS_ACTIVE
                        elif "Expired" in duration_raw_txt or "expired" in duration_raw_txt.lower():
                            status = STATUS_EXPIRED

                        for code_tag in code_tags:
                            code_txt = code_tag.get_text(strip=True)
                            code_clean = self._clean_code(code_txt)

                            if not code_clean:
                                continue

                            results.append(
                                Code(
                                    code=code_clean,
                                    server=server,
                                    status=status,
                                    rewards=rewards,
                                    duration=duration,
                                )
                            )

            self.log(f"Total kode ditemukan: {len(results)}")
            self.save_results(results)
