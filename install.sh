#!/usr/bin/env bash
# Install hhd-fan and its packaged Tauri overlay runtime.
set -euo pipefail

repo="https://github.com/JosEffigy/hhd-fan.git"
raw="https://raw.githubusercontent.com/JosEffigy/hhd-fan/master"

command -v pip3 >/dev/null || { echo "pip3 is required." >&2; exit 1; }
command -v curl >/dev/null || { echo "curl is required." >&2; exit 1; }

echo "Installing hhd-fan..."
pip3 install --upgrade "git+${repo}"

echo "Installing service and device rules..."
sudo mkdir -p /usr/lib/udev/rules.d /usr/lib/systemd/system
sudo curl -fsSL "${raw}/usr/lib/udev/rules.d/83-hhd.rules" -o /usr/lib/udev/rules.d/83-hhd.rules
sudo curl -fsSL "${raw}/usr/lib/systemd/system/hhd_local@.service" -o /usr/lib/systemd/system/hhd_local@.service
sudo systemctl daemon-reload
sudo systemctl enable --now "hhd_local@${USER}"

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
