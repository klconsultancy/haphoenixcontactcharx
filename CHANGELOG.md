# Changelog

## [2.0.0](https://github.com/klconsultancy/haphoenixcontactcharx/compare/v1.0.2...v2.0.0) (2026-11-10)

Upgrading from 1.x: these notes cover everything since 1.0.2, including 2.0.0-rc.1. **Your entities, entity IDs and history stay as they are**: every unique ID is unchanged, and no reconfiguration is needed.

### ⚠ BREAKING CHANGES

* **requires Home Assistant 2026.10 or later.** The integration now uses Home Assistant's own Modbus connection (the `modbus` integration's connection handling), so HACS won't offer 2.0.0 on older versions.
* **The Charging Release and Available switches are unavailable unless the charging point's release mode is Modbus.** In any other mode (OCPP, Permanent, Whitelist) the controller ignores those writes; 1.x showed switches that did nothing. The log names the release mode. With an OCPP backend, use **Group Dynamic Max Current** to limit the current: it works in every release mode.
* Another integration that uses the same controller address with different Modbus settings now makes setup fail with a clear error ("connection in use"), instead of the two fighting over the connection.

### Features

* run on aiophoenixcontactcharx 2.0 and Home Assistant's modbus connection ([#48](https://github.com/klconsultancy/haphoenixcontactcharx/issues/48)) ([eba42ea](https://github.com/klconsultancy/haphoenixcontactcharx/commit/eba42eacd4d0fffcbc59c04d6980a3b18d4831a7))
  * **availability per part:** when one charging point stops answering, only its own entities become unavailable, not the whole controller. The log says when a part fails and when it is back.
  * **new button "Clear Group Dynamic Max Current"** removes the dynamic limit again; the number can set a limit but couldn't clear it.
  * a write returns once the controller reports the new value, and every entity shows it right away.
  * the device model is "CHARX SEC"; the hub's name and firmware version follow the controller.

### Bug Fixes

* show the Max Current number as unknown while the controller reads 0 ([#51](https://github.com/klconsultancy/haphoenixcontactcharx/issues/51)) ([16ea6e4](https://github.com/klconsultancy/haphoenixcontactcharx/commit/16ea6e4ef954c4831477df733055f4c50757d571)), as it does in release mode OCPP
* the vehicle status sensor knows states D1 and D2 (vehicle with ventilation); a charging point in status D no longer fails the sensor ([#48](https://github.com/klconsultancy/haphoenixcontactcharx/issues/48))
* setup waits and retries while the controller still reports no charging points, as right after it starts ([#48](https://github.com/klconsultancy/haphoenixcontactcharx/issues/48))

### Dependencies

* aiophoenixcontactcharx 2.0.0 ([release notes](https://github.com/klconsultancy/aiophoenixcontactcharx/releases/tag/v2.0.0))

## [2.0.0-rc.1](https://github.com/klconsultancy/haphoenixcontactcharx/compare/v1.0.2...v2.0.0-rc.1) (2026-11-09)


### ⚠ BREAKING CHANGES

* requires Home Assistant 2026.10 or later.

### Features

* run on aiophoenixcontactcharx 2.0 and Home Assistant's modbus connection ([#48](https://github.com/klconsultancy/haphoenixcontactcharx/issues/48)) ([eba42ea](https://github.com/klconsultancy/haphoenixcontactcharx/commit/eba42eacd4d0fffcbc59c04d6980a3b18d4831a7))

## [1.0.2](https://github.com/klconsultancy/haphoenixcontactcharx/compare/v1.0.1...v1.0.2) (2026-11-08)


### Bug Fixes

* pin aiophoenixcontactcharx to 1.0.0 ([#46](https://github.com/klconsultancy/haphoenixcontactcharx/issues/46)) ([9a3d0b6](https://github.com/klconsultancy/haphoenixcontactcharx/commit/9a3d0b624323bb441dfb444907a898cd24505581))

## [1.0.1](https://github.com/klconsultancy/haphoenixcontactcharx/compare/v1.0.0...v1.0.1) (2026-11-08)


### Bug Fixes

* don't publish 0 kWh total energy after a reconnect ([3d04812](https://github.com/klconsultancy/haphoenixcontactcharx/commit/3d0481258a366a636f02164535301fa349fba6c3))
* replace deprecated via_device with via_device_id for charging point devices ([963eeaa](https://github.com/klconsultancy/haphoenixcontactcharx/commit/963eeaaf0f7845f92c797a18af1aaaa4bab5d6a1))
