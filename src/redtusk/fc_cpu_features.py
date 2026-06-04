"""Detect CRaC "warp" CPU-feature mismatches from a Firecracker guest console.

A CRaC checkpoint records the CPU feature set of the host it was *created* on
(the build container, which sees the full host CPU). When that checkpoint is
*restored* inside a Firecracker microVM — which exposes a reduced feature set —
the warp engine aborts the restore if the checkpoint needs features the guest
lacks. The JVM then dies with the generic ``Could not create the Java Virtual
Machine``; from the pool's point of view the slot simply never signals READY,
surfacing only as an opaque ``fifo not found within warmup timeout``.

The warp engine, however, prints the *compatible* value on the guest console:

    [crac] Restore failed due to incompatible or missing CPU features,
           try using -XX:CPUFeatures=0x102100055bbd7,0x1c8 on checkpoint.

So detection is a parse, not a guess. :func:`parse_cpu_mismatch` extracts that
value from the captured serial console (``<slot.scratch_dir>/fc.log``); the FC
runtime, on warmup timeout, raises :class:`redtusk.errors.FcCpuFeatureMismatchError`
with an actionable remediation instead of the opaque timeout.

----
Canonical implementation: ``blastbox.host.runtime.cpu_features`` (with its unit
tests). This is a deliberate vendored copy: RedTusk pins ``blastbox`` from PyPI,
so importing the canonical module would couple this error-path diagnostic to a
blastbox release. Keep the two byte-for-byte in sync (same regex, same fields).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# The warp/CRaC restore error names the compatible value, e.g.
#   "... incompatible or missing CPU features, try using
#    -XX:CPUFeatures=0x102100055bbd7,0x1c8 on checkpoint."
# DOTALL so a console with the message wrapped across lines still matches; the
# value charset is restricted to what -XX:CPUFeatures accepts (hex words +
# comma separators) so we stop at the first whitespace/end-of-token.
_MISMATCH_RE = re.compile(
    r"incompatible or missing CPU features.*?-XX:CPUFeatures=([0-9a-fx,]+)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class CpuFeatureMismatch:
    """A detected CRaC CPU-feature mismatch parsed from a guest console.

    ``needed`` is the value to pin on the checkpoint, e.g.
    ``"0x102100055bbd7,0x1c8"``. ``raw_line`` is the matched text, for logs.
    """

    needed: str
    raw_line: str


def parse_cpu_mismatch(console_text: str | None) -> CpuFeatureMismatch | None:
    """Scan a guest serial console for the warp CRaC CPU-feature-mismatch
    signature.

    Returns a :class:`CpuFeatureMismatch` carrying the compatible
    ``-XX:CPUFeatures`` value the warp engine reported, or ``None`` if the
    console shows no such mismatch — so the caller falls back to the generic
    warmup-timeout path with no behavior change on the happy path.
    """
    if not console_text:
        return None
    m = _MISMATCH_RE.search(console_text)
    if not m:
        return None
    return CpuFeatureMismatch(needed=m.group(1), raw_line=m.group(0).strip())
