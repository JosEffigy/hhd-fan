import os

FAN_HWMONS_LEGACY = ["oxpec"]
FAN_HWMONS = ["oxp_ec", "gpdfan", "ayaneo_ec"]
HWMON_DIR = "/sys/class/hwmon"


def get_hwmon():
    try:
        entries = os.listdir(HWMON_DIR)
    except OSError as e:
        # A missing or unreadable hwmon hierarchy means this host cannot safely
        # be controlled.  Callers treat an empty iterator as unsupported.
        return
    for dir in entries:
        if dir.startswith("hwmon"):
            yield dir


def find_edge_temp():
    for hwmon in get_hwmon():
        with open(f"{HWMON_DIR}/{hwmon}/name") as f:
            name = f.read().strip()

        if name != "amdgpu":
            continue

        # For sanity, check the device has CPUs to avoid hooking an eGPU.
        if not os.path.exists(f"{HWMON_DIR}/{hwmon}/device/local_cpus"):
            continue

        if not os.path.exists(f"{HWMON_DIR}/{hwmon}/temp1_input"):
            continue

        return f"{HWMON_DIR}/{hwmon}/temp1_input"


def find_tctl_temp():
    for hwmon in get_hwmon():
        with open(f"{HWMON_DIR}/{hwmon}/name") as f:
            name = f.read().strip()

        if name != "k10temp":
            continue

        # For sanity, check the device has CPUs to avoid hooking an eGPU.
        if not os.path.exists(f"{HWMON_DIR}/{hwmon}/device/local_cpus"):
            continue

        if not os.path.exists(f"{HWMON_DIR}/{hwmon}/temp1_input"):
            continue

        return f"{HWMON_DIR}/{hwmon}/temp1_input"


def find_fans():
    """Finds tunable fans with endpoints pwmX and pwmX_enable."""
    fans = []
    for hwmon in get_hwmon():
        try:
            with open(f"{HWMON_DIR}/{hwmon}/name") as f:
                name = f.read().strip()
            files = set(os.listdir(f"{HWMON_DIR}/{hwmon}"))
        except OSError:
            # hwmon devices can disappear during suspend/resume or hotplug.
            # Skipping them is safer than retaining a stale writable path.
            continue

        if name not in FAN_HWMONS and name not in FAN_HWMONS_LEGACY:
            continue

        for fn in files:
            if (
                fn.startswith("pwm")
                and fn[3:].isdigit()
                and os.path.exists(f"{HWMON_DIR}/{hwmon}/{fn}_enable")
            ):
                idx = fn[3:]
                speed = f"fan{idx}_input"
                if speed in files:
                    speed_fn = f"{HWMON_DIR}/{hwmon}/{speed}"
                else:
                    speed_fn = None
                fans.append(
                    (
                        f"{HWMON_DIR}/{hwmon}/{fn}",
                        f"{HWMON_DIR}/{hwmon}/{fn}_enable",
                        speed_fn,
                        name in FAN_HWMONS_LEGACY,
                    )
                )

    return fans


def read_temp(path: str) -> float:
    with open(path, "r") as f:
        return int(f.read()) / 1000


def read_fan_speed(path: str) -> int:
    with open(path, "r") as f:
        return int(f.read())


def write_fan_speed(path: str, speed: int):
    if not 0 <= speed <= 255:
        raise ValueError(f"PWM value out of range: {speed}")
    with open(path, "w") as f:
        f.write(str(speed))
