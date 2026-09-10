from utils.models import Code, Duration, Reward


def test_reward_creation() -> None:
    reward = Reward(name="Primogem x100", image="http://example.com/gem.png")
    assert reward.name == "Primogem x100"
    assert reward.image == "http://example.com/gem.png"


def test_duration_defaults() -> None:
    duration = Duration()
    assert duration.discovered is None
    assert duration.valid is None
    assert duration.expired is None
    assert duration.notes is None


def test_duration_partial() -> None:
    duration = Duration(discovered="2023-01-01", valid="2023-12-31")
    assert duration.discovered == "2023-01-01"
    assert duration.valid == "2023-12-31"
    assert duration.expired is None
    assert duration.notes is None


def test_code_creation() -> None:
    duration = Duration(discovered="2023-01-01")
    rewards = [Reward(name="Mora x10000", image="http://example.com/mora.png")]
    code = Code(
        code="TEST123",
        server="Global",
        status="active",
        rewards=rewards,
        duration=duration,
        link="http://example.com",
    )
    assert code.code == "TEST123"
    assert code.server == "Global"
    assert code.status == "active"
    assert len(code.rewards) == 1
    assert code.rewards[0].name == "Mora x10000"
    assert code.duration.discovered == "2023-01-01"
    assert code.link == "http://example.com"


def test_code_without_link() -> None:
    code = Code(
        code="TEST456",
        server="Asia",
        status="expired",
        rewards=[],
        duration=Duration(),
        link=None,
    )
    assert code.code == "TEST456"
    assert code.link is None
