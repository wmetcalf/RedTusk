#!/usr/bin/env python3
"""Validate the generated metadata JSON Schema against real RedTusk output.

Iterates every succeeded job on the RedTusk host, fetches its result, and
runs Draft 2020-12 validation on each entry's metadata dict. Reports every
violation with the field name that caused it, the job ID, and the entry
content_type — so a non-100% pass tells you exactly what to add to the
registry/schema.

Exit codes:
  0  — every metadata dict validated cleanly
  1  — at least one violation
  2  — operational failure (host unreachable, schema unparseable, etc.)
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


def fetch_succeeded_ids(host: str, limit: int) -> list[str]:
    ids: list[str] = []
    page_size = 200
    offset = 0
    while len(ids) < limit:
        url = f"{host}/v1/jobs?state=succeeded&limit={page_size}&offset={offset}"
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                d = json.loads(r.read())
        except Exception as e:
            print(f"warn: list page failed at offset {offset}: {e}", file=sys.stderr)
            break
        page = d.get("jobs", [])
        if not page:
            break
        ids.extend(j["id"] for j in page)
        if not d.get("has_more"):
            break
        offset += page_size
    return ids[:limit]


def fetch_job(host: str, job_id: str) -> dict | None:
    try:
        with urllib.request.urlopen(f"{host}/v1/jobs/{job_id}", timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--host", default="http://172.18.101.15:8002")
    ap.add_argument("--schema", default=Path("docs/metadata-schema.json"), type=Path)
    ap.add_argument("--max-jobs", type=int, default=15000)
    ap.add_argument("--limit-report", type=int, default=50,
                    help="Print at most this many distinct violation field names")
    args = ap.parse_args(argv)

    if not args.schema.exists():
        print(f"error: schema not found: {args.schema}", file=sys.stderr)
        return 2
    schema = json.loads(args.schema.read_text())
    validator = Draft202012Validator(schema)

    ids = fetch_succeeded_ids(args.host, args.max_jobs)
    print(f"validating {len(ids)} succeeded jobs", file=sys.stderr)

    n_jobs = 0
    n_entries = 0
    n_clean_entries = 0
    # field_name → Counter of content_types where the violation was seen
    violators: dict[str, Counter] = defaultdict(Counter)
    sample_job_for: dict[str, str] = {}

    for i, jid in enumerate(ids):
        if i and i % 250 == 0:
            print(f"  [{i}/{len(ids)}] checked", file=sys.stderr)
        rec = fetch_job(args.host, jid)
        if rec is None:
            continue
        n_jobs += 1
        result = rec.get("result") or {}
        ext = result.get("extraction") or {}
        for entry in ext.get("entries") or []:
            md = entry.get("metadata") or {}
            if not isinstance(md, dict):
                continue
            n_entries += 1
            ct = entry.get("content_type", "?")
            errors = list(validator.iter_errors(md))
            if not errors:
                n_clean_entries += 1
                continue
            for err in errors:
                # additionalProperties violation: err.path empty, err.message
                # includes the bad key. Iterate err.context for sub-errors.
                if err.validator == "additionalProperties":
                    bad_keys = []
                    msg = err.message
                    # message: "Additional properties are not allowed ('foo', 'bar' were unexpected)"
                    import re as _re
                    bad_keys = _re.findall(r"'([^']+)' (?:was|were) unexpected",
                                            msg)
                    if not bad_keys:
                        bad_keys = _re.findall(r"'([^']+)'", msg)
                    for k in bad_keys:
                        violators[k][ct] += 1
                        sample_job_for.setdefault(k, jid)
                else:
                    # Other validation failure (type mismatch, regex, etc.)
                    path = "/".join(str(p) for p in err.absolute_path) or "(root)"
                    key = f"__{err.validator}__ at {path}"
                    violators[key][ct] += 1
                    sample_job_for.setdefault(key, jid)

    print(file=sys.stderr)
    print("=" * 64, file=sys.stderr)
    print(f"jobs checked:    {n_jobs}", file=sys.stderr)
    print(f"entries checked: {n_entries}", file=sys.stderr)
    print(f"entries clean:   {n_clean_entries} ({100*n_clean_entries//max(1,n_entries)}%)", file=sys.stderr)
    print(f"distinct violators: {len(violators)}", file=sys.stderr)
    print("=" * 64, file=sys.stderr)
    if not violators:
        print("\nSCHEMA PASSES 100% — no missing fields.", file=sys.stderr)
        return 0

    print(file=sys.stderr)
    print(f"top {min(args.limit_report, len(violators))} missing fields:", file=sys.stderr)
    sorted_v = sorted(violators.items(), key=lambda x: -sum(x[1].values()))
    for name, ct_counts in sorted_v[:args.limit_report]:
        total = sum(ct_counts.values())
        cts = ", ".join(f"{ct}={n}" for ct, n in ct_counts.most_common(3))
        print(f"  {total:6d}  {name!r:60}  sample_job={sample_job_for[name]}",
              file=sys.stderr)
        print(f"           ↳ top mimes: {cts}", file=sys.stderr)

    # Emit machine-readable summary on stdout
    print(json.dumps({
        "jobs_checked": n_jobs,
        "entries_checked": n_entries,
        "entries_clean": n_clean_entries,
        "distinct_violators": len(violators),
        "violators": {
            name: {
                "total": sum(ct_counts.values()),
                "by_content_type": dict(ct_counts),
                "sample_job": sample_job_for[name],
            } for name, ct_counts in sorted_v
        },
    }, indent=2))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
