from dataclasses import dataclass
from typing import Any, Iterable, Mapping


INT32_MAX = 2_147_483_647
MAX_HP_DELTA = 65_535
HP_BITS_DESCENDING = tuple(1 << exponent for exponent in range(15, -1, -1))


class PolicyError(ValueError):
    """The requested POC operation cannot be represented safely."""


@dataclass(frozen=True)
class Policy:
    eligible_size: int
    effective_size: int
    level_sum: int
    average_level: int
    hardened_tier: int
    target_hp_percent: int
    attack_save_dc_bonus: int
    ac_bonus: int
    action_budget: int
    bonus_action_budget: int
    recipient_cap: int
    clamped: bool

    @property
    def supported(self) -> bool:
        return 1 <= self.hardened_tier <= 6

    @property
    def relentless_i_recipients(self) -> int:
        return self.action_budget - self.bonus_action_budget

    @property
    def relentless_ii_recipients(self) -> int:
        return self.bonus_action_budget


@dataclass(frozen=True)
class HpTransactionPlan:
    target_maximum: int
    delta: int
    bits: tuple[int, ...]
    restored_current: int
    outcome: str

    @property
    def total_status(self) -> str | None:
        """Exact representation-2 status; bits remain available for legacy readers."""
        return f"AESN_HP_TOTAL_{self.delta}" if self.delta > 0 else None


@dataclass(frozen=True)
class HardenedRefreshPlan:
    external_base: int
    target_maximum: int
    delta: int
    bits: tuple[int, ...]
    restored_current: int


@dataclass(frozen=True)
class WorldHardenedDecision:
    action: str
    reason: str


@dataclass(frozen=True)
class MergeResult:
    aliases: dict[str, str]
    snapshots: dict[str, Policy]
    enemy_owners: dict[str, str]
    mismatch_count: int


@dataclass(frozen=True)
class ReloadDecision:
    action: str
    reason: str
    mutate: bool


@dataclass(frozen=True)
class RelentlessCandidate:
    identity: str
    priority: int
    action_points: float = 1.0
    bonus_action_points: float = 1.0


@dataclass(frozen=True)
class RelentlessRecipient:
    identity: str
    tier: int


def _policy_from_summary(eligible_size: int, average_level: int) -> Policy:
    if eligible_size <= 0:
        raise PolicyError("eligible party size must be positive")
    if average_level <= 0:
        raise PolicyError("average level must be positive")

    effective_size = min(eligible_size, 12)
    effective_level = min(average_level, 20)

    if effective_level <= 4:
        hardened_tier, base_hp_percent, stat_bonus, ac_bonus = (1, 125, 1, 0)
        level_action_budget, level_bonus_budget = (0, 0)
    elif effective_level <= 8:
        hardened_tier, base_hp_percent, stat_bonus, ac_bonus = (2, 150, 2, 1)
        level_action_budget, level_bonus_budget = (1, 0)
    elif effective_level <= 12:
        hardened_tier, base_hp_percent, stat_bonus, ac_bonus = (3, 180, 3, 1)
        level_action_budget, level_bonus_budget = (1, 0)
    elif effective_level <= 16:
        hardened_tier, base_hp_percent, stat_bonus, ac_bonus = (4, 220, 4, 2)
        level_action_budget, level_bonus_budget = (1, 1)
    elif effective_level <= 18:
        hardened_tier, base_hp_percent, stat_bonus, ac_bonus = (5, 260, 5, 2)
        level_action_budget, level_bonus_budget = (2, 1)
    else:
        hardened_tier, base_hp_percent, stat_bonus, ac_bonus = (6, 300, 6, 3)
        level_action_budget, level_bonus_budget = (2, 2)

    target_hp_percent = base_hp_percent + 20 * (effective_size - 1)

    if effective_size <= 2:
        action_budget = 1 if hardened_tier >= 2 else 0
        bonus_action_budget = 0
        recipient_cap = action_budget
    else:
        size_above_four = max(0, effective_size - 4)
        recipient_cap = min(6, effective_size - 2)
        action_budget = min(
            recipient_cap,
            level_action_budget + size_above_four,
        )
        bonus_action_budget = min(
            action_budget,
            level_bonus_budget + size_above_four // 2,
        )

    return Policy(
        eligible_size=eligible_size,
        effective_size=effective_size,
        level_sum=eligible_size * average_level,
        average_level=average_level,
        hardened_tier=hardened_tier,
        target_hp_percent=target_hp_percent,
        attack_save_dc_bonus=stat_bonus,
        ac_bonus=ac_bonus,
        action_budget=action_budget,
        bonus_action_budget=bonus_action_budget,
        recipient_cap=recipient_cap,
        clamped=eligible_size > 12 or average_level > 20,
    )


