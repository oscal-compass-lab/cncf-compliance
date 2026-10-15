#!/usr/bin/env bash
# Install pinned Privateer (pvtr) and the GitHub repo scanner plugin into
# .privateer/bin, verifying each archive against the published SHA-256 checksums.
# Then build our own cncf-controls plugin from privateer-plugins/cncf-controls
# (requires Go); its dependencies are pinned and verified by go.mod and go.sum.
#
# Usage: scripts/privateer/install.sh [install-dir]
#
# Versions are pinned for reproducibility; bump them deliberately.
# The same script is intended to be called from the GitHub Actions workflow.
set -euo pipefail

PVTR_VERSION="v0.24.1"
PLUGIN_VERSION="v0.32.3"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${1:-$ROOT/.privateer/bin}"

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64)  OS_ARCH="Linux_x86_64" ;;
  Linux-aarch64) OS_ARCH="Linux_arm64" ;;
  *) echo "Unsupported platform: $(uname -s)-$(uname -m)" >&2; exit 1 ;;
esac

fetch() {
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    --max-time 120 -o "$2" "$1"
}

install_release() {
  local repo="$1" version="$2" asset="$3" tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN
  local base="https://github.com/${repo}/releases/download/${version}"
  fetch "${base}/${asset}" "$tmp/${asset}"
  fetch "${base}/checksums.txt" "$tmp/checksums.txt"
  local expected actual
  expected="$(awk -v a="$asset" '$2 == a {print $1}' "$tmp/checksums.txt")"
  [ -n "$expected" ] || { echo "No checksum published for ${asset}" >&2; return 1; }
  actual="$(sha256sum "$tmp/${asset}" | awk '{print $1}')"
  [ "$expected" = "$actual" ] || { echo "Checksum mismatch for ${asset}" >&2; return 1; }
  mkdir -p "$DEST"
  tar -xzf "$tmp/${asset}" -C "$DEST"
  echo "Installed ${asset} (${version}) -> ${DEST}"
}

install_release "privateerproj/pvtr" "$PVTR_VERSION" "pvtr_${OS_ARCH}.tar.gz"
install_release "revanite-io/pvtr-github-repo" "$PLUGIN_VERSION" \
  "pvtr-github-repo-scanner_${OS_ARCH}.tar.gz"

command -v go >/dev/null || { echo "Go is required to build the cncf-controls plugin" >&2; exit 1; }
PLUGIN_SRC="$ROOT/privateer-plugins/cncf-controls"
(cd "$PLUGIN_SRC" && GOFLAGS=-mod=readonly go build -trimpath \
  -ldflags "-s -w -X main.VersionPostfix=" -o "$DEST/cncf-controls" .)
echo "Built cncf-controls from ${PLUGIN_SRC} -> ${DEST}"

ls -l "$DEST"
