"""Fan-only adjustor integration for hhd-fan.

This intentionally excludes adjustor's TDP, GPU, battery and platform plugins.
"""

import logging
from threading import Event, Lock, Thread
from typing import Sequence

from hhd.plugins import Config, Context, HHDPlugin, load_relative_yaml

from adjustor.core.fan import fan_worker, get_fan_info
from adjustor.core.fan.core import validate_fan_curve

logger = logging.getLogger(__name__)
POINTS = (40, 50, 60, 70, 80, 90)


class FanPlugin(HHDPlugin):
    name = "adjustor_fan"
    priority = 10
    log = "fan"

    def __init__(self) -> None:
        self.info = None
        self.thread: Thread | None = None
        self.exit = Event()
        self.junction = Event()
        self.lock = Lock()
        self.curve: dict[int, float] = {}
        self.state: dict = {}

    def open(self, emit, context: Context) -> None:
        self.emit = emit
        self.info = get_fan_info()
        if self.info:
            logger.info("Supported fan capability detected: %d fan(s)", len(self.info["fans"]))
        else:
            logger.warning("No supported fan capability detected; hardware will remain untouched")

    def settings(self):
        return {"fan": load_relative_yaml("fan_settings.yml")} if self.info else {}

    def _stop(self) -> None:
        if self.thread:
            self.exit.set()
            self.thread.join(timeout=3)
            if self.thread.is_alive():
                logger.critical("Fan worker did not stop within watchdog timeout")
            self.thread = None
        self.state.clear()

    def update(self, conf: Config) -> None:
        if not self.info:
            return
        enabled = conf.get("fan.fan.enabled", False)
        if not enabled:
            self._stop()
            conf["fan.fan.status"] = "Automatic control"
            return

        candidate = {point: conf[f"fan.fan.st{point}"].to(int) / 100 for point in POINTS}
        try:
            validate_fan_curve(candidate)
        except (TypeError, ValueError) as error:
            logger.error("Rejected unsafe fan curve: %s", error)
            conf["fan.fan.enabled"] = False
            self._stop()
            return

        with self.lock:
            self.curve.clear()
            self.curve.update(candidate)
            use_junction = conf.get("fan.fan.sensor", "edge") == "junction"
            if use_junction and self.info["tctl"] is None:
                logger.warning("Junction sensor requested but unavailable; using edge sensor")
                conf["fan.fan.sensor"] = "edge"
                use_junction = False
            self.junction.set() if use_junction else self.junction.clear()

            if self.state:
                rpm = ", ".join(str(v) for v in self.state["v_rpm"]) or "unavailable"
                conf["fan.fan.status"] = (
                    f"{self.state['v_curr'] * 100:.0f}% · {self.state['t_edge']:.1f}°C · RPM {rpm}"
                )

        if self.thread and not self.thread.is_alive():
            logger.error("Fan watchdog detected a stopped worker; restoring automatic control")
            self._stop()
            conf["fan.fan.enabled"] = False
            return
        if not self.thread:
            self.exit.clear()
            self.thread = Thread(
                name="hhd-fan-worker",
                target=fan_worker,
                args=(self.info, self.exit, self.lock, self.curve, self.state, self.junction),
                daemon=True,
            )
            self.thread.start()

    def close(self) -> None:
        self._stop()


def autodetect(existing: Sequence[HHDPlugin]) -> Sequence[HHDPlugin]:
    return list(existing) or [FanPlugin()]
