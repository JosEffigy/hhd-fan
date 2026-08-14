Exit code: 0
Wall time: 0.4 seconds
Output:
# hhd-fan

`hhd-fan` is an intentionally narrow fork of [Handheld Daemon (hhd)](https://github.com/hhd-dev/hhd). It is being reduced to safe, hardware-supported fan control plus a fan-only overlay surface.

This is not a generic fan-control utility. It writes device-specific Linux hwmon/EC interfaces and must only manage hardware that it positively recognizes. Unsupported hardware remains untouched.

## Current architecture

- **adjustor** supplies the device-specific fan backends and fan-curve logic used by hhd.
- **hhd-ui** supplies the separately packaged overlay executable. It remains an external runtime dependency; this repository does not vendor its code.
- This repository owns the service, capability detection, safety checks, and the fan-only settings/API contract between those components.

The planned overlay trigger is deliberately independent of hhd controller emulation: a desktop/session launcher and explicit service command will request the existing overlay service. Hardware shortcuts are optional rather than a prerequisite.

## Safety model

Fan control is opt-in and activates only after all of the following succeed:

1. a known, writable fan interface is discovered;
2. a safe temperature sensor is available;
3. the requested curve passes bounds and monotonicity validation; and
4. writes can be confirmed and monitored.

On a failed check, the service logs the reason, stops issuing PWM writes, and returns the device to its kernel-managed automatic mode whenever that recovery operation is available. A custom curve should never be used as a substitute for a manufacturer thermal-protection system.

## Status

This repository is in an extraction phase. The upstream tree is not yet a minimal fan-only distribution. Do not package or install it as a replacement for hhd until the dependency reduction and hardware validation matrix are complete.

## License and attribution

This project is a fork of hhd and remains licensed under the GNU Lesser General Public License, version 2.1 or later. The full license text is retained in [LICENSE](LICENSE). Upstream copyright notices and per-file SPDX notices must remain intact.

`hhd-ui` is a separate LGPL-2.1-or-later project. Installing it does not transfer ownership or modify either project's license obligations. See the upstream projects for their complete source and notices:

- [hhd](https://github.com/hhd-dev/hhd)
- [adjustor](https://github.com/hhd-dev/hhd/tree/master/src/adjustor)
- [hhd-ui](https://github.com/hhd-dev/hhd-ui)