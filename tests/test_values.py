"""Unit tests for pure value-extraction helpers in values.py."""

from __future__ import annotations

import pytest

from custom_components.phoenixcontact_charx.values import (
    error_code_hex,
    meter_reading_kwh,
    nullable_round,
    vehicle_status_key,
)

from tests.conftest import fake_cp_data


# ---------------------------------------------------------------------------
# nullable_round
# ---------------------------------------------------------------------------

def test_nullable_round_none_returns_none():
    assert nullable_round(None, 2) is None


def test_nullable_round_rounds_to_ndigits():
    assert nullable_round(1.2345, 2) == 1.23


def test_nullable_round_zero_is_not_none():
    assert nullable_round(0.0, 2) == 0.0


def test_nullable_round_negative():
    assert nullable_round(-3.567, 1) == -3.6


# ---------------------------------------------------------------------------
# vehicle_status_key
# ---------------------------------------------------------------------------

def test_vehicle_status_key_lowercases():
    cp = fake_cp_data(vehicle_status="C2")
    assert vehicle_status_key(cp) == "c2"


def test_vehicle_status_key_none_when_empty():
    cp = fake_cp_data(vehicle_status="")
    assert vehicle_status_key(cp) is None


def test_vehicle_status_key_already_lower():
    cp = fake_cp_data(vehicle_status="a1")
    assert vehicle_status_key(cp) == "a1"


# ---------------------------------------------------------------------------
# error_code_hex
# ---------------------------------------------------------------------------

def test_error_code_hex_zero():
    cp = fake_cp_data(error_code=0)
    assert error_code_hex(cp) == "0x00000000"


def test_error_code_hex_one():
    cp = fake_cp_data(error_code=1)
    assert error_code_hex(cp) == "0x00000001"


def test_error_code_hex_large():
    cp = fake_cp_data(error_code=0xDEADBEEF)
    assert error_code_hex(cp) == "0xDEADBEEF"


def test_error_code_hex_uppercase():
    cp = fake_cp_data(error_code=0xABCDEF12)
    assert error_code_hex(cp) == "0xABCDEF12"


# ---------------------------------------------------------------------------
# meter_reading_kwh (issue #38)
# ---------------------------------------------------------------------------

def test_meter_reading_kwh_converts_and_rounds():
    assert meter_reading_kwh(fake_cp_data(energy_active_wh=10_450_504)) == 10450.504


def test_meter_reading_kwh_zero_is_none():
    """A lifetime meter reading of 0 means 'not yet read', never a real value."""
    assert meter_reading_kwh(fake_cp_data(energy_active_wh=0)) is None


def test_meter_reading_kwh_reconnect_sequence_never_yields_zero():
    readings = [10_450_504, 0, 10_450_504]
    values = [meter_reading_kwh(fake_cp_data(energy_active_wh=wh)) for wh in readings]
    assert values == [10450.504, None, 10450.504]
