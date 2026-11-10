# vts-service

[VTube Studio](https://denchisoft.com/) integration for [Luna Engine](../../README.md). It connects to the VTube Studio plugin API with [pyvts](https://github.com/Genteki/pyvts) so the dashboard can create and drive custom tracking parameters on Luna's avatar. The main use is voice-based motion: the dashboard updates parameters about 30 times per second while Luna is speaking.

- **Stack:** Python 3.11, FastAPI, pyvts
- **Port:** 5007
- **Proxied by Luna Engine at:** `/api/vts/`

## API

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/health` | | Health check |
| `GET` | `/connect` | | Connects and authenticates with VTube Studio. On first use, VTube Studio shows a prompt where you must allow the plugin. Returns `401` if the plugin isn't approved |
| `GET` | `/list_custom_params` | | Lists the custom parameters on the current model. Returns `502` if VTube Studio reports an API error |
| `POST` | `/create_param` | `{ "name", "min", "max", "default_value", "info" }` | Creates a custom parameter |
| `POST` | `/get_param` | `{ "name" }` | Gets a parameter's current value |
| `POST` | `/set_param` | `{ "name", "value" }` | Sets one parameter |
| `POST` | `/set_params` | `{ "names": [...], "values": [...] }` | Sets several parameters in one call |
| `DELETE` | `/delete_param` | `{ "name" }` | Deletes a custom parameter |

Interactive docs: http://localhost:5007/docs

## Setup

1. In VTube Studio, open **Settings → General → Start API** and enable the plugin API on port **8001** (the default).
2. Start the service and call `/connect`, or use **Connect** on the dashboard's VTS page.
3. Accept the plugin authorization prompt in VTube Studio. The token is saved to `token.txt` in the container's working directory.

No environment variables or `.env` file are needed. The service connects to `host.docker.internal:8001`, which means VTube Studio running on the Docker host. compose maps that name to the host with `extra_hosts: ["host.docker.internal:host-gateway"]`.


## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build vts-service`.

**Locally (without Docker):** change the host in `src/app.py` to `localhost`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5007 --reload
```

## Troubleshooting

### `/connect` returns `401`
The plugin wasn't approved. Accept the authorization prompt in VTube Studio and call `/connect` again.

### `/connect` returns `500`
The service can't reach VTube Studio. Check that the API is enabled on port 8001 and see [Troubleshooting](../../README.md#troubleshooting) in the root README for host connectivity.

### The plugin has to be approved again after an update
`token.txt` isn't stored on a volume, so the token is lost each time the container is recreated.

## License

[MIT](../../LICENSE) © Matthias Raffeiner
