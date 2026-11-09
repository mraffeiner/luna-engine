# CLAUDE.md: docker-service

Part of the **Luna Engine** monorepo (AI VTuber). The root `CLAUDE.md` covers the big picture, and the dashboard lives in `../../app`. This service lets the dashboard start and stop the other service containers and stream their logs. See `README.md` for the API.

- **Stack:** Python 3.11, FastAPI, uvicorn, aiodocker
- **Port:** 5000. The UI reaches it through Nginx at `/api/docker/`
- **Single file:** `src/app.py`

## Commands

```bash
# from the repo root (normal workflow)
docker compose up -d --build docker-service
docker compose logs -f docker-service

# local, without Docker
pip install -r requirements.in && uvicorn src.app:app --port 5000 --reload
```

There are no tests. Verify with `curl localhost:5000/health`, `/docs`, and the dashboard's Docker page.

## How it works

- It talks to the host Docker daemon through the mounted `/var/run/docker.sock`. Treat changes here as security-sensitive.
- `/container_status/{name}`, `/start_container/{name}` and `/stop_container/{name}` act on containers by **name**. The names are the `container_name`s in the root `docker-compose.yml`, which the UI's `PAGES[].serviceId` also uses.
- Stopping a container does not remove it. That was a deliberate choice, so keep it that way.
- `/container_logs` is a Server-Sent Events stream (`data: {"service","log"}\n\n`). It follows every container on the `luna-engine_default` network, with one task per container plus a heartbeat. Only one client is allowed at a time: a new request closes the previous Docker client.

## Conventions (shared by all Python Luna services)

- Logging format: `[%(asctime)s] - %(levelname)s: %(message)s` with datefmt `%Y/%m/%d %H:%M:%S`. The `lifespan` hook re-formats the `uvicorn.access` logger to match.
- `GET /health` returns `{"status": "OK", "timestamp": <iso>}`.
- Dependencies are listed in `requirements.in` without pins and installed directly with pip.

## Cross-repo contract

Consumer: `../../app/src/lib/pages/services/docker/dockerService.ts`. Update it together with any API change here.

## Working rules

- Don't push unless asked.
- Never read or print `.env` (enforced in the root `.claude/settings.json`).
