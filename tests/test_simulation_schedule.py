"""Tests for session-local scheduled simulation timing."""

import pytest

from src.simulation_schedule import (
    acquire_simulation_lease,
    release_simulation_lease,
    renew_simulation_lease,
    schedule_next_simulation_tick,
    simulation_tick_is_due,
)


def test_simulation_tick_runs_only_when_running_and_due():
    due_at = schedule_next_simulation_tick(100.0, 60)

    assert not simulation_tick_is_due("stopped", due_at, 160.0)
    assert not simulation_tick_is_due("paused", due_at, 160.0)
    assert not simulation_tick_is_due("running", due_at, 159.9)
    assert simulation_tick_is_due("running", due_at, 160.0)


def test_rescheduling_prevents_duplicate_tick_on_same_rerun():
    due_at = schedule_next_simulation_tick(100.0, 60)
    assert simulation_tick_is_due("running", due_at, 160.0)

    next_due_at = schedule_next_simulation_tick(160.0, 60)
    assert not simulation_tick_is_due("running", next_due_at, 160.0)
    assert simulation_tick_is_due("running", next_due_at, 220.0)


def test_schedule_rejects_intervals_below_minimum():
    with pytest.raises(ValueError, match="at least 60 seconds"):
        schedule_next_simulation_tick(100.0, 59)


def test_simulation_lease_prevents_a_second_session_from_starting():
    owner_a = "session-a"
    owner_b = "session-b"
    try:
        assert acquire_simulation_lease(owner_a, 100.0, 120)
        assert not acquire_simulation_lease(owner_b, 101.0, 120)
        assert renew_simulation_lease(owner_a, 102.0, 120)
        assert release_simulation_lease(owner_a)
        assert acquire_simulation_lease(owner_b, 103.0, 120)
    finally:
        release_simulation_lease(owner_a)
        release_simulation_lease(owner_b)


def test_expired_simulation_lease_can_be_reclaimed():
    owner_a = "expired-session"
    owner_b = "replacement-session"
    try:
        assert acquire_simulation_lease(owner_a, 100.0, 60)
        assert not renew_simulation_lease(owner_a, 160.0, 60)
        assert acquire_simulation_lease(owner_b, 161.0, 60)
    finally:
        release_simulation_lease(owner_a)
        release_simulation_lease(owner_b)
