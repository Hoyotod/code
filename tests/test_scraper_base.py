from utils.models import Duration
from utils.scraper_base import ScraperBase


class MockScraper(ScraperBase):
    def __init__(self):
        super().__init__(game_name="Test Game", game_color="cyan", folder_name="test")

    def scrape(self):
        pass


def test_clean_code():
    scraper = MockScraper()
    assert scraper._clean_code("ABC123") == "ABC123"
    assert scraper._clean_code("abc-123") == "ABC123"
    assert scraper._clean_code("test_code!@#") == "TESTCODE"
    assert scraper._clean_code("") == ""
    assert scraper._clean_code("lower123") == "LOWER123"


def test_extract_duration():
    scraper = MockScraper()

    text1 = "Discovered: 2023-01-01 Valid: 2023-12-31"
    duration1 = scraper._extract_duration(text1)
    assert duration1.discovered == "2023-01-01"
    assert duration1.valid == "2023-12-31"
    assert duration1.expired is None

    text2 = "Expired: 2023-06-01 Note: Limited time"
    duration2 = scraper._extract_duration(text2)
    assert duration2.expired == "2023-06-01"
    assert duration2.notes == "Limited time"

    text3 = ""
    duration3 = scraper._extract_duration(text3)
    assert duration3.discovered is None
    assert duration3.valid is None
    assert duration3.expired is None


def test_normalize_code_data():
    scraper = MockScraper()

    data1 = [{"code": "ABC", "status": "active"}, {"code": "XYZ", "status": "expired"}]
    data2 = [{"status": "active", "code": "ABC"}, {"status": "expired", "code": "XYZ"}]

    normalized1 = scraper._normalize_code_data(data1)
    normalized2 = scraper._normalize_code_data(data2)

    assert normalized1 == normalized2


def test_build_webhook_payload():
    from utils.constants import COLOR_ACTIVE, STATUS_ACTIVE
    from utils.models import Code, Reward

    scraper = MockScraper()

    code = Code(
        code="TEST123",
        server="Global",
        status=STATUS_ACTIVE,
        rewards=[Reward(name="Primogem x100", image="http://example.com/gem.png")],
        duration=Duration(),
    )

    payload = scraper.build_webhook_payload(code)

    assert "embeds" in payload
    assert len(payload["embeds"]) == 1
    embed = payload["embeds"][0]
    assert embed["title"] == "TEST123"
    assert embed["color"] == COLOR_ACTIVE
    assert "Primogem x100" in embed["fields"][0]["value"]
