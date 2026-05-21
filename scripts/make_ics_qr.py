#!/usr/bin/env python3
"""Generate an ICS calendar invite that renders a phone-scannable QR code
in the Outlook desktop event description (via X-ALT-DESC HTML).

The QR is encoded as half-block Unicode-art glyphs (▀▄█) inside a
fixed-width table cell with Word-specific styling that locks the
character-cell aspect so the QR doesn't get mangled by Outlook's HTML
renderer.

The fixture pattern is the one that decoded both visually in Outlook
desktop and through ClippyShot's HTML+Unicode-art QR detector
(fixture 32_ics_altdesc_locked.ics from the regression test set).

Usage examples:

  # Minimal — generate a QR for a URL, write to ./invite.ics
  ./make_ics_qr.py --url 'https://example.com/coffee'

  # Custom subject, start time, duration, output path
  ./make_ics_qr.py \\
      --url 'https://example.com/promo' \\
      --summary 'Q1 Review' \\
      --start 2026-06-15T14:00 \\
      --duration-min 30 \\
      --out promo.ics

  # Bulk — read URLs from stdin, one per line, name files <hash>.ics
  echo 'https://a.example/x' | ./make_ics_qr.py --url - --out-dir /tmp/bulk/

Requires: python -m pip install qrcode (no PIL needed; matrix-only mode).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import qrcode


# ── QR matrix → half-block text-art rows ──────────────────────────────────
def make_qr_rows(url: str, *, ecc: str = 'H', border: int = 4) -> list[str]:
    """Return the QR encoded as half-block text-art rows.

    `border=4` is the spec-required quiet zone — iPhone scanner needs it.
    `ecc='H'` is 30% error correction (tolerates module misreads from
    line-height jitter / font fallback at the edges).
    """
    ecc_map = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H,
    }
    q = qrcode.QRCode(version=None, error_correction=ecc_map[ecc.upper()],
                      box_size=1, border=border)
    q.add_data(url)
    q.make(fit=True)
    m = q.get_matrix()
    rows, cols = len(m), len(m[0])
    if rows % 2:                       # half-block packs 2 module-rows per char
        m.append([False] * cols)
    art = []
    for r in range(0, len(m), 2):
        chars = []
        for c in range(cols):
            top, bot = m[r][c], m[r + 1][c]
            if top and bot: chars.append('█')
            elif top:       chars.append('▀')
            elif bot:       chars.append('▄')
            else:           chars.append(' ')
        art.append(''.join(chars))
    return art


# ── HTML body — fixture 32 style: Word HTML survives this ────────────────
def make_html_body(url: str, art_rows: list[str], *, font_size_px: int = 11) -> str:
    """Build the X-ALT-DESC HTML body. The combination of:

      - <font face="Courier New" size="1">    (legacy HTML, Word respects)
      - fixed-width <table><td>               (prevents Word from reflowing)
      - per-row <div> with mso-line-height-rule:exactly
      - matching line-height + font-size in px (locks square aspect)
      - &nbsp; for light cells                (no font-fallback on whitespace)
      - white-space:nowrap                    (no mid-row wrap)

    is what survived Outlook desktop's HTML rendering in our regression
    fixtures. Other combinations rendered as vertical stripes, blank
    cells, or misaligned right edges.
    """
    cols = len(art_rows[0])
    container_w = cols * 8 + 20     # eyeballed: 11px Courier ≈ 6.6px per glyph

    def to_entities(s: str) -> str:
        # Encodes for both text and attribute contexts: covers `&<>` as expected
        # plus `"` and `'` so a future use like <a href="{to_entities(url)}">
        # doesn't reintroduce attribute-context XSS that the caller might miss.
        out = []
        for ch in s:
            cp = ord(ch)
            if ch == ' ':
                out.append('&nbsp;')
            elif cp < 128:
                out.append({'&': '&amp;', '<': '&lt;', '>': '&gt;',
                            '"': '&quot;', "'": '&#39;'}.get(ch, ch))
            else:
                out.append(f'&#{cp};')
        return ''.join(out)

    parts = [
        '<html><body style="margin:0;padding:0">',
        '<p>Scan to verify:</p>',
        f'<table cellpadding="0" cellspacing="0" border="0" width="{container_w}" '
        f'style="border-collapse:collapse;table-layout:fixed;width:{container_w}px">',
        f'<tr><td width="{container_w}" '
        f'style="width:{container_w}px;padding:0">',
        '<font face="Courier New" size="1">',
    ]
    for row in art_rows:
        parts.append(
            f'<div style="margin:0;padding:0;'
            f'line-height:{font_size_px}px;mso-line-height-rule:exactly;'
            f'font-family:Courier New,monospace;'
            f'font-size:{font_size_px}px;letter-spacing:0;white-space:nowrap">'
            + to_entities(row) + '</div>'
        )
    parts.append('</font></td></tr></table>')
    # Entity-encode the URL so a `--url` that contains `</p><script>` or other
    # markup characters can't break out of the <p> context and inject script
    # tags into the Outlook HTML alternative. The QR rows are already encoded
    # via to_entities(); the bare URL was the lone unescaped sink.
    parts.append(f'<p>{to_entities(url)}</p></body></html>')
    return ''.join(parts)


# ── ICS framing ──────────────────────────────────────────────────────────
def ics_escape(s: str) -> str:
    """RFC 5545 §3.3.11 — escape \\, ;, , and convert newlines to \\n."""
    return (s.replace('\\', '\\\\')
             .replace(';', r'\;')
             .replace(',', r'\,')
             .replace('\n', r'\n'))


def fold_line(line: str) -> list[str]:
    """RFC 5545 §3.1 — fold lines >75 octets at 72 octets with leading space."""
    if len(line) <= 72:
        return [line]
    out = [line[:72]]
    rest = line[72:]
    while rest:
        out.append(' ' + rest[:71])
        rest = rest[71:]
    return out


def build_ics(*, url: str, summary: str, start: datetime,
              duration: timedelta, uid: str,
              description: str | None = None) -> bytes:
    """Assemble the full VCALENDAR/VEVENT body with the X-ALT-DESC QR.

    DTSTART/DTEND are emitted as floating UTC (Z suffix). The plain-text
    DESCRIPTION is a fallback for clients that don't render X-ALT-DESC
    (Thunderbird, several mobile clients).
    """
    art_rows = make_qr_rows(url)
    html_body = make_html_body(url, art_rows)
    alt = ics_escape(html_body)

    end = start + duration
    dtstamp = datetime.now(timezone.utc)

    plain_desc = description if description else (
        'Scan the QR rendered in the HTML alt-desc to verify.\\n\\n'
        + ics_escape(url)
    )

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//ClippyShot//ICS QR generator//EN',
        'BEGIN:VEVENT',
        f'UID:{uid}',
        f'DTSTAMP:{dtstamp.strftime("%Y%m%dT%H%M%SZ")}',
        f'DTSTART:{start.strftime("%Y%m%dT%H%M%SZ")}',
        f'DTEND:{end.strftime("%Y%m%dT%H%M%SZ")}',
        f'SUMMARY:{ics_escape(summary)}',
        f'DESCRIPTION:{plain_desc}',
        f'X-ALT-DESC;FMTTYPE=text/html:{alt}',
        'END:VEVENT',
        'END:VCALENDAR',
    ]
    folded = []
    for ln in lines:
        folded.extend(fold_line(ln))
    return ('\r\n'.join(folded) + '\r\n').encode('utf-8')


# ── CLI ──────────────────────────────────────────────────────────────────
def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument('--url', required=True,
                   help='URL/text to encode in the QR. Use "-" to read '
                        'multiple URLs from stdin (one per line).')
    p.add_argument('--summary', default='Important meeting',
                   help='Calendar event title (default: "Important meeting")')
    p.add_argument('--start', default=None,
                   help='Event start, ISO-8601 (default: 1 hour from now, UTC). '
                        'Example: 2026-06-15T14:00')
    p.add_argument('--duration-min', type=int, default=60,
                   help='Event duration in minutes (default: 60)')
    p.add_argument('--uid', default=None,
                   help='VEVENT UID (default: random)')
    p.add_argument('--out', default=None,
                   help='Output file path. Defaults to ./invite.ics or, '
                        'when --url is "-", <urlhash>.ics in --out-dir.')
    p.add_argument('--out-dir', default='.',
                   help='Output directory when --url is "-" (default: cwd)')
    return p.parse_args(argv)


def default_start() -> datetime:
    """One hour from now, truncated to the minute."""
    return (datetime.now(timezone.utc) + timedelta(hours=1)).replace(
        second=0, microsecond=0)


def parse_iso(s: str) -> datetime:
    """Accept '2026-06-15T14:00' (assume UTC) or full ISO with timezone."""
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as exc:
        raise SystemExit(f'invalid --start: {s} ({exc})')
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def write_one(url: str, args, *, out_path: Path) -> Path:
    start = parse_iso(args.start) if args.start else default_start()
    duration = timedelta(minutes=args.duration_min)
    uid = args.uid or f'{uuid.uuid4()}@clippyshot.local'
    blob = build_ics(url=url, summary=args.summary, start=start,
                     duration=duration, uid=uid)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(blob)
    return out_path


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.url == '-':
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for line in sys.stdin:
            url = line.strip()
            if not url or url.startswith('#'):
                continue
            slug = hashlib.sha1(url.encode()).hexdigest()[:12]
            target = out_dir / f'{slug}.ics'
            write_one(url, args, out_path=target)
            print(f'{target}  {url}')
        return 0

    out_path = Path(args.out) if args.out else Path('invite.ics')
    written = write_one(args.url, args, out_path=out_path)
    print(f'wrote {written}  ({written.stat().st_size} bytes)  url={args.url}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
