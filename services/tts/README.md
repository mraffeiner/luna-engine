# tts-service

Text-to-speech backend for [Luna Engine](https://github.com/mraffeiner/luna-engine). It gives one API over three TTS engines, and the dashboard picks an engine and voice per request.

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

With `"save": true`, the audio is also written to `output/<engine>_<voice>_<timestamp>.wav`. Luna Engine mounts this folder at `luna-engine/output/tts/`.

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

Kokoro and Sesame aren't part of this repo. Run an OpenAI-compatible server for each, e.g. [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) for Kokoro, and tag the images `kokoro-tts` and `sesame-tts` so Luna Engine's compose file can find them.

## Running

**As part of Luna Engine (recommended):** clone this repo next to `luna-engine/` and run `docker compose up -d --build` from `luna-engine/`.

**Standalone:** only Azure works here unless you also run the Kokoro or Sesame containers and point the URLs at them.

```bash
docker compose up -d --build
```

**Locally (without Docker):**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5002 --reload
```

## License

[MIT](LICENSE) © Matthias Raffeiner
