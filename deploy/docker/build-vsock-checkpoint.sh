#!/bin/sh
# Build-time CRaC checkpoint orchestration for the vsock IPC profile.
#
# Starts a tiny AF_UNIX listener (build-vsock-listener.py), then runs the
# worker JVM in --checkpoint mode with REDTUSK_VSOCK_UNIX_PATH pointing at
# that listener. The worker connects, sends READY, then calls
# Core.checkpointRestore() — at which point VsockIpcChannel.beforeCheckpoint
# closes the socket, the listener sees EOF and exits, and warp dumps the
# checkpoint.
set -eu

BUILD_SOCK=/tmp/build-vsock.sock
LOG=/tmp/build-vsock.log
rm -f "$BUILD_SOCK" "$LOG"

echo "build-vsock: starting listener" >&2
BUILD_VSOCK_SOCK="$BUILD_SOCK" python3 /usr/local/bin/build-vsock-listener.py > "$LOG" 2>&1 &
BG_PID=$!

# Wait for the listener socket to appear (max 5s).
for _ in $(seq 1 50); do
    if [ -S "$BUILD_SOCK" ]; then break; fi
    sleep 0.1
done
if [ ! -S "$BUILD_SOCK" ]; then
    echo "build-vsock: listener failed to bind in 5s" >&2
    cat "$LOG" >&2
    exit 2
fi
echo "build-vsock: listener bound, launching java" >&2

# Run the checkpoint JVM. The vsock URL override makes VsockIpcChannel
# use AF_UNIX (no /dev/vsock needed at build time).
REDTUSK_WORKER_IPC=vsock \
REDTUSK_VSOCK_UNIX_PATH="$BUILD_SOCK" \
REDTUSK_VSOCK_PORT=10001 \
REDTUSK_VSOCK_HOST_CID=2 \
REDTUSK_DISABLE_KSM=1 \
java \
    -XX:CRaCEngine=warp \
    -XX:CRaCCheckpointTo=/app/checkpoint \
    -XX:AOTCache=/app/redtusk.aot \
    --enable-native-access=ALL-UNNAMED \
    -XX:+UseSerialGC -Xverify:none -XX:TieredStopAtLevel=1 \
    -Xms800m -Xmx800m -XX:+AlwaysPreTouch \
    -Djava.library.path=/app \
    -jar /app/redtusk-worker.jar \
    --checkpoint /scratch \
    || true

# warp checkpoint exits the JVM non-zero by design. Wait for the listener
# to drain (it sees EOF when the JVM's beforeCheckpoint closes the socket).
wait "$BG_PID" 2>/dev/null || true

echo "build-vsock: listener log:" >&2
cat "$LOG" >&2 || true
rm -f "$BUILD_SOCK" "$LOG"

if [ ! -d /app/checkpoint ] || [ -z "$(ls /app/checkpoint/ 2>/dev/null)" ]; then
    echo "build-vsock: FAILED — /app/checkpoint is missing or empty" >&2
    exit 3
fi
echo "warp checkpoint (vsock-mode) captured: $(du -sh /app/checkpoint | cut -f1)"
