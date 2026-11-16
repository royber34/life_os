#!/usr/bin/env python3
"""Check the machine before a run spends anything. Prints one line per check; never prints secrets.

    python -I preflight.py <run-dir> [--mcp-config <file>] [--require-treg] [--json]

Checks:
  1. The run folder is outside a synced folder (Proton Drive, OneDrive, Dropbox, iCloud, Google Drive),
     which create conflict copies when agents write in parallel. Copy the run there at close instead.
  2. Python 3.10 or later, and Playwright with Chromium for the render test.
  3. The treg MCP server is configured (in --mcp-config, else ~/.claude.json) and its host answers over HTTPS.
     Any HTTP status counts as reachable; the request carries no credentials.
Exit 0 when every required check passes, 1 when one fails, 2 on a usage error.
With --require-treg a missing or unreachable treg fails the run; without it, it is a warning and the run
must say it fell back to free sources.
"""
import argparse, json, os, socket, ssl, sys, urllib.error, urllib.request
from pathlib import Path

SYNCED = ("proton drive", "onedrive", "dropbox", "icloud", "google drive", "googledrive")


def browsers_dir():
    """Where Playwright keeps its browsers, without starting its driver."""
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        return Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"])
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "ms-playwright"
    if sys.platform == "darwin":
        return Path.home() / "Library/Caches/ms-playwright"
    return Path.home() / ".cache/ms-playwright"


def treg_url(mcp_config):
    paths = [mcp_config] if mcp_config else [Path.home() / ".claude.json"]
    for p in paths:
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        servers = dict(data.get("mcpServers") or {})
        for proj in (data.get("projects") or {}).values():
            servers.update((proj or {}).get("mcpServers") or {})
        for name, cfg in servers.items():
            if "treg" in name.lower() and isinstance(cfg, dict) and cfg.get("url"):
                return cfg["url"]
    return None


def reachable(url, timeout=8):
    """True when the host answers over HTTPS at all. No headers or credentials are sent."""
    host = urllib.request.urlparse(url).hostname
    try:
        socket.getaddrinfo(host, 443)
    except OSError as e:
        return False, f"DNS lookup for {host} failed ({e.__class__.__name__})"
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout,
                               context=ssl.create_default_context())
        return True, f"{host} answered"
    except urllib.error.HTTPError as e:
        return True, f"{host} answered with HTTP {e.code} (expected without credentials)"
    except (urllib.error.URLError, OSError) as e:
        return False, f"{host} did not answer ({e.__class__.__name__})"


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--mcp-config", type=Path)
    ap.add_argument("--require-treg", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    rows = []

    def add(name, ok, detail, required=True):
        rows.append({"check": name, "ok": bool(ok), "required": required, "detail": detail})

    where = str(args.run_dir.resolve()).lower()
    synced = [s for s in SYNCED if s in where]
    add("Run folder is outside synced folders", not synced,
        f"inside {synced[0]}: run locally and copy at close" if synced else str(args.run_dir.resolve()))

    add("Python 3.10 or later", sys.version_info >= (3, 10), sys.version.split()[0])
    try:
        import playwright  # noqa: F401
        cache = browsers_dir()
        found = sorted(cache.glob("chromium-*")) if cache and cache.is_dir() else []
        add("Playwright with Chromium", bool(found),
            f"ready ({found[-1].name})" if found else "Playwright is installed; run: python -m playwright install chromium")
    except ImportError:
        add("Playwright with Chromium", False, "pip install playwright, then python -m playwright install chromium")

    url = treg_url(args.mcp_config)
    if not url:
        add("treg MCP configured", False, "no treg server in the MCP config", required=args.require_treg)
    else:
        ok, detail = reachable(url)
        add("treg MCP reachable", ok, detail, required=args.require_treg)

    failed = [r for r in rows if r["required"] and not r["ok"]]
    if args.json:
        print(json.dumps({"ok": not failed, "checks": rows}, indent=1))
    else:
        for r in rows:
            tag = "pass" if r["ok"] else ("FAIL" if r["required"] else "WARN")
            print(f"{tag}  {r['check']}: {r['detail']}")
        print("PREFLIGHT OK" if not failed else f"PREFLIGHT FAILED: {', '.join(r['check'] for r in failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
