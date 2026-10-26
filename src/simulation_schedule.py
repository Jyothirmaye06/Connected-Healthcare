"""Small timing helpers for the session-scoped dashboard simulator."""

import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.synthetic_generator import simulate_next_observation

_SIMULATION_LEASE_LOCK = threading.Lock()
_SIMULATION_LEASE_OWNER: Optional[str] = None
_SIMULATION_LEASE_EXPIRES_AT = 0.0


def simulation_tick_is_due(
    status: str,
    next_tick_at: Optional[float],
    now: float,
) -> bool:
    """Returns whether a running simulation has reached its next scheduled tick."""
    return status == "running" and next_tick_at is not None and now >= next_tick_at


def schedule_next_simulation_tick(now: float, interval_seconds: int) -> float:
    """Returns the monotonic deadline for the next simulation tick."""
    if interval_seconds < 60:
        raise ValueError("Simulation interval must be at least 60 seconds.")
    return now + interval_seconds


def acquire_simulation_lease(owner: str, now: float, lease_seconds: int) -> bool:
    """Claims the process-wide simulator lease unless another session owns it."""
    global _SIMULATION_LEASE_OWNER, _SIMULATION_LEASE_EXPIRES_AT
    with _SIMULATION_LEASE_LOCK:
        if (
            _SIMULATION_LEASE_OWNER is not None
            and _SIMULATION_LEASE_OWNER != owner
            and now < _SIMULATION_LEASE_EXPIRES_AT
        ):
            return False
        _SIMULATION_LEASE_OWNER = owner
        _SIMULATION_LEASE_EXPIRES_AT = now + lease_seconds
        return True


def renew_simulation_lease(owner: str, now: float, lease_seconds: int) -> bool:
    """Renews the lease only for its current owner and before it expires."""
    global _SIMULATION_LEASE_EXPIRES_AT
    with _SIMULATION_LEASE_LOCK:
        if (
            owner != _SIMULATION_LEASE_OWNER
            or now >= _SIMULATION_LEASE_EXPIRES_AT
        ):
            return False
        _SIMULATION_LEASE_EXPIRES_AT = now + lease_seconds
        return True


def release_simulation_lease(owner: str) -> bool:
    """Releases the simulator lease if the caller currently owns it."""
    global _SIMULATION_LEASE_OWNER, _SIMULATION_LEASE_EXPIRES_AT
    with _SIMULATION_LEASE_LOCK:
        if owner != _SIMULATION_LEASE_OWNER:
            return False
        _SIMULATION_LEASE_OWNER = None
        _SIMULATION_LEASE_EXPIRES_AT = 0.0
        return True


def simulate_selected_hospitals(
    hospital_ids: Sequence[int],
    db_path: Optional[Path] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Adds one simulated observation per selected hospital and reports partial failures."""
    generated = []
    errors = []
    for hospital_id in hospital_ids:
        try:
            generated.append(
                simulate_next_observation(int(hospital_id), db_path=db_path)
            )
        except (sqlite3.Error, ValueError) as ex:
            errors.append(f"Hospital ID {hospital_id}: {ex}")
    return generated, errors
