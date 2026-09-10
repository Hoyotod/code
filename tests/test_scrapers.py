from unittest.mock import patch

from bs4 import BeautifulSoup

from utils.constants import STATUS_ACTIVE, STATUS_EXPIRED
from utils.genshin_scraper import GenshinScraper
from utils.starrail_scraper import StarrailScraper
from utils.zzz_scraper import ZZZScraper


def test_genshin_scraper_initialization() -> None:
    scraper = GenshinScraper()
    assert scraper.game_name == "Genshin Impact"
    assert scraper.game_color == "blue"
    assert scraper.game_folder == "genshin"
    assert scraper.active_url == "https://genshin-impact.fandom.com/wiki/Promotional_Code"
    assert (
        scraper.history_url == "https://genshin-impact.fandom.com/wiki/Promotional_Code/History"
    )


def test_genshin_parse_table_empty() -> None:
    scraper = GenshinScraper()
    result = scraper._parse_table(None, STATUS_ACTIVE)
    assert result == []


def test_genshin_parse_table_with_code() -> None:
    scraper = GenshinScraper()
    html = """
    <div class="mw-parser-output">
        <table class="wikitable">
            <tr><th>Code</th><th>Server</th><th>Rewards</th><th>Duration</th></tr>
            <tr>
                <td><code>TEST123</code></td>
                <td>Global</td>
                <td>
                    <span class="item">
                        <span class="item-text">Primogem x100</span>
                        <img src="http://example.com/gem.png"/>
                    </span>
                </td>
                <td>Discovered: 2023-01-01 Valid: 2023-12-31</td>
            </tr>
        </table>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    codes = scraper._parse_table(soup, STATUS_ACTIVE)
    assert len(codes) == 1
    assert codes[0].code == "TEST123"
    assert codes[0].server == "Global"
    assert codes[0].status == STATUS_ACTIVE
    assert len(codes[0].rewards) == 1
    assert codes[0].rewards[0].name == "Primogem x100"


def test_starrail_scraper_initialization() -> None:
    scraper = StarrailScraper()
    assert scraper.game_name == "Honkai Starrail"
    assert scraper.game_color == "magenta"
    assert scraper.game_folder == "starrail"
    assert scraper.url == "https://honkai-star-rail.fandom.com/wiki/Redemption_Code"


def test_zzz_scraper_initialization() -> None:
    scraper = ZZZScraper()
    assert scraper.game_name == "Zenless Zone Zero"
    assert scraper.game_color == "yellow"
    assert scraper.game_folder == "zzz"
    assert scraper.active_url == "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code"
    assert scraper.history_url == "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code/History"


def test_zzz_parse_table_empty() -> None:
    scraper = ZZZScraper()
    result = scraper._parse_table(None, STATUS_ACTIVE)
    assert result == []


def test_zzz_parse_table_with_multiple_codes() -> None:
    scraper = ZZZScraper()
    html = """
    <div class="mw-parser-output">
        <table class="wikitable">
            <tr><th>Code</th><th>Server</th><th>Rewards</th><th>Duration</th></tr>
            <tr>
                <td><code>CODE1</code><code>CODE2</code></td>
                <td>All</td>
                <td>
                    <span class="item">
                        <span class="item-text">Polychrome x60</span>
                    </span>
                </td>
                <td>Valid: Unknown</td>
            </tr>
        </table>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    codes = scraper._parse_table(soup, STATUS_ACTIVE)
    assert len(codes) == 2
    assert codes[0].code == "CODE1"
    assert codes[1].code == "CODE2"
    assert codes[0].server == "All"


def test_scraper_with_missing_columns() -> None:
    scraper = GenshinScraper()
    html = """
    <div class="mw-parser-output">
        <table class="wikitable">
            <tr><th>Code</th><th>Server</th></tr>
            <tr>
                <td><code>INVALID</code></td>
                <td>Global</td>
            </tr>
        </table>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    codes = scraper._parse_table(soup, STATUS_ACTIVE)
    assert len(codes) == 0


def test_starrail_status_detection() -> None:
    scraper = StarrailScraper()
    html = """
    <div class="mw-parser-output">
        <table class="wikitable">
            <tr><th>Code</th><th>Server</th><th>Rewards</th><th>Duration</th></tr>
            <tr>
                <td><code>EXPIRED1</code></td>
                <td>Global</td>
                <td><span class="item"><span class="item-text">Stellar Jade x50</span></span></td>
                <td>Expired: 2023-01-01</td>
            </tr>
        </table>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    with (
        patch.object(scraper, 'get_soup', return_value=soup),
        patch.object(scraper, 'save_results') as mock_save,
    ):
        scraper.scrape()
        mock_save.assert_called_once()
        codes = mock_save.call_args[0][0]
        assert len(codes) == 1
        assert codes[0].status == STATUS_EXPIRED
