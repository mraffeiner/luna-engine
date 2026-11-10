# alerts-service

Stream alerts relay for [Luna Engine](../../README.md). It connects to the **StreamElements** realtime socket, converts each alert (follows, subs, gift subs, cheers, tips, raids and so on) into one common format, and broadcasts it to every connected WebSocket client. Luna can then react to alerts on stream.

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

Copy `.env.example` to `.env` and fill it in:

| Variable | Default | Description |
|---|---|---|
| `STREAMELEMENTS_JWT_TOKEN` | | Your JWT token, found in StreamElements under **Account → Channels → Show secrets** |
| `PORT` | `5005` | HTTP port |

## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build alerts-service`.

**Locally (without Docker):** the code doesn't load `.env` itself, so pass it with `--env-file`:

```bash
deno run --env-file --watch --allow-net --allow-env --allow-read src/main.ts
```

## Troubleshooting

### No alerts arrive
- Check the service log for a successful connection to StreamElements. An invalid or expired `STREAMELEMENTS_JWT_TOKEN` is the most common cause. Copy it again from **Account → Channels → Show secrets**.
- Use **Emulate** in the StreamElements dashboard to send a test alert, and check that the dashboard's Alerts page is connected to `/ws`.

### An alert shows up as `unknown`
StreamElements sent an event type the service doesn't map yet. The original name is kept in `originalEventName`.

## License

[MIT](../../LICENSE) © Matthias Raffeiner
