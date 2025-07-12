#!/bin/bash
set -e

echo "[*] Cleaning DNF metadata and cache..."
sudo dnf clean all

echo "[*] Forcing full metadata refresh..."
sudo dnf makecache --refresh --enablerepo='*-source'

echo "[✓] DNF cache refreshed."



