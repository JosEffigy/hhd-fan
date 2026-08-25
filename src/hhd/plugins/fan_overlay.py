"""Fan overlay lifecycle with an optional logical InputPlumber QAM shortcut."""

import time
import logging
from threading import Event as ThreadEvent, Lock, Thread
from typing import Sequence

from hhd.plugins import Context, Event, HHDPlugin

logger = logging.getLogger(__name__)
QAM_DOUBLE_TAP_WINDOW_SECONDS = 0.35
QAM_DEBOUNCE_SECONDS = 0.06


class FanOverlayPlugin(HHDPlugin):
    name = "fan_overlay"
    priority = 75
    log = "fovr"

    def __init__(self) -> None:
        self.service = None
        self.emit = None
        self._inputplumber_stop = ThreadEvent()
        self._inputplumber_thread: Thread | None = None
        self._last_qam_press = 0.0
        self._last_seen_press = 0.0
        self._qam_lock = Lock()

    def open(self, emit, context: Context) -> None:
        self.emit = emit
        try:
            from hhd.plugins.overlay.base import OverlayService

            self.service = OverlayService(context, emit)
        except Exception:
            logger.exception("Could not initialize the fan overlay")
        self._start_inputplumber_listener()

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
        self._inputplumber_stop.set()
        if self.service:
            self.service.close()

    def _start_inputplumber_listener(self) -> None:
        """Listen for InputPlumber's logical QAM event, never raw device input."""
        if self._inputplumber_thread:
            return
        self._inputplumber_thread = Thread(
            name="hhd-fan-inputplumber",
            target=self._listen_inputplumber,
            daemon=True,
        )
        self._inputplumber_thread.start()

    def _listen_inputplumber(self) -> None:
        try:
            import dbus
            import dbus.mainloop.glib
            from gi.repository import GLib

            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SystemBus()
            if not bus.name_has_owner("org.shadowblip.InputPlumber"):
                logger.info("InputPlumber is unavailable; QAM double-tap shortcut disabled")
                return

            loop = GLib.MainLoop()
            bus.add_signal_receiver(
                self._on_inputplumber_event,
                signal_name="InputEvent",
                dbus_interface="org.shadowblip.Input.DBusDevice",
            )
            logger.info("Listening for InputPlumber logical ui_quick events")

            def stop_when_requested() -> bool:
                if self._inputplumber_stop.is_set():
                    loop.quit()
                    return False
                return True

            GLib.timeout_add(250, stop_when_requested)
            loop.run()
        except Exception:
            logger.exception("InputPlumber listener disabled; fan control remains available")

    def _on_inputplumber_event(self, action, value) -> None:
        if str(action) != "ui_quick" or float(value) < 0.5 or not self.emit:
            return
        now = time.monotonic()
        with self._qam_lock:
            if now - self._last_seen_press < QAM_DEBOUNCE_SECONDS:
                return
            self._last_seen_press = now
            if now - self._last_qam_press > QAM_DOUBLE_TAP_WINDOW_SECONDS:
                self._last_qam_press = now
                return
            self._last_qam_press = 0.0
        logger.info("InputPlumber QAM double-tap detected; opening fan overlay")
        self.emit({"type": "special", "event": "overlay"})


def autodetect(existing: Sequence[HHDPlugin]) -> Sequence[HHDPlugin]:
    return list(existing) or [FanOverlayPlugin()]