def policy_from_summary(eligible_size: int, average_level: int) -> Policy:
    """Build the canonical policy when only persisted summary fields exist."""
    return _policy_from_summary(eligible_size, average_level)


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
        effective_size=policy.effective_size,
        level_sum=level_sum,
        average_level=policy.average_level,
        hardened_tier=policy.hardened_tier,
        target_hp_percent=policy.target_hp_percent,
        attack_save_dc_bonus=policy.attack_save_dc_bonus,
        ac_bonus=policy.ac_bonus,
        action_budget=policy.action_budget,
        bonus_action_budget=policy.bonus_action_budget,
        recipient_cap=policy.recipient_cap,
        clamped=policy.clamped,
    )


def select_relentless_recipients(
    candidates: Iterable[RelentlessCandidate],
    *,
    action_budget: int,
    bonus_action_budget: int,
    recipient_cap: int,
) -> tuple[RelentlessRecipient, ...]:
    """Allocate frozen Relentless budgets to highest-priority safe candidates."""
    ordered = sorted(candidates, key=lambda candidate: candidate.priority, reverse=True)
    recipients: list[RelentlessRecipient] = []
    action_spent = 0
    bonus_action_spent = 0

    for candidate in ordered:
        if action_spent >= action_budget or len(recipients) >= recipient_cap:
            break
        if candidate.action_points > 1.0 or candidate.bonus_action_points > 1.0:
            continue

        tier = 2 if bonus_action_spent < bonus_action_budget else 1
        recipients.append(RelentlessRecipient(candidate.identity, tier))
        action_spent += 1
        if tier == 2:
            bonus_action_spent += 1

    return tuple(recipients)


def target_maximum(base_maximum: int, policy: Policy) -> int:
    if not isinstance(base_maximum, int) or isinstance(base_maximum, bool) or base_maximum <= 0:
        raise PolicyError("base maximum HP must be a positive integer")
    if not policy.supported:
        raise PolicyError("average level is outside the POC tier")

    product = base_maximum * policy.target_hp_percent
    if product > INT32_MAX:
        raise PolicyError("maximum HP calculation exceeds signed 32-bit range")

    target = product // 100
    if target <= 0:
        raise PolicyError("calculated target maximum HP must be positive")
    return target


def plan_hardened_refresh(
    observed_current: int,
    observed_maximum: int,
    owned_applied_sum: int,
    policy: Policy,
    *,
    alive: bool,
) -> HardenedRefreshPlan:
    values = (observed_current, observed_maximum, owned_applied_sum)
    if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
        raise PolicyError("observed HP values and owned HP must be integers")
    if observed_maximum <= 0:
        raise PolicyError("observed maximum HP must be positive")
    if observed_current < 0 or observed_current > observed_maximum:
        raise PolicyError("observed current HP must be within the observed maximum")
    if owned_applied_sum < 0 or owned_applied_sum >= observed_maximum:
        raise PolicyError("owned HP must leave a positive external base")

    external_base = observed_maximum - owned_applied_sum
    target = target_maximum(external_base, policy)
    delta = target - external_base
    bits = tuple(decompose_delta(delta))
    restored = restore_current(
        observed_current,
        observed_maximum,
        target,
        alive=alive,
    )
    return HardenedRefreshPlan(
        external_base=external_base,
        target_maximum=target,
        delta=delta,
        bits=bits,
        restored_current=restored,
    )


def decide_world_hardened(
    *,
    tracked: bool,
    committed: bool,
    in_combat: bool,
    alive: bool,
    active: bool,
    on_stage: bool,
    invisible: bool,
    hostile: bool,
) -> WorldHardenedDecision:
    if in_combat:
        return WorldHardenedDecision("defer", "active combat freezes Hardened")

    # Visibility, range, and hostility are discovery gates. Once the complete
    # world-owned package commits, only an explicit policy replan or a
    # fail-closed transaction path may mutate it.
    if tracked and committed:
        return WorldHardenedDecision("retain", "committed world target is sticky")
    if tracked:
        return WorldHardenedDecision("wait", "world transaction is still pending")

    eligible = (
        alive
        and active
        and on_stage
        and not invisible
        and hostile
    )
    if eligible:
        return WorldHardenedDecision("apply", "new eligible world target")
    return WorldHardenedDecision("ignore", "untracked target is not eligible")


def should_reconsider_rejected_hostile(
    *,
    rejected_reason: str,
    still_in_combat: bool,
    hostile_to_participant: bool,
) -> bool:
    return (
        rejected_reason == "HostileToNoParticipant"
        and still_in_combat
        and hostile_to_participant
    )


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


