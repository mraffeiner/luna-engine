# CLAUDE.md: vts-service

Part of the **Luna Engine** monorepo (AI VTuber). The root `CLAUDE.md` covers the big picture, and the dashboard lives in `../../app`. This service drives Luna's avatar in **VTube Studio** through its plugin API (pyvts): it creates, reads and sets custom tracking parameters. See `README.md` for the API and setup.

- **Stack:** Python 3.11, FastAPI, uvicorn, pyvts (the image installs `python3-opencv` because pyvts depends on opencv)
- **Port:** 5007. The UI reaches it through Nginx at `/api/vts/`
- **Single file:** `src/app.py`

## Commands

```bash
# from the repo root (normal workflow)
docker compose up -d --build vts-service
docker compose logs -f vts-service

# local, without Docker (change host.docker.internal → localhost in src/app.py)
pip install -r requirements.in && uvicorn src.app:app --port 5007 --reload
```

There are no tests. Verification needs VTube Studio running on the host with its API enabled on port 8001. Call `/connect`, accept the prompt in VTS, then call `/list_custom_params`.

## How it works

- A global `pyvts.vts` instance is created in `lifespan`. It points at `host.docker.internal:8001`, the plugin is named "VTS Service" by developer "TastiHam", and the auth token goes to `./token.txt`.
- `/connect` connects, requests a token (VTS shows an approval prompt the first time) and authenticates.
- The parameter endpoints wrap pyvts requests (`requestCustomParameter`, `requestSetParameterValue` and so on). `/set_params` sets several values in one call. The UI calls it about every 33 ms for voice-based motion while Luna speaks, so keep it fast and keep the access logs quiet (the access log level is WARNING on purpose).

## Conventions (shared by all Python Luna services)

- Logging format: `[%(asctime)s] - %(levelname)s: %(message)s` with datefmt `%Y/%m/%d %H:%M:%S`.
- `GET /health` returns `{"status": "OK", "timestamp": <iso>}`.
- Dependencies are listed in `requirements.in` without pins.

## Gotchas

- Error paths `return HTTPException(...)` instead of raising it, so failures may come back as HTTP 200 with an error body. Check before relying on status codes.
- `token.txt` isn't on a volume, so VTS has to approve the plugin again after the container is recreated.
- No environment variables are read, but the root `docker-compose.yml` lists `services/vts/.env` as an `env_file`, so the file must exist (it can be empty).
- `host.docker.internal` only resolves because of the `extra_hosts: host-gateway` entry in compose. Keep it. VTube Studio runs under Steam Proton on the host.

## Cross-repo contract

Consumer: `../../app/src/lib/pages/services/vts/vtsService.ts`. It holds the parameter polling and voice-based motion intervals.

## Working rules

- Don't push unless asked.
