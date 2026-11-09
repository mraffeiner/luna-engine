# CLAUDE.md: obs-service

Part of the **Luna Engine** multi-repo system (AI VTuber). Sibling repos live in `../`, and the hub is `../luna-engine` (read its `CLAUDE.md` for the big picture). This service connects to **OBS Studio** through obs-websocket v5 so the dashboard can write Luna's current spoken line into a text source as a subtitle, and list scenes. See `README.md` for the API and OBS setup.

- **Stack:** Deno 2, Oak (`deno.land/x/oak@v12.6.1`), `npm:obs-websocket-js@5`
- **Port:** 5006 (env `PORT`). The UI reaches it through Nginx at `/api/obs/`
- **Single file:** `src/main.ts`

## Commands

```bash
# from ../luna-engine (normal workflow)
docker compose up -d --build obs-service
docker compose logs -f obs-service

# standalone / local
docker compose up -d --build
deno task dev                    # --watch
deno check src/main.ts && deno lint
```

There are no tests. Verify with `curl localhost:5006/health` (check `obsConnected`), then `curl -X POST localhost:5006/subtitle -H 'Content-Type: application/json' -d '{"text":"test"}'` and watch the text source in OBS.

## How it works

- `connectToObs()` connects with `OBS_WEBSOCKET_ADDRESS` and `OBS_WEBSOCKET_PASSWORD`. It retries every 5 s on failure and on `ConnectionClosed`, and the `isConnecting` flag prevents overlapping attempts.
- `GET /scenes` calls `GetSceneList`. `POST /subtitle {text}` calls `SetInputSettings` on the input named by `OBS_SUBTITLE_SOURCE_NAME`, setting `inputSettings.text`. Both return 503 while disconnected.
- `.env` is loaded with `std/dotenv` `loadSync({ export: true })`, so the service also works without compose's `env_file`.

## Conventions (shared by the Deno Luna services)

- Logging uses `std/log` with the formatter `[yyyy-MM-dd HH:mm:ss] - LEVEL: msg`.
- `/health` returns `{status: "OK", timestamp, obsConnected}`.
- Imports are mapped in `deno.json`.

## Gotchas

- OBS runs on the host, so the address is usually `ws://host.docker.internal:4455`. That only resolves because of the `extra_hosts: host-gateway` entry in compose. Keep it.

## Cross-repo contract

Consumer: `../luna-engine/src/lib/pages/services/obs/obsService.ts`. The engine loop writes `subtitles.text`, and the OBS page sends it to this service.

## Working rules

- Default branch is `development`. Use feature branches and don't push unless asked.
- Never read or print `.env`, which holds the OBS password (enforced in `.claude/settings.json`).
