#!/usr/bin/env python3
"""Submit a corpus directory to RedTusk concurrently.

Usage:
  python3 scripts/submit_corpus.py /home/coz/cstorage/mbzdls \
      --from-file /tmp/corpus_filenames.txt \
      --concurrency 16 \
      --url http://localhost:8000
"""

import argparse
import asyncio
import sys
from pathlib import Path

import aiohttp


async def submit(session: aiohttp.ClientSession, url: str, path: Path, sem: asyncio.Semaphore) -> tuple[str, str]:
    async with sem:
        try:
            data = aiohttp.FormData()
            data.add_field("file", open(path, "rb"), filename=path.name, content_type="application/octet-stream")
            async with session.post(f"{url}/v1/jobs", data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status in (200, 201, 202):
                    j = await resp.json()
                    return path.name, j.get("id", "?")
                else:
                    text = await resp.text()
                    return path.name, f"HTTP {resp.status}: {text[:80]}"
        except Exception as e:
            return path.name, f"ERROR: {e}"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus_dir", help="Directory containing corpus files")
    ap.add_argument("--from-file", help="File listing filenames (one per line, relative to corpus_dir)")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--ext", nargs="*", help="Only submit files with these extensions (e.g. .doc .xls)")
    args = ap.parse_args()

    corpus = Path(args.corpus_dir)

    if args.from_file:
        names = [line.strip() for line in Path(args.from_file).read_text().splitlines() if line.strip()]
        paths = [corpus / name for name in names if (corpus / name).exists()]
    elif args.ext:
        exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.ext}
        paths = [p for p in corpus.iterdir() if p.suffix.lower() in exts and p.is_file()]
    else:
        paths = [p for p in corpus.iterdir() if p.is_file()]

    print(f"Submitting {len(paths)} files with concurrency={args.concurrency} to {args.url}", flush=True)

    sem = asyncio.Semaphore(args.concurrency)
    ok = err = 0

    connector = aiohttp.TCPConnector(limit=args.concurrency + 4)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [submit(session, args.url, p, sem) for p in paths]
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            name, result = await coro
            if result.startswith("ERROR") or result.startswith("HTTP"):
                err += 1
                print(f"[{i}/{len(paths)}] FAIL {name}: {result}", flush=True)
            else:
                ok += 1
                if i % 50 == 0:
                    print(f"[{i}/{len(paths)}] submitted {ok} ok, {err} err", flush=True)

    print(f"\nDone: {ok} submitted, {err} failed out of {len(paths)}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
