# alerts-service

Stream alerts relay for [Luna Engine](https://github.com/mraffeiner/luna-engine). It connects to the **StreamElements** realtime socket, converts each alert (follows, subs, gift subs, cheers, tips, raids and so on) into one common format, and broadcasts it to every connected WebSocket client. Luna can then react to alerts on stream.

- **Stack:** Deno 2, Oak, socket.io-client
- **Port:** 5005
- **Proxied by Luna Engine at:** `/api/alerts/`

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `WS` | `/ws` | Pushes alerts as JSON. Send `ping` to get `pong` back |

Alert format:

```jsonc
{
  "id": "...",
  "type": "follow | sub | resub | giftsub | communitygiftsub | tip | cheer | raid | host | test | redemption | merch | charityCampaignDonation | unknown",
  "platform": "twitch | youtube | facebook | trovo | unknown",
  "timestamp": "2025-01-01T12:00:00.000Z",
  "user": "viewer",          // optional fields depending on type
  "recipient": "...",
  "amount": 5,
  "currency": "USD",
  "message": "...",
  "tier": "1000",
  "isGift": false,
  "isCommunity": false,
  "gifter": "...",
  "originalEventName": "event"
}
```

Use **Emulate** in the StreamElements dashboard to send test alerts.

## Configuration

Create a `.env` file in the repo root:

| Variable | Default | Description |
|---|---|---|
| `STREAMELEMENTS_JWT_TOKEN` | | Your JWT token, found in StreamElements under **Account → Channels → Show secrets** |
| `PORT` | `5005` | HTTP port |

## Running

**As part of Luna Engine (recommended):** clone this repo next to `luna-engine/` and run `docker compose up -d --build` from `luna-engine/`.

**Standalone:**

```bash
docker compose up -d --build
```

**Locally (without Docker):**

```bash
deno task dev      # with file watching
deno task start
```

## Known issues

- The `Dockerfile` runs `deno cache src/main.ts` *before* `COPY src`, so that step can't find the file. Move `COPY src ./src` above it if the build fails.
