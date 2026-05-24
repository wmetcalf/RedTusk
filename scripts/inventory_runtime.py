#!/usr/bin/env python3
"""Runtime metadata-field observer for RedTusk.

Pairs with the Tika fork's tools/inventory_static.py: that one walks the
parser SOURCE to enumerate every field that could possibly be emitted. This
one walks the API for jobs already in the corpus and reports which fields
have actually been observed in practice, grouped by per-entry content type.

Output JSON shape:

    {
      "scanned_at": "...",
      "host": "...",
      "jobs_scanned": N,
      "by_mime_type": {
        "application/pdf": {
          "<field-name>": {
            "count": <how many entries of this MIME emitted the field>,
            "example_value": "<truncated example string>"
          }
        }
      },
      "by_field": {
        "<field-name>": {
          "total_count": <how many entries across all MIME types>,
          "mime_types": ["application/pdf", "image/jpeg", ...]
        }
      }
    }

Run after submitting a representative corpus. Compose with inventory_static.json
to attach per-MIME observed-count to each declared field — the resulting registry
shows both "what CAN be emitted" (static) and "what HAS been emitted" (runtime).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def fetch_json(host: str, path: str, timeout: float = 30.0) -> dict:
    url = host.rstrip("/") + path
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)


def walk_jobs(host: str, max_jobs: int) -> list[dict]:
    """Paginate /v1/jobs until we have max_jobs or run out."""
    jobs: list[dict] = []
    offset = 0
    page_size = 200
    while len(jobs) < max_jobs:
        page = fetch_json(host, f"/v1/jobs?limit={page_size}&offset={offset}")
        items = page.get("items") or page.get("jobs") or []
        if not items:
            break
        jobs.extend(items[: max_jobs - len(jobs)])
        offset += len(items)
        if len(items) < page_size:
            break
    return jobs


def truncate(s: str, n: int = 80) -> str:
    s = s.replace("\n", " ").replace("\r", " ")
    return s if len(s) <= n else s[: n - 3] + "..."


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="http://localhost:8000",
                    help="RedTusk API base URL (default: http://localhost:8000)")
    ap.add_argument("--max-jobs", type=int, default=2000,
                    help="Cap total jobs to scan (default: 2000)")
    ap.add_argument("--out", default="docs/metadata-fields-observed.json", type=Path,
                    help="Output JSON path (default: docs/metadata-fields-observed.json)")
    args = ap.parse_args(argv)

    print(f"walking jobs from {args.host} ...", file=sys.stderr)
    jobs = walk_jobs(args.host, args.max_jobs)
    print(f"  fetched {len(jobs)} job summaries", file=sys.stderr)

    succeeded = [j for j in jobs if j.get("state") == "succeeded"]
    print(f"  {len(succeeded)} succeeded", file=sys.stderr)

    # Per-MIME, per-field counts + example values.
    by_mime: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"count": 0, "example_value": None}))
    by_field_total: Counter[str] = Counter()
    by_field_mimes: dict[str, set[str]] = defaultdict(set)

    for i, j in enumerate(succeeded):
        if i % 50 == 0:
            print(f"  fetching job detail {i}/{len(succeeded)}", file=sys.stderr)
        try:
            doc = fetch_json(args.host, f"/v1/jobs/{j['id']}")
        except Exception as e:
            print(f"  warn: fetch {j['id'][:8]} failed: {e}", file=sys.stderr)
            continue
        entries = ((doc.get("result") or {}).get("extraction") or {}).get("entries") or []
        for entry in entries:
            mime = entry.get("content_type") or "application/octet-stream"
            mime = mime.split(";", 1)[0].strip()  # strip "; charset=..." params
            meta = entry.get("metadata") or {}
            for field_name, value in meta.items():
                slot = by_mime[mime][field_name]
                slot["count"] += 1
                if slot["example_value"] is None and isinstance(value, str) and value:
                    slot["example_value"] = truncate(value)
                by_field_total[field_name] += 1
                by_field_mimes[field_name].add(mime)

    out_doc = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "host": args.host,
        "jobs_scanned": len(succeeded),
        "by_mime_type": {
            mime: dict(sorted(fields.items()))
            for mime, fields in sorted(by_mime.items())
        },
        "by_field": {
            field: {
                "total_count": by_field_total[field],
                "mime_types": sorted(by_field_mimes[field]),
            }
            for field in sorted(by_field_total)
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out_doc, indent=2, ensure_ascii=False))
    print(f"wrote {args.out}", file=sys.stderr)
    print(f"  {len(by_field_total)} distinct fields observed across {len(by_mime)} MIME types",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
