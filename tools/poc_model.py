from dataclasses import dataclass
from typing import Iterable


INT32_MAX = 2_147_483_647
MAX_HP_DELTA = 65_535
HP_BITS_DESCENDING = tuple(1 << exponent for exponent in range(15, -1, -1))


class PolicyError(ValueError):
    """The requested POC operation cannot be represented safely."""


@dataclass(frozen=True)
class Policy:
    eligible_size: int
    level_sum: int
    average_level: int
    level_percent: int
    party_percent: int
    clamped: bool

    @property
    def supported(self) -> bool:
        return self.level_percent > 0


def _policy_from_summary(eligible_size: int, average_level: int) -> Policy:
    if eligible_size <= 0:
        raise PolicyError("eligible party size must be positive")
    if average_level <= 0:
        raise PolicyError("average level must be positive")

    capped_size = min(eligible_size, 8)
    return Policy(
        eligible_size=eligible_size,
        level_sum=eligible_size * average_level,
        average_level=average_level,
        level_percent=115 if 5 <= average_level <= 8 else 0,
        party_percent=100 + 20 * (capped_size - 1),
        clamped=eligible_size > 8,
    )


def build_policy(levels: Iterable[int]) -> Policy:
    normalized = tuple(levels)
    if not normalized:
        raise PolicyError("eligible roster cannot be empty")
    if any(not isinstance(level, int) or isinstance(level, bool) or level <= 0 for level in normalized):
        raise PolicyError("eligible member levels must be positive integers")

    level_sum = sum(normalized)
    average_level = level_sum // len(normalized)
    policy = _policy_from_summary(len(normalized), average_level)
    return Policy(
        eligible_size=policy.eligible_size,
        level_sum=level_sum,
        average_level=policy.average_level,
        level_percent=policy.level_percent,
        party_percent=policy.party_percent,
        clamped=policy.clamped,
    )


def target_maximum(base_maximum: int, policy: Policy) -> int:
    if not isinstance(base_maximum, int) or isinstance(base_maximum, bool) or base_maximum <= 0:
        raise PolicyError("base maximum HP must be a positive integer")
    if not policy.supported:
        raise PolicyError("average level is outside the POC tier")

    product = base_maximum * policy.level_percent * policy.party_percent
    if product > INT32_MAX:
        raise PolicyError("maximum HP calculation exceeds signed 32-bit range")

    target = product // 10_000
    if target <= 0:
        raise PolicyError("calculated target maximum HP must be positive")
    return target


def decompose_delta(delta: int) -> list[int]:
    if not isinstance(delta, int) or isinstance(delta, bool):
        raise PolicyError("HP delta must be an integer")
    if delta < 0 or delta > MAX_HP_DELTA:
        raise PolicyError(f"HP delta must be between 0 and {MAX_HP_DELTA}")

    remainder = delta
    bits: list[int] = []
    for bit in HP_BITS_DESCENDING:
        if remainder >= bit:
            bits.append(bit)
            remainder -= bit

    if remainder != 0 or sum(bits) != delta:
        raise PolicyError("HP delta could not be represented exactly")
    return bits


def restore_current(
    old_current: int,
    old_maximum: int,
    new_maximum: int,
    *,
    alive: bool,
) -> int:
    values = (old_current, old_maximum, new_maximum)
    if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
        raise PolicyError("HP values must be integers")
    if old_current < 0:
        raise PolicyError("current HP cannot be negative")
    if old_maximum <= 0 or new_maximum <= 0:
        raise PolicyError("maximum HP values must be positive")
    if old_current > old_maximum:
        raise PolicyError("current HP cannot exceed the captured maximum")
    if not alive:
        return 0

    numerator = old_current * new_maximum * 2 + old_maximum
    denominator = old_maximum * 2
    if numerator > INT32_MAX or denominator > INT32_MAX:
        raise PolicyError("current HP calculation exceeds signed 32-bit range")

    restored = numerator // denominator
    return max(1, min(restored, new_maximum))


def canonical_merge_policy(left: Policy, right: Policy) -> Policy:
    return _policy_from_summary(
        max(left.eligible_size, right.eligible_size),
        max(left.average_level, right.average_level),
    )
