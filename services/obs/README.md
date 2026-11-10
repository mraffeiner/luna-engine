# obs-service

[OBS Studio](https://obsproject.com/) integration for [Luna Engine](../../README.md). It connects to OBS through **obs-websocket v5** and lets the dashboard show Luna's current spoken line as a subtitle in a text source. It also lists scenes.

If the connection drops, it reconnects every 5 seconds.

- **Stack:** Deno 2, Oak, obs-websocket-js
- **Port:** 5006
- **Proxied by Luna Engine at:** `/api/obs/`

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check. Includes `obsConnected` |
| `GET` | `/scenes` | Returns the OBS scene list. Gives `503` when OBS isn't connected |
| `POST` | `/subtitle` | Body `{ "text": "..." }`. Sets the text of the configured subtitle source |

```bash
curl -X POST http://localhost:5006/subtitle -H 'Content-Type: application/json' -d '{"text":"Hello chat!"}'
```

## Setup

1. In OBS, open **Tools → WebSocket Server Settings**, enable the server and set a password. The default port is 4455.
2. Add a **Text (GDI+ / FreeType 2)** source to your scene for the subtitles, and note its name.
3. Copy `.env.example` to `.env` and fill it in:

| Variable | Default | Description |
|---|---|---|
| `OBS_WEBSOCKET_ADDRESS` | | e.g. `ws://host.docker.internal:4455` when OBS runs on the Docker host |
| `OBS_WEBSOCKET_PASSWORD` | | The password set in OBS |
| `OBS_SUBTITLE_SOURCE_NAME` | | Name of the text source to update |
| `PORT` | `5006` | HTTP port |

> `host.docker.internal` is mapped to the host through `extra_hosts` in compose.

## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build obs-service`.

**Locally (without Docker):**

```bash
deno task dev      # with file watching
deno task start
```

## Troubleshooting

### `obsConnected` stays `false`
Check that the WebSocket server is enabled in OBS and that address and password match. When OBS runs on the Docker host, see [Troubleshooting](../../README.md#troubleshooting) in the root README for host connectivity.

### `/subtitle` fails although OBS is connected
`OBS_SUBTITLE_SOURCE_NAME` must exactly match the name of a text source in OBS.

## License

[MIT](../../LICENSE) © Matthias Raffeiner
