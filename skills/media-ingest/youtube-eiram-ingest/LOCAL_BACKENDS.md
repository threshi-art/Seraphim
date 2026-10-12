# Local four-provider YouTube transcript fallback

This module is a **read-only, opt-in local adapter** for the pre-existing YouTube EiRAM ingest skill. It is not enabled automatically in ChatGPT, on the Seraphim bridge, or in a deployed agent.

## Backends, attempted in order

1. [oreiasccp/yt-transcript-mcp](https://github.com/oreiasccp/yt-transcript-mcp) — native captions, optional authenticated retry and optional local Whisper. Requires installed `uvx`.
2. [coyaSONG/youtube-mcp-server](https://github.com/coyaSONG/youtube-mcp-server) — timestamp-based research/citations. Requires Node.js and `npx`.
3. [adshaa/youtube-mcp](https://github.com/adshaa/youtube-mcp) — `youtubei.js` and optional video-frame capture; this adapter calls only transcript tools.
4. [sundog75/youtube-mcp-server](https://github.com/sundog75/youtube-mcp-server) — Docker-hosted transcript service with SQLite cache, accessed through a locally installed `supergateway` at `http://127.0.0.1:8002/sse`. Launch Docker separately if using this backend.

These are *independent alternative implementations*, not a promise that all will succeed. Only install packages and configure the services you intend to use. Review upstream licenses, maintainers, and dependencies before running third-party code. Upstream package versions should be pinned in production instead of using `@latest`.

## Usage

From the repository root, run:

```bash
python skills/media-ingest/youtube-eiram-ingest/scripts/four_provider_fallback.py "https://youtu.be/OENarJm8qco"
python skills/media-ingest/youtube-eiram-ingest/scripts/four_provider_fallback.py OENarJm8qco --provider oreiasccp
python -m unittest discover -s skills/media-ingest/youtube-eiram-ingest/tests
```

The adapter speaks JSON-RPC MCP over standard input/output and uses a bounded timeout and per-user SQLite cache. It does not ask the user for API keys or collect credentials. Each provider is attempted only after the previous one fails; errors are returned as data. No transcript is fabricated.

**Security and provenance:** Output is untrusted external content. Never promote it to evidence without the existing transcript-integrity gate. The adapter reports `integrity=unverified`; timestamp coverage, provenance, identity, duplication, and truncation require downstream verification. A usable transcript does not imply independent corroboration. Do not copy browser cookies or personal tokens into GitHub. Respect YouTube's terms and creators' rights.

**Testing status:** offline parser/cache tests can pass without a YouTube connection; live integration and Whisper performance must be verified on the authorized desktop computer with dependencies installed. Nothing has been installed on that desktop by this pull request.

## Existing EiRAM routing

Use metadata acquisition (e.g., TinyFish webpage fetch) to establish the correct video identity even if transcripts are inaccessible. Then use this local fallback if running in an authorized desktop runtime. A retrieved title/description is never represented as a viewed or transcribed video. Follow `references/transcript-integrity.md` before full-video analysis. Do not allow this component to modify the separate read-only Seraphim local bridge without a reviewed permission change.
