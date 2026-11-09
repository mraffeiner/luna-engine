# CLAUDE.md: vts-service

Part of the **Luna Engine** multi-repo system (AI VTuber). Sibling repos live in `../`, and the hub is `../luna-engine` (read its `CLAUDE.md` for the big picture). This service drives Luna's avatar in **VTube Studio** through its plugin API (pyvts): it creates, reads and sets custom tracking parameters. See `README.md` for the API and setup.

- **Stack:** Python 3.11, FastAPI, uvicorn, pyvts (the image installs `python3-opencv` because pyvts depends on opencv)
- **Port:** 5007. The UI reaches it through Nginx at `/api/vts/`
- **Single file:** `src/app.py`

## Commands

```bash
# from ../luna-engine (normal workflow)
docker compose up -d --build vts-service
docker compose logs -f vts-service

# standalone / local (change host.docker.internal → localhost in src/app.py)
docker compose up -d --build
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
- The module does `import datetime` but `/health` calls `datetime.now()`. Check whether `/health` actually works before relying on it.
- `token.txt` isn't on a volume, so VTS has to approve the plugin again after the container is recreated.
- No `.env` is used, and the compose entry has no `env_file`.

## Cross-repo contract

Consumer: `../luna-engine/src/lib/pages/services/vts/vtsService.ts`. It holds the parameter polling and voice-based motion intervals.

## Working rules

- Default branch is `development`. Use feature branches and don't push unless asked.
