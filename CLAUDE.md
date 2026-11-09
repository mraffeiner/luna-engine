# CLAUDE.md: alerts-service

Part of the **Luna Engine** multi-repo system (AI VTuber). Sibling repos live in `../`, and the hub is `../luna-engine` (read its `CLAUDE.md` for the big picture). This service connects to the **StreamElements** realtime socket, converts each alert (follow, sub, tip, raid and so on) into a `StandardizedAlert`, and broadcasts it to WebSocket clients. See `README.md` for the alert format.

- **Stack:** Deno 2, Oak (`deno.land/x/oak@v12.6.1`), `npm:socket.io-client`
- **Port:** 5005 (env `PORT`). The UI reaches it through Nginx at `/api/alerts/`
- **Single file:** `src/main.ts`

## Commands

```bash
# from ../luna-engine (normal workflow)
docker compose up -d --build alerts-service
docker compose logs -f alerts-service

# standalone / local
docker compose up -d --build
deno task dev                    # --watch
deno check src/main.ts && deno lint
```

There are no tests. Verify by connecting to `ws://localhost:5005/ws` (sending `ping` should return `pong`) and firing an **Emulate** alert from the StreamElements dashboard.

## How it works

- `connectToStreamElements()` connects through socket.io to `https://realtime.streamelements.com` (websocket transport) and authenticates with `STREAMELEMENTS_JWT_TOKEN`.
- It listens for `follower`, `subscriber`, `host`, `raid`, `cheer`, `tip`, `test` and `event`. `processStreamElementsEvent()` maps the raw payload to a `StandardizedAlert` using `safeGet()` to read properties defensively. Unmapped types are logged as warnings.
- `broadcastAlert()` sends JSON to every client in `connectedClients` and removes closed sockets.
- There are separate loggers: the default one and `alertsLogger` for alert payloads.

To add an event type, add it to the `eventTypes` listener list, add a `case` in `processStreamElementsEvent`, and extend the `StandardizedAlert["type"]` union, which the UI's `alertsService.ts` mirrors.

## Conventions (shared by the Deno Luna services)

- Logging uses `std/log` with the formatter `[yyyy-MM-dd HH:mm:ss] - LEVEL: msg`.
- `/health` returns `{status: "OK", timestamp}`.
- Imports are mapped in `deno.json`.

## Cross-repo contract

Consumer: `../luna-engine/src/lib/pages/services/alerts/alertsService.ts`, which must stay in sync with the `StandardizedAlert` shape.

## Working rules

- Default branch is `development`. Use feature branches and don't push unless asked.
- Never read or print `.env`, which holds the StreamElements JWT (enforced in `.claude/settings.json`).
