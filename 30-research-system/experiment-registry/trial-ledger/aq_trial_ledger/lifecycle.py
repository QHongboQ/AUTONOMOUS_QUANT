"""Pure derived lifecycle decisions; storage never updates status rows."""

from __future__ import annotations

from collections.abc import Sequence


def latest(events: Sequence[str]) -> str | None:
    """Return the most recent lifecycle fact, if the history is non-empty."""

    return events[-1] if events else None


def actor_active(events: Sequence[str]) -> bool:
    """Only an explicit latest activation makes an identity writable."""

    return latest(events) == "ACTOR_ACTIVATED"


def capability_active(events: Sequence[str]) -> bool:
    """A later revoke supersedes an earlier grant without changing history."""

    return latest(events) == "CAPABILITY_GRANTED"


def policy_active(events: Sequence[str]) -> bool:
    """A retired policy remains visible but cannot admit a new registration."""

    return latest(events) == "FAMILY_POLICY_ACTIVATED"


def legal_execution_transition(current: str | None, event: str) -> bool:
    """Accept exactly the execution transitions defined by the V1 contract."""

    return ((current is None and event == "TRIAL_STARTED") or
            (current == "TRIAL_STARTED" and event in {
                "TRIAL_COMPLETED", "TRIAL_FAILED", "TRIAL_CANCELLED",
            }))
