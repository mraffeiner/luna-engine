# CLAUDE.md: Luna Engine

Monorepo for **Luna**, an AI VTuber: a SvelteKit dashboard (`app/`) that runs the conversation loop, plus nine small Docker microservices (`services/<name>/`). See `README.md` for the architecture diagram, user setup and port table. Each subfolder has its own `CLAUDE.md` with details. Read the one for the area you're changing.

**Platform: Linux-first.** The stack runs with Docker Engine on Linux, and host apps like VTube Studio (under Proton), OBS and LM Studio are reached through `host.docker.internal` (mapped with `extra_hosts: host-gateway`). Don't add Windows- or macOS-specific code or config.

## Layout

| Folder | Container | Port | Stack | Role |
|---|---|---|---|---|
| `app/` | `luna-engine` | 8080 | SvelteKit, Nginx, Tauri | Dashboard, engine loop, `/api/<name>/` reverse proxy |
| `services/docker/` | `docker-service` | 5000 | Python/FastAPI | Start and stop containers, SSE log stream |
| `services/llm/` | `llm-service` | 5001 | Python/FastAPI | Streaming LLM replies (OpenAI, Groq, Google, local) |
| `services/tts/` | `tts-service` | 5002 | Python/FastAPI | TTS over Azure, Kokoro and Sesame |
| `services/stt/` | `stt-service` | 5003 | Python/FastAPI | Whisper STT (OpenAI, Groq) with Silero VAD |
| `services/discord/` | `discord-service` | 5004 | Deno | Discord voice bridge (WS audio in and out) |
| `services/alerts/` | `alerts-service` | 5005 | Deno/Oak | StreamElements alerts → WS |
| `services/obs/` | `obs-service` | 5006 | Deno/Oak | OBS subtitles and scenes |
| `services/vts/` | `vts-service` | 5007 | Python/FastAPI | VTube Studio parameters |
| `services/chat/` | `chat-service` | 8005 | Python/FastAPI | Twitch and YouTube chat → WS |

The folder names are short, but the **container names keep the `-service` suffix**. Container names are used by nginx upstreams, docker-service and `PAGES[].serviceId` in the app, so don't rename them.

## Commands (from the repo root)

```bash
docker compose up -d --build                    # whole stack, UI on http://localhost:8080
docker compose up -d --build llm-service        # rebuild one service
docker compose logs -f llm-service
docker compose --profile experimental up -d     # also starts sesame-tts
```

There is **no test suite**. Verify a service with `curl localhost:<port>/health` and its `/docs`, then check the UI in the running stack. App-specific checks are in `app/CLAUDE.md`.

## Cross-cutting contracts

- Each backend's HTTP/WS API is consumed by exactly one client: `app/src/lib/pages/services/<name>/<name>Service.ts`. An API change and its client update go in the **same commit**.
- Every backend exposes `GET /health` → `{ "status": "OK", "timestamp": ... }`.
- Every service that reads env vars has a `.env.example` (docker and vts have none). When you add or rename an env var, update that service's `.env.example`, its README and, for a service's first variable, its `env_file` entry in compose, all in the same change.

To add a new service, touch all of the following:

1. `services/<name>/` with a Dockerfile, `.env.example`, README and CLAUDE.md
2. a service entry in `docker-compose.yml` with its port bound to `127.0.0.1`, plus an entry in `depends_on` of `luna-engine`
3. a `location /api/<name>/` block in `app/nginx.conf`
4. a `PAGES` entry in `app/src/lib/shared/constants.ts` whose `serviceId` matches the container name
5. a page and client in `app/src/lib/pages/services/<name>/`

## Gotchas

- `name: luna-engine` in compose pins the project name. docker-service only streams logs for containers on the `luna-engine_default` network and only starts or stops containers labelled `com.docker.compose.project=luna-engine`, so keep the pin.
- Every published port is bound to `127.0.0.1` because no service has authentication and Docker bypasses ufw. New services must follow that (`"127.0.0.1:<port>:<port>"`).
- `kokoro-tts` (upstream `ghcr.io/remsky/kokoro-fastapi-gpu`, pinned) and `sesame-tts` are third-party images with no build context. `sesame-tts` only runs with `--profile experimental`. Both load `services/tts/.env` (for `HF_TOKEN` and Kokoro settings), which tts-service shares and ignores.
- compose fails if any referenced `.env` file is missing. docker-service and vts-service read no env vars, so they have no `env_file` and no `.env.example`. Keep it that way unless they gain variables. A missing `services/chat/youtube_secret.json` makes Docker create a directory in its place.
- TTS files saved with "Save TTS" land in `output/tts/` at the repo root (git-ignored).
- History from the former separate repos was merged in, so `git log --follow services/<name>/<file>` shows a file's full history.

## Working rules

- Default branch is `development`. Work on feature branches and don't push without being asked.
- Never read or print `.env` files, `services/chat/youtube_secret.json` or `services/chat/credentials/`. They hold API keys and tokens (enforced in `.claude/settings.json`).
- Prefer small, verifiable changes. There are no tests to catch regressions.
