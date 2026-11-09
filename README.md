# docker-service

Container management backend for [Luna Engine](https://github.com/mraffeiner/luna-engine). The dashboard uses it to start and stop the other Luna services and to show their logs live.

It talks to the Docker daemon through the mounted socket (`/var/run/docker.sock`) using [aiodocker](https://github.com/aio-libs/aiodocker).

- **Stack:** Python 3.11, FastAPI, aiodocker
- **Port:** 5000
- **Proxied by Luna Engine at:** `/api/docker/`

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/container_status/{name}` | Returns `{ "status": "<docker state>" }` for one container |
| `POST` | `/start_container/{name}` | Starts an existing container |
| `POST` | `/stop_container/{name}` | Stops a container. It is not removed |
| `GET` | `/container_logs` | **Server-Sent Events** stream of the last 100 lines and live logs of every container on the `luna-engine_default` network. Each event is `{ "service": "<name>", "log": "<line>" }` |

Only one log stream client is allowed at a time. A new request closes the previous stream.

Interactive docs: http://localhost:5000/docs

## Configuration

No environment variables are required. The container needs access to the Docker socket, which `docker-compose.yml` sets up:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

> **Security:** mounting the Docker socket gives this container full control over the host's Docker daemon. Don't expose port 5000 outside your machine.

## Running

**As part of Luna Engine (recommended):** clone this repo next to `luna-engine/` and run `docker compose up -d --build` from `luna-engine/`.

**Standalone:**

```bash
docker compose up -d --build
```

Without the Luna Engine stack, the log stream finds nothing, because it only follows containers on the `luna-engine_default` network.

**Locally (without Docker):**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5000 --reload
```
