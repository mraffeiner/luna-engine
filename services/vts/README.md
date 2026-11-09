# vts-service

[VTube Studio](https://denchisoft.com/) integration for [Luna Engine](https://github.com/mraffeiner/luna-engine). It connects to the VTube Studio plugin API with [pyvts](https://github.com/Genteki/pyvts) so the dashboard can create and drive custom tracking parameters on Luna's avatar. The main use is voice-based motion: the dashboard updates parameters about 30 times per second while Luna is speaking.

- **Stack:** Python 3.11, FastAPI, pyvts
- **Port:** 5007
- **Proxied by Luna Engine at:** `/api/vts/`

## API

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/health` | | Health check |
| `GET` | `/connect` | | Connects and authenticates with VTube Studio. On first use, VTube Studio shows a prompt where you must allow the plugin |
| `GET` | `/list_custom_params` | | Lists the custom parameters on the current model |
| `POST` | `/create_param` | `{ "name", "min", "max", "default_value", "info" }` | Creates a custom parameter |
| `POST` | `/get_param` | `{ "name" }` | Gets a parameter's current value |
| `POST` | `/set_param` | `{ "name", "value" }` | Sets one parameter |
| `POST` | `/set_params` | `{ "names": [...], "values": [...] }` | Sets several parameters in one call |
| `DELETE` | `/delete_param` | `{ "name" }` | Deletes a custom parameter |

Interactive docs: http://localhost:5007/docs

## Setup

1. In VTube Studio (it runs fine under Steam Proton), open **Settings → General → Start API** and enable the plugin API on port **8001** (the default).
2. Start the service and call `/connect`, or use **Connect** on the dashboard's VTS page.
3. Accept the plugin authorization prompt in VTube Studio. The token is saved to `token.txt` in the container's working directory.

The service doesn't read any environment variables, but Luna Engine's compose file still expects a `.env` file here, so copy `.env.example` (which is empty) to `.env`. It connects to `host.docker.internal:8001`, which means VTube Studio running on the Docker host. compose maps that name to the host with `extra_hosts: ["host.docker.internal:host-gateway"]`.

> `token.txt` isn't stored on a volume, so you have to authorize the plugin again each time the container is recreated.

## Running

**As part of Luna Engine (recommended):** clone this repo next to `luna-engine/` and run `docker compose up -d --build` from `luna-engine/`.

**Standalone:**

```bash
docker compose up -d --build
```

**Locally (without Docker):** change the host in `src/app.py` to `localhost`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5007 --reload
```

## License

[MIT](LICENSE) © Matthias Raffeiner
