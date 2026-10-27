from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Reward:
    """Represents an in-game reward item."""

    name: str
    image: str


@dataclass
class Duration:
    """Represents the validity period of a code."""

    discovered: str | None = None
    valid: str | None = None
    expired: str | None = None
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: Any) -> Duration:
        """Build Duration from a dict, falling back to empty on error."""
        if not isinstance(data, dict):
            return cls()
        try:
            return cls(**data)
        except (TypeError, ValueError):
            return cls()


@dataclass
class Code:
    """Represents a single promotional code."""

    code: str
    server: str
    status: str
    rewards: list[Reward]
    duration: Duration
    link: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Code | None:
        """Reconstruct a Code from a serialized dict. Returns None on bad data."""
        code_str = d.get("code", "")
        if not code_str:
            return None

        rewards = []
        for r in d.get("rewards", []) or []:
            try:
                rewards.append(Reward(**r))
            except (TypeError, ValueError):
                continue

        duration = Duration.from_dict(d.get("duration") or {})

        return cls(
            code=code_str,
            server=d.get("server", ""),
            status=d.get("status", ""),
            rewards=rewards,
            duration=duration,
            link=d.get("link"),
        )