def plan_hp_target(
    current: int,
    base_maximum: int,
    target: int,
    *,
    alive: bool,
) -> HpTransactionPlan:
    """Validate one immutable target and describe exact total and legacy bit representations."""
    values = (current, base_maximum, target)
    if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
        raise PolicyError("HP values must be integers")
    if current < 0:
        raise PolicyError("current HP cannot be negative")
    if base_maximum <= 0 or target <= 0:
        raise PolicyError("maximum HP values must be positive")
    if current > base_maximum:
        raise PolicyError("current HP cannot exceed the captured maximum")

    if not alive or current == 0:
        return HpTransactionPlan(
            target_maximum=target,
            delta=0,
            bits=(),
            restored_current=0,
            outcome="skip_dead",
        )

    delta = target - base_maximum
    bits = tuple(decompose_delta(delta))
    restored = restore_current(
        current,
        base_maximum,
        target,
        alive=True,
    )
    return HpTransactionPlan(
        target_maximum=target,
        delta=delta,
        bits=bits,
        restored_current=restored,
        outcome="no_change" if delta == 0 else "planned",
    )


def canonical_merge_policy(left: Policy, right: Policy) -> Policy:
    return _policy_from_summary(
        max(left.eligible_size, right.eligible_size),
        max(left.average_level, right.average_level),
    )


def resolve_combat_owner(aliases: Mapping[str, str], combat: str) -> str:
    """Resolve a discarded combat through every alias to its final survivor."""
    current = combat
    visited: set[str] = set()
    while current in aliases:
        if current in visited:
            raise PolicyError("combat alias cycle detected")
        visited.add(current)
        current = aliases[current]
    return current


def reconcile_merge_case(case: Mapping[str, Any]) -> MergeResult:
    """Deterministic oracle for mark-before-migrate combat ownership."""
    snapshots = {
        combat: policy_from_summary(
            int(summary["eligibleSize"]),
            int(summary["averageLevel"]),
        )
        for combat, summary in case.get("snapshots", {}).items()
    }
    enemy_owners: dict[str, str] = {}
    for combat, enemies in case.get("enemies", {}).items():
        for enemy in enemies:
            if enemy in enemy_owners:
                raise PolicyError(f"enemy has multiple combat owners: {enemy}")
            enemy_owners[str(enemy)] = str(combat)

    aliases: dict[str, str] = {}
    mismatch_count = 0
    for raw_old, raw_new in case.get("merges", []):
        old = resolve_combat_owner(aliases, str(raw_old))
        new = resolve_combat_owner(aliases, str(raw_new))
        if old == new:
            continue

        left = snapshots.get(old)
        right = snapshots.get(new)
        if left is not None and right is not None:
            if (
                left.eligible_size != right.eligible_size
                or left.average_level != right.average_level
            ):
                mismatch_count += 1
            canonical = canonical_merge_policy(left, right)
        else:
            canonical = left if left is not None else right

        # Mark first. Cleanup sees the alias before any ownership row moves.
        aliases[old] = new
        snapshots.pop(old, None)
        if canonical is not None:
            snapshots[new] = canonical
        for enemy, owner in tuple(enemy_owners.items()):
            if resolve_combat_owner(aliases, owner) == new:
                enemy_owners[enemy] = new

    return MergeResult(
        aliases=aliases,
        snapshots=snapshots,
        enemy_owners=enemy_owners,
        mismatch_count=mismatch_count,
    )


def cleanup_commands(result: MergeResult, combat: str) -> tuple[str, ...]:
    """Return unique final-owner cleanup targets; discarded ends are no-ops."""
    if combat in result.aliases:
        return ()
    final = resolve_combat_owner(result.aliases, combat)
    if final != combat:
        return ()
    return tuple(
        sorted(
            enemy
            for enemy, owner in result.enemy_owners.items()
            if resolve_combat_owner(result.aliases, owner) == final
        )
    )


def reconcile_reload_state(
    *,
    combat_active: bool,
    schema_version: int,
    hp_state: str,
    component_state: str | None,
    identities_valid: bool,
) -> ReloadDecision:
    """Choose the sole allowed recovery path for one persisted application."""
    if schema_version != 2:
        return ReloadDecision("cleanup", "UnsupportedSchema", True)
    if not identities_valid:
        return ReloadDecision("cleanup", "IdentityMismatch", True)

    fully_committed = (
        hp_state == "HPCommitted"
        and component_state == "FullyCommitted"
    )
    if not combat_active:
        return ReloadDecision("cleanup", "InactiveCombat", True)
    if fully_committed:
        return ReloadDecision("retain", "ValidActiveCommit", False)
    return ReloadDecision("rollback", "PendingApplication", True)
