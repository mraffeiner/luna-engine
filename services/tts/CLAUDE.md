# CLAUDE.md: tts-service

Part of the **Luna Engine** monorepo (AI VTuber). The root `CLAUDE.md` covers the big picture, and the dashboard lives in `../../app`. This service is Luna's voice: one TTS API over Azure (cloud), Kokoro and Sesame (both local GPU containers). See `README.md` for the request formats.

- **Stack:** Python 3.11, FastAPI, uvicorn, Azure Speech SDK, httpx
- **Port:** 5002. The UI reaches it through Nginx at `/api/tts/`
- **Single file:** `src/app.py`

## Commands

```bash
# from the repo root (normal workflow)
docker compose up -d --build tts-service kokoro-tts
docker compose logs -f tts-service

# local, without Docker
pip install -r requirements.in && uvicorn src.app:app --port 5002 --reload
```

There are no tests. Verify with `curl localhost:5002/health` (which lists the reachable engines) and a `/generate` call that writes a `.wav` (see the README).

## How it works

- `TTSRequest` is a union of `AzureTTSRequest`, `KokoroTTSRequest` and `SesameTTSRequest`, selected by the `engine` literal. `/generate` dispatches on the type with `isinstance` and returns `audio/wav` bytes.
- **Azure** builds SSML (style through `mstts:express-as`, plus rate and pitch) and needs `AZURE_SUBSCRIPTION` and `AZURE_ENDPOINT`.
- **Kokoro and Sesame** send an OpenAI-style `POST {URL}/v1/audio/speech` to the `kokoro-tts:8880` and `sesame-tts:8000` containers. Those are third-party images that aren't in any Luna repo.
- **Kokoro pitch** is varispeed done in tts-service, not by Kokoro: `apply_varispeed_pitch` scales the sample rate and byte rate in the WAV's `fmt ` chunk. Kokoro is called with `stream: false` so it returns one complete WAV.
- `GET /options` is a **hard-coded** catalog of voices, languages and styles that the UI uses for its dropdowns. When you add a voice or engine, update it here.
- With `save: true`, the audio is also written to `output/<engine>_<voice>_<timestamp>.wav`. The path is hard-coded on purpose, after env-based config misbehaved. compose mounts it at `output/tts/` in the repo root.

To add an engine, touch all of these:

1. a `TTSEngine` enum value
2. a request model added to the `TTSRequest` union
3. a `synthesize_with_*` function
4. the dispatch in `/generate`
5. the `/health` check
6. the `/options` entry
7. `TTS_ENGINES` and a form component in `../../app`

## Conventions (shared by all Python Luna services)

- Logging format: `[%(asctime)s] - %(levelname)s: %(message)s` with datefmt `%Y/%m/%d %H:%M:%S`. The `lifespan` hook re-formats the `uvicorn.access` logger to match.
- `GET /health` returns `{"status": "OK", "timestamp": <iso>, ...}`. Here it also includes `engines`.
- Dependencies are listed in `requirements.in` without pins.

## Gotchas

- The root compose file passes this service's `.env` to `kokoro-tts` and `sesame-tts` too (`HF_TOKEN`, Kokoro's `USE_GPU`/`PYTHON*`). tts-service ignores those keys, so don't remove them as unused.
- The UI normalizes text per engine before sending it (`normalizeTtsInput` in `../../app/src/lib/shared/utils.ts`).

## Cross-repo contract

Consumer: `../../app/src/lib/pages/services/tts/ttsService.ts`. There is one form component per engine: `AzureTtsForm.svelte`, `KokoroTtsForm.svelte` and `SesameTtsForm.svelte`.

## Working rules

- Don't push unless asked.
- Never read or print `.env`, which holds API keys (enforced in the root `.claude/settings.json`).
