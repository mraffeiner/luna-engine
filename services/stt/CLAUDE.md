# CLAUDE.md: stt-service

Part of the **Luna Engine** monorepo (AI VTuber). The root `CLAUDE.md` covers the big picture, and the dashboard lives in `../../app`. This service transcribes audio clips (the browser mic, or Discord voice relayed by the UI). Silero VAD trims silence first, then Whisper runs on OpenAI or Groq. See `README.md` for the API.

- **Stack:** Python 3.11, FastAPI, uvicorn, torch + torchaudio (VAD only), `openai`, `groq`
- **Port:** 5003. The UI reaches it through Nginx at `/api/stt/`
- **Single file:** `src/app.py`

## Commands

```bash
# from the repo root (normal workflow)
docker compose up -d --build stt-service
docker compose logs -f stt-service

# local, without Docker (needs ffmpeg + libsndfile)
pip install -r requirements.in && uvicorn src.app:app --port 5003 --reload
```

There are no tests. Verify with `curl localhost:5003/transcribe -F audio=@clip.wav -F model=whisper-large-v3-turbo`.

## How it works

- `lifespan` loads Silero VAD from `torch.hub` (`snakers4/silero-vad`), which needs network access on the first start. If loading fails, `vad_model` is `None`.
- `POST /transcribe` (multipart `audio`, `model`):
  1. writes the upload to a temp `.wav`
  2. `extract_speech_only` keeps only the speech segments, resampled to `TARGET_SAMPLE_RATE`
  3. the clip goes to OpenAI or Groq depending on which dict, `OPENAI_MODELS` or `GROQ_MODELS`, contains the model
  4. temp files are cleaned up
- `GET /models` only lists models whose provider API key is set.
- To add a model, add it to the right dict. The UI fills its dropdown from `/models`.

## Conventions (shared by all Python Luna services)

- Logging format: `[%(asctime)s] - %(levelname)s: %(message)s` with datefmt `%Y/%m/%d %H:%M:%S`. The `lifespan` hook re-formats the `uvicorn.access` logger to match.
- `GET /health` returns `{"status": "OK", "timestamp": <iso>}`.
- Dependencies are listed in `requirements.in` without pins.

## Gotchas

- The image is large because of PyTorch. Avoid adding more ML dependencies without a reason.
- the root `docker-compose.yml` also gives this service's `.env` to `kokoro-tts` and `sesame-tts`, so renaming or removing the file breaks those containers.

## Cross-repo contract

Consumer: `../../app/src/lib/pages/services/stt/sttService.ts`. The recording UI is in `SttPage.svelte`, which uses MediaRecorder with webm or mp3.

## Working rules

- Don't push unless asked.
- Never read or print `.env`, which holds API keys (enforced in the root `.claude/settings.json`).
