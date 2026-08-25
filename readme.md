# hhd-fan

Safe fan control and a lightweight handheld overlay.

This focused downstream fork reuses and modifies code from [hhd](https://github.com/hhd-dev/hhd), [adjustor](https://github.com/hhd-dev/adjustor), and [hhd-ui](https://github.com/hhd-dev/hhd-ui) for fan control only.

The overlay follows InputPlumber's active QAM mapping (double-tap), not HHD controller controls; the included InputPlumber patch must be applied where its logical QAM event is not already exposed.

```sh
curl -fsSL https://raw.githubusercontent.com/JosEffigy/hhd-fan/master/install.sh | bash
```

The installer rejects unsupported hosts and hardware. LGPL-2.1-or-later; see [LICENSE](LICENSE).
