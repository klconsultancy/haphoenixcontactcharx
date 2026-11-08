# Security policy

## Supported versions

Only the latest release receives security fixes.

## Reporting a vulnerability

Report vulnerabilities privately through [GitHub's private vulnerability reporting](https://github.com/klconsultancy/haphoenixcontactcharx/security/advisories/new), not in a public issue.

Include what an attacker can do, the steps to reproduce it, and the affected version or commit. You will get an answer within a week. Once a fix is released, the advisory is published with credit to you unless you prefer otherwise.

The integration talks Modbus/TCP to a CHARX controller, which has no authentication of its own, and its switches and numbers can release charging and change the charging current. Issues that let a user without the matching Home Assistant permissions change those, or that make an entity misreport the controller's state, are treated as the most severe.
