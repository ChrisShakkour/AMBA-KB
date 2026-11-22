"""Download the Arm source documents listed in raw/sources.json into raw/.

Usage:  python tools/download_sources.py [--force] [filter ...]

  filter   only download entries whose path or document number contains this text,
           e.g.  python tools/download_sources.py CHI AXI-Stream
  --force  re-download files that already exist

Every file is checked against the SHA-256 recorded in sources.json, so you get the exact
issue the wiki cites. Files are fetched from Arm's public documentation service.
"""
import hashlib, json, os, sys, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw")
HEADERS = {"User-Agent": "Mozilla/5.0"}

def main(argv):
    force = "--force" in argv
    filters = [a.lower() for a in argv if not a.startswith("--")]
    entries = json.load(open(os.path.join(ROOT, "sources.json"), encoding="utf-8"))
    ok = skipped = failed = 0
    for e in entries:
        if filters and not any(f in (e["path"] + " " + e["doc"]).lower() for f in filters):
            continue
        dest = os.path.normpath(os.path.join(ROOT, e["path"]))
        if os.path.exists(dest) and not force:
            if hashlib.sha256(open(dest, "rb").read()).hexdigest() == e["sha256"]:
                skipped += 1
                continue
        try:
            req = urllib.request.Request(e["url"], headers=HEADERS)
            data = urllib.request.urlopen(req, timeout=120).read()
        except Exception as exc:
            print(f"FAIL  {e['path']}: {exc}  (manual download: {e['page']})")
            failed += 1
            continue
        if hashlib.sha256(data).hexdigest() != e["sha256"]:
            print(f"WARN  {e['path']}: checksum differs, Arm may have republished it. "
                  f"Saved anyway; check the issue on {e['page']}")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(data)
        print(f"OK    {e['path']}  ({len(data) // 1024} KB)")
        ok += 1
    print(f"\n{ok} downloaded, {skipped} already present, {failed} failed")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
