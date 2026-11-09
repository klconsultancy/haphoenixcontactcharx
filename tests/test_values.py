from aiophoenixcontactcharx import ErrorCode, VehicleStatus

from custom_components.phoenixcontact_charx.values import (
    error_code_hex,
    nullable_round,
    vehicle_status_key,
)


def test_nullable_round() -> None:
    assert nullable_round(1.2345, 2) == 1.23
    assert nullable_round(None, 2) is None
    assert nullable_round(0.0, 1) == 0.0


def test_vehicle_status_key() -> None:
    assert vehicle_status_key(VehicleStatus.C2) == "c2"
    assert vehicle_status_key(VehicleStatus.IN) == "in"
    assert vehicle_status_key(None) is None


def test_error_code_hex() -> None:
    assert error_code_hex(ErrorCode.RFID_READER_ERROR) == "0x00000040"
    assert error_code_hex(ErrorCode(0)) == "0x00000000"
    assert error_code_hex(ErrorCode(1 << 31)) == "0x80000000"
    assert error_code_hex(None) is None
