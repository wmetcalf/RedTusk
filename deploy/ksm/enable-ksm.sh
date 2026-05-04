#!/usr/bin/env bash
# Enable KSM (Kernel Same-page Merging) for RedTusk worker memory dedup.
# Run once at host boot or via the systemd unit below.
# Requires Linux with CONFIG_KSM=y (standard on all major distros since 2.6.32).
set -euo pipefail
echo 1    > /sys/kernel/mm/ksm/run
echo 1000 > /sys/kernel/mm/ksm/pages_to_scan
echo 200  > /sys/kernel/mm/ksm/sleep_millisecs
echo "KSM enabled:"
echo "  run=$(cat /sys/kernel/mm/ksm/run)"
echo "  pages_to_scan=$(cat /sys/kernel/mm/ksm/pages_to_scan)"
echo "  sleep_millisecs=$(cat /sys/kernel/mm/ksm/sleep_millisecs)"
