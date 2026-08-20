"""Minimal overlay lifecycle with no controller/input shortcut monitoring."""

import logging
from typing import Sequence

from hhd.plugins import Context, Event, HHDPlugin

logger = logging.getLogger(__name__)


class FanOverlayPlugin(HHDPlugin):
    name = "fan_overlay"
    priority = 75
    log = "fovr"

    def __init__(self) -> None:
        self.service = None

    def open(self, emit, context: Context) -> None:
        try:
            from hhd.plugins.overlay.base import OverlayService

            self.service = OverlayService(context, emit)
        except Exception:
            logger.exception("Could not initialize the fan overlay")

    def settings(self):
        return {}

    def update(self, conf) -> None:
        if self.service:
            self.service.launch_overlay()

    def notify(self, events: Sequence[Event]) -> None:
        if not self.service:
            return
        for event in events:
            if event.get("type") == "special" and event.get("event") == "overlay":
                self.service.update("open_qam", True)

    def close(self) -> None:
        if self.service:
            self.service.close()


def autodetect(existing: Sequence[HHDPlugin]) -> Sequence[HHDPlugin]:
    return list(existing) or [FanOverlayPlugin()]
