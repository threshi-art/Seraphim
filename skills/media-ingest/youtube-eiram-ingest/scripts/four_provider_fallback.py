"""Four-provider YouTube transcript failover for Seraphim (local, read-only).

Dependencies: Python 3.11+ standard library. Each MCP backend is optional.
Only configured subprocesses are launched; no remote code or credentials are stored.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import sqlite3
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
URL_ID = re.compile(r"(?:youtube\.com/(?:watch\?[^#]*?v=|shorts/|live/|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})")
DEFAULT_TIMEOUT = 35
# Explicit argv only; never shell=True. Programs must be installed separately.
PROVIDERS = (
    ("oreiasccp", ("uvx", "yt-transcript-mcp"), ("get_transcript",), "output"),
    ("coyasong", ("npx", "-y", "@coyasong/youtube-mcp-server@latest"), ("get_transcript", "research-video"), "url"),
    ("adshaa", ("npx", "-y", "@inlustris/youtube-mcp@latest"), ("get_transcript",), "url"),
    ("sundog75", ("npx", "-y", "supergateway", "--sse", "http://127.0.0.1:8002/sse"), ("get_transcript_json", "get_transcript"), "url"),
)


def video_id(value: str) -> str:
    value = value.strip()
    if VIDEO_ID.fullmatch(value):
        return value
    matched = URL_ID.search(value)
    if matched:
        return matched.group(1)
    raise ValueError("Expected an 11-character YouTube ID or supported YouTube URL")


def cache_path() -> Path:
    return Path(os.getenv("SERAPHIM_YT_CACHE", str(Path.home() / ".seraphim" / "youtube-cache.sqlite3")))


def cache_get(path: Path, key: str, ttl: int) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS transcripts (video TEXT PRIMARY KEY, saved REAL, payload TEXT)")
        row = db.execute("SELECT saved, payload FROM transcripts WHERE video=?", (key,)).fetchone()
    return json.loads(row[1]) if row and time.time() - row[0] < ttl else None


def cache_put(path: Path, key: str, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS transcripts (video TEXT PRIMARY KEY, saved REAL, payload TEXT)")
        db.execute("INSERT OR REPLACE INTO transcripts VALUES (?, ?, ?)", (key, time.time(), json.dumps(result)))


def read_messages(proc: subprocess.Popen[str], messages: queue.Queue[dict[str, Any]]) -> None:
    if proc.stdout is None:
        return
    for line in proc.stdout:
        try:
            messages.put(json.loads(line))
        except json.JSONDecodeError:
            continue


class MCP:
    def __init__(self, argv: tuple[str, ...], timeout: int):
        self.argv, self.timeout = argv, timeout
        self.proc: subprocess.Popen[str] | None = None
        self.messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self.sequence = 0

    def __enter__(self) -> "MCP":
        self.proc = subprocess.Popen(
            self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        threading.Thread(target=read_messages, args=(self.proc, self.messages), daemon=True).start()
        self.request("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "seraphim-video-retriever", "version": "1.0.0"},
        })
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        return self

    def send(self, message: dict[str, Any]) -> None:
        assert self.proc is not None and self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.sequence += 1
        request_id = self.sequence
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if self.proc is not None and self.proc.poll() is not None:
                raise RuntimeError("Backend exited before a response")
            try:
                msg = self.messages.get(timeout=min(0.25, max(0.01, deadline - time.monotonic())))
            except queue.Empty:
                continue
            if msg.get("id") == request_id:
                if "error" in msg:
                    raise RuntimeError(str(msg["error"])[:500])
                return msg.get("result", {})
        raise TimeoutError(f"MCP {method} timed out after {self.timeout}s")

    def __exit__(self, *_: object) -> None:
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()


def extract_text(result: dict[str, Any]) -> str:
    content = result.get("content", [])
    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"]
        return "\n".join(parts).strip()
    if isinstance(result.get("text"), str):
        return result["text"].strip()
    return ""


def candidate_args(tool_name: str, id_: str) -> list[dict[str, Any]]:
    url = f"https://www.youtube.com/watch?v={id_}"
    if tool_name == "research-video":
        return [{"url": url, "query": "Provide a transcript with timestamps"}]
    return [
        {"url": url}, {"video": url}, {"video_url": url},
        {"videoId": id_}, {"video_id": id_},
    ]


def fetch_provider(name: str, argv: tuple[str, ...], tools: tuple[str, ...], id_: str, timeout: int) -> str:
    with MCP(argv, timeout) as mcp:
        tool_listing = mcp.request("tools/list", {})
        available = {item["name"]: item for item in tool_listing.get("tools", []) if isinstance(item, dict) and "name" in item}
        failures: list[str] = []
        for tool_name in tools:
            if tool_name not in available:
                continue
            schema = available[tool_name].get("inputSchema", {})
            props = schema.get("properties", {}) if isinstance(schema, dict) else {}
            required = set(schema.get("required", [])) if isinstance(schema, dict) else set()
            for candidate in candidate_args(tool_name, id_):
                # Use only advertised properties and satisfy advertised required fields.
                params = {key: value for key, value in candidate.items() if key in props}
                if not params or not required.issubset(params):
                    continue
                try:
                    result = mcp.request("tools/call", {"name": tool_name, "arguments": params})
                    if result.get("isError"):
                        failures.append(extract_text(result)[:100])
                        continue
                    body = extract_text(result)
                    if len(body) >= 60:
                        return body
                except (TimeoutError, RuntimeError) as exc:
                    failures.append(str(exc)[:100])
        raise RuntimeError(f"{name}: no usable transcript; {', '.join(failures[:2])}")


def retrieve(value: str, *, timeout: int = DEFAULT_TIMEOUT, ttl_days: int = 7, provider: str = "all") -> dict[str, Any]:
    id_ = video_id(value)
    cache = cache_path()
    key = f"{id_}:{provider}"
    existing = cache_get(cache, key, ttl_days * 86400)
    if existing:
        return {**existing, "cached": True}
    failures = []
    for name, argv, tools, _ in PROVIDERS:
        if provider not in ("all", name):
            continue
        try:
            body = fetch_provider(name, argv, tools, id_, timeout)
            result = {"video_id": id_, "url": f"https://www.youtube.com/watch?v={id_}",
                      "provider": name, "transcript": body, "cached": False,
                      "integrity": "unverified", "source_type": "mcp-derived"}
            cache_put(cache, key, result)
            return result
        except (OSError, RuntimeError, TimeoutError) as exc:
            failures.append({"provider": name, "error": str(exc)[:300]})
    return {"video_id": id_, "url": f"https://www.youtube.com/watch?v={id_}",
            "transcript": None, "status": "unavailable", "failures": failures}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seraphim four-provider local YouTube transcript fallback")
    parser.add_argument("video", help="Video URL or ID")
    parser.add_argument("--provider", default="all", choices=["all", *(p[0] for p in PROVIDERS)])
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--ttl-days", type=int, default=7)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 180 or not 0 <= args.ttl_days <= 365:
        parser.error("timeout or cache TTL outside supported bounds")
    try:
        print(json.dumps(retrieve(args.video, timeout=args.timeout, ttl_days=args.ttl_days, provider=args.provider),
                         ensure_ascii=False, indent=2))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
