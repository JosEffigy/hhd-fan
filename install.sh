#!/usr/bin/env bash
# Install hhd-fan and its packaged Tauri overlay runtime.
set -euo pipefail

repo="https://github.com/JosEffigy/hhd-fan.git"
raw="https://raw.githubusercontent.com/JosEffigy/hhd-fan/master"

command -v pip3 >/dev/null || { echo "pip3 is required." >&2; exit 1; }
command -v curl >/dev/null || { echo "curl is required." >&2; exit 1; }
command -v git >/dev/null || { echo "git is required." >&2; exit 1; }
[ "$(uname -s)" = "Linux" ] || { echo "hhd-fan supports Linux only." >&2; exit 1; }
[ "$(uname -m)" = "x86_64" ] || { echo "hhd-fan currently supports x86_64 only." >&2; exit 1; }
command -v systemctl >/dev/null || { echo "A systemd-based host is required." >&2; exit 1; }

supported_fan=0
for name_file in /sys/class/hwmon/hwmon*/name; do
  [ -r "${name_file}" ] || continue
  case "$(cat "${name_file}")" in
    oxp_ec|gpdfan|ayaneo_ec|oxpec)
      hwmon_dir=$(dirname "${name_file}")
      for pwm in "${hwmon_dir}"/pwm[0-9]*; do
        [ -e "${pwm}_enable" ] && supported_fan=1
      done
      ;;
  esac
done
[ "${supported_fan}" -eq 1 ] || {
  echo "No safe, supported fan interface was found. Installation rejected." >&2
  exit 1
}

echo "Installing hhd-fan..."
pip3 install --upgrade "git+${repo}"

if ! python3 -c 'from adjustor.core.fan import get_fan_info; raise SystemExit(0 if get_fan_info() else 1)'; then
  echo "No safe, supported fan capability was found. Nothing was installed as a service." >&2
  exit 1
fi

echo "Installing service and device rules..."
sudo mkdir -p /usr/lib/udev/rules.d /usr/lib/systemd/system
sudo curl -fsSL "${raw}/usr/lib/udev/rules.d/83-hhd.rules" -o /usr/lib/udev/rules.d/83-hhd.rules
sudo curl -fsSL "${raw}/usr/lib/systemd/system/hhd_fan@.service" -o /usr/lib/systemd/system/hhd_fan@.service
sudo systemctl daemon-reload
sudo systemctl enable --now "hhd_fan@${USER}"

echo "Installing the packaged Tauri overlay..."
tmpdir=$(mktemp -d)
trap 'rm -rf "${tmpdir}"' EXIT
case "$(. /etc/os-release && printf '%s' "${ID_LIKE:-$ID}")" in
  *debian*|*ubuntu*)
    ui_url="https://github.com/JosEffigy/hhd-fan/releases/latest/download/hhd-fan-ui-linux-amd64.deb"
    curl -fL "${ui_url}" -o "${tmpdir}/hhd-fan-ui.deb"
    sudo apt-get install -y "${tmpdir}/hhd-fan-ui.deb"
    ;;
  *fedora*|*rhel*|*suse*)
    ui_url="https://github.com/JosEffigy/hhd-fan/releases/latest/download/hhd-fan-ui-linux-x86_64.rpm"
    curl -fL "${ui_url}" -o "${tmpdir}/hhd-fan-ui.rpm"
    if command -v dnf >/dev/null; then
      sudo dnf install -y "${tmpdir}/hhd-fan-ui.rpm"
    else
      sudo zypper --non-interactive install "${tmpdir}/hhd-fan-ui.rpm"
    fi
    ;;
  *)
    echo "Unsupported package manager. Install the hhd-fan-ui .deb or .rpm release manually." >&2
    exit 1
    ;;
esac

echo "Installed. Launch the fan overlay with: hhd-fan-overlay"
