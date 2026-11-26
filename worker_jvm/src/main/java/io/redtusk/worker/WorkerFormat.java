package io.redtusk.worker;

/**
 * The output layout this worker writes (rmeta/metadata.json, rmeta/embedded/..., thumbnails).
 *
 * A CRaC checkpoint resumes the jar it was baked from, so the checkpoint image records this
 * value ({@code --worker-format}) next to the checkpoint, and the engine refuses to restore a
 * checkpoint that records anything but its own {@code _WORKER_FORMAT} (src/redtusk/engine.py).
 * Bump both together when the output layout changes in a way the engine depends on.
 *
 * <p>1 = before the engine output contract (#64), which never recorded a format; 2 = #64's
 * layout (thumbnail namespace, embedded_paths, embedded size-cap warnings).
 */
final class WorkerFormat {
    static final int VERSION = 2;

    private WorkerFormat() { }
}
