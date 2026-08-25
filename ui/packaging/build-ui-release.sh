#!/usr/bin/env bash
# Run on x86_64 Linux to create the release assets used by hhd-fan/install.sh.
set -euo pipefail

command -v npm >/dev/null || { echo "npm is required." >&2; exit 1; }
command -v cargo >/dev/null || { echo "Rust/Cargo is required." >&2; exit 1; }

npm ci
npm run build

out="dist/release"
mkdir -p "${out}"
cp src-tauri/target/release/bundle/deb/*.deb "${out}/hhd-fan-ui-linux-amd64.deb"
cp src-tauri/target/release/bundle/rpm/*.rpm "${out}/hhd-fan-ui-linux-x86_64.rpm"
(cd "${out}" && sha256sum hhd-fan-ui-linux-amd64.deb hhd-fan-ui-linux-x86_64.rpm > SHA256SUMS)

echo "Release assets are in ${out}/"
