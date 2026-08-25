"""Detect active upstream HHD daemons before touching fan hardware."""

import os
import re
import subprocess

_UPSTREAM_HHD = re.compile(r"(?:^|[ /])hhd(?:\s|$)|python(?:3)?\s+-m\s+hhd(?:\s|$)")


def active_upstream_hhd() -> str | None:
    """Return a diagnostic if a distinct upstream HHD process is active."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            capture_output=True,
            check=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    for line in result.stdout.splitlines():
        pid_text, _, command = line.strip().partition(" ")
        if not pid_text.isdigit() or int(pid_text) == os.getpid():
            continue
        if _UPSTREAM_HHD.search(command):
            return f"active upstream HHD process (PID {pid_text})"
    return None
