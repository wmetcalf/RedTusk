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
from pathlib import Path

import aiohttp


async def submit(session: aiohttp.ClientSession, url: str, path: Path,
                 sem: asyncio.Semaphore) -> tuple[str, str]:
    async with sem:
        try:
            body = await asyncio.to_thread(path.read_bytes)
            data = aiohttp.FormData()
            data.add_field("file", body, filename=path.name,
                           content_type="application/octet-stream")
            async with session.post(f"{url}/v1/jobs", data=data,
                                    timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status in (200, 201, 202):
                    j = await resp.json()
                    return path.name, j.get("id", "?")
                else:
                    text = await resp.text()
                    return path.name, f"HTTP {resp.status}: {text[:80]}"
        except Exception as e:
            return path.name, f"ERROR: {e}"


def _collect_paths(corpus: Path, from_file: str | None, ext: list[str] | None) -> list[Path]:
    """Directory walk for the corpus. Sync on purpose -- see the to_thread call in main()."""
    if from_file:
        names = [ln.strip() for ln in Path(from_file).read_text().splitlines() if ln.strip()]
        return [corpus / name for name in names if (corpus / name).exists()]
    if ext:
        exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in ext}
        return [p for p in corpus.iterdir() if p.suffix.lower() in exts and p.is_file()]
    return [p for p in corpus.iterdir() if p.is_file()]


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus_dir", help="Directory containing corpus files")
    ap.add_argument("--from-file",
                    help="File listing filenames (one per line, relative to corpus_dir)")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--ext", nargs="*",
                    help="Only submit files with these extensions (e.g. .doc .xls)")
    args = ap.parse_args()

    paths = await asyncio.to_thread(
        _collect_paths, Path(args.corpus_dir), args.from_file, args.ext)

    print(f"Submitting {len(paths)} files with concurrency={args.concurrency} "
          f"to {args.url}", flush=True)

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
