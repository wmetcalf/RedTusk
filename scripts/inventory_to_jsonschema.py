#!/usr/bin/env python3
"""Generate a JSON Schema for the RedTusk metadata dict from the combined registry.

Input:  docs/metadata-fields.json (combined static+runtime registry)
Output: docs/metadata-schema.json

The schema validates the per-entry metadata dict found at

    result.extraction.entries[].metadata

of any RedTusk job result. Every observed Tika metadata field becomes either
a named `properties` entry or matches a `patternProperties` regex; the schema
sets `additionalProperties: false` so any field name not in the registry is
rejected. This is the strict data contract for downstream consumers — adding
a new field requires a registry refresh + schema regeneration.

Empirically every metadata value in actual RedTusk output is a JSON string
(Tika's Metadata API stores String[]/String and RedTusk passes them through
verbatim — even *Bag-typed Properties get joined to a single string at
serialization time). The schema therefore types every field as `string`;
the original Tika Property factory is preserved in each property's
`description` for documentation only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _template_to_regex(pattern: str) -> str | None:
    """Convert a registry template pattern like 'ICC:*' or '*:x-default' to a regex.

    Patterns have at most one '*' wildcard. We anchor and require the dynamic
    middle to be non-empty (avoids matching the bare anchor).
    """
    if pattern.count("*") != 1:
        return None
    prefix, suffix = pattern.split("*", 1)
    if not prefix and not suffix:
        return None
    parts = ["^"]
    if prefix:
        parts.append(re.escape(prefix))
    parts.append(".+")
    if suffix:
        parts.append(re.escape(suffix))
    parts.append("$")
    return "".join(parts)


def build_schema(registry: dict, schema_id: str | None = None) -> dict:
    properties: dict[str, dict] = {}
    pattern_props: dict[str, dict] = {}

    # ── named properties ─────────────────────────────────────────────────
    # Include every declared field and every undeclared-literal field.
    # Skip templated entries — they're individual instances of a parent
    # pattern that goes into patternProperties below.
    for name, info in registry["fields"].items():
        status = set(info["status"])
        if "templated" in status:
            continue
        # Sanity guard: skip names with control characters or newlines.
        # All real Tika field names are printable ASCII (possibly with
        # spaces and trailing space). JSON Schema property keys can be
        # any string but malformed names are almost always indexer noise.
        if "\n" in name or "\r" in name or "\t" in name:
            continue
        prop = {"type": "string"}
        decl = info.get("declared_in")
        cname = info.get("constant_name")
        ftype = info.get("type")
        bits = []
        if decl:
            bits.append(f"declared_in={decl}")
        if cname:
            bits.append(f"constant={cname}")
        if ftype:
            bits.append(f"factory={ftype}")
        if "observed" in status:
            obs_count = info.get("observed_count")
            if obs_count is not None:
                bits.append(f"observed_count={obs_count}")
        if bits:
            prop["description"] = "; ".join(bits)
        properties[name] = prop

    # ── pattern properties from templated patterns ───────────────────────
    seen_patterns: set[str] = set()
    for info in registry["fields"].values():
        if "templated" not in info["status"]:
            continue
        tp = info.get("template_pattern")
        if tp and tp not in seen_patterns:
            seen_patterns.add(tp)

    for tp in sorted(seen_patterns):
        regex = _template_to_regex(tp)
        if regex is None:
            continue
        pattern_props[regex] = {
            "type": "string",
            "description": f"templated field matching {tp}",
        }

    schema: dict = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "RedTusk metadata field contract",
        "description": (
            "Strict schema for the per-entry metadata dict in a RedTusk job "
            "result (result.extraction.entries[].metadata). Generated from "
            "docs/metadata-fields.json by scripts/inventory_to_jsonschema.py — "
            "do not edit by hand."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "patternProperties": pattern_props,
    }
    if schema_id:
        schema["$id"] = schema_id
    schema["x-generated-at"] = datetime.now(timezone.utc).isoformat()
    schema["x-registry-summary"] = registry.get("summary", {})
    schema["x-counts"] = {
        "properties": len(properties),
        "pattern_properties": len(pattern_props),
    }
    return schema


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--registry", default=Path("docs/metadata-fields.json"),
                    type=Path, help="Combined registry JSON")
    ap.add_argument("--out", default=Path("docs/metadata-schema.json"),
                    type=Path, help="Output JSON Schema path")
    ap.add_argument("--schema-id",
                    default="https://redtusk.local/schemas/metadata.json",
                    help="JSON Schema $id (informational)")
    args = ap.parse_args(argv)

    registry = json.loads(args.registry.read_text())
    schema = build_schema(registry, schema_id=args.schema_id)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(schema, indent=2, ensure_ascii=False))
    print(f"wrote {args.out}", file=sys.stderr)
    print(f"  properties:        {schema['x-counts']['properties']}", file=sys.stderr)
    print(f"  pattern_properties: {schema['x-counts']['pattern_properties']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
