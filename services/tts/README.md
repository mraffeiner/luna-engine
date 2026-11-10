# tts-service

Text-to-speech backend for [Luna Engine](../../README.md). It gives one API over three TTS engines, and the dashboard picks an engine and voice per request.

| Engine | Where it runs | Notes |
|---|---|---|
| **Azure** | Azure Cognitive Services (cloud) | Neural voices with speaking styles, rate and pitch (through SSML) |
| **Kokoro** | Local `kokoro-tts` container (GPU) | Fast and free. Supports voice blends such as `af_bella+af_sky`, speed and pitch |
| **Sesame** | Local `sesame-tts` container (GPU) | CSM-1B. Experimental |

- **Stack:** Python 3.11, FastAPI, Azure Speech SDK, httpx
- **Port:** 5002
- **Proxied by Luna Engine at:** `/api/tts/`

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check. `engines` lists the engines that are currently reachable |
| `GET` | `/options` | Voices, languages and styles for each engine, used to fill the dashboard's dropdowns |
| `POST` | `/generate` | Synthesizes speech and returns `audio/wav` |

The `POST /generate` body depends on `engine`:

```jsonc
// Azure
{ "engine": "azure", "voice": "en-US-AriaNeural", "text": "Hi!", "language": "en-US",
  "style": "cheerful", "rate": "0%", "pitch": "0%", "save": false }

// Kokoro
{ "engine": "kokoro", "voice": "af_heart", "text": "Hi!", "language": "en-US",
  "speed": 1.0, "pitch": 1.0, "save": false }

// Sesame
{ "engine": "sesame", "voice": "...", "text": "Hi!", "save": false }
```

With `"save": true`, the audio is also written to `output/<engine>_<voice>_<timestamp>.wav`. compose mounts this folder at `output/tts/` in the repo root.

Example:

```bash
curl http://localhost:5002/generate -H 'Content-Type: application/json' \
  -d '{"engine":"kokoro","voice":"af_heart","text":"Hello chat!","language":"en-US"}' \
  -o hello.wav
```

Interactive docs: http://localhost:5002/docs

## Configuration

Copy `.env.example` to `.env` and fill it in:

| Variable | Default | Description |
|---|---|---|
| `AZURE_SUBSCRIPTION` | | Azure Speech resource key. Azure is turned off if this or `AZURE_ENDPOINT` is missing |
| `AZURE_ENDPOINT` | | Azure Speech endpoint URL |
| `KOKORO_API_URL` | `http://kokoro-tts:8880` | OpenAI-compatible Kokoro server (`/v1/audio/speech`, `/health`) |
| `SESAME_API_URL` | `http://sesame-tts:8000` | OpenAI-compatible Sesame CSM server (`/v1/audio/speech`, `/health`) |

The root `docker-compose.yml` also passes this `.env` to the `kokoro-tts` and `sesame-tts` containers. Those containers read `HF_TOKEN` (needed by Sesame to download the gated CSM-1B model from Hugging Face) and Kokoro-FastAPI's `USE_GPU`, `PYTHONUNBUFFERED` and `PYTHONPATH` (its GPU image already defaults to them). tts-service itself ignores these.

Kokoro and Sesame aren't part of Luna Engine. The root `docker-compose.yml` pulls [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)'s GPU image from GHCR for `kokoro-tts`. For Sesame, run an OpenAI-compatible server and tag its image `sesame-tts`.

Kokoro-FastAPI has no pitch option, so tts-service applies Kokoro's `pitch` itself as varispeed: it scales the sample rate in the returned WAV's header, which shifts pitch and tempo together without touching the samples.

## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build tts-service`.

**Locally (without Docker):**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5002 --reload
```

## License

[MIT](../../LICENSE) © Matthias Raffeiner
