# stt-service

Speech-to-text backend for [Luna Engine](../../README.md). The dashboard records the microphone in the browser and uploads the clip here to be transcribed.

Before transcription, the audio goes through **[Silero VAD](https://github.com/snakers4/silero-vad)**, which removes silence and keeps only the speech. Silent clips are rejected, and less audio is sent to the API. Transcription itself uses Whisper models from **OpenAI** or **Groq**.

- **Stack:** Python 3.11, FastAPI, PyTorch/torchaudio (VAD), `openai`, `groq`
- **Port:** 5003
- **Proxied by Luna Engine at:** `/api/stt/`

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/models` | Models whose provider has a key configured, as `{ "models": [{ "value", "label" }] }` |
| `POST` | `/transcribe` | Multipart form upload. Fields: `audio` (file) and `model` (default `whisper-large-v3`). Returns `{ "text": "..." }` |

Available models:

| Provider | Model IDs |
|---|---|
| OpenAI | `whisper-1`, `gpt-4o-transcribe` |
| Groq | `whisper-large-v3`, `whisper-large-v3-turbo`, `distil-whisper-large-v3-en` |

Example:

```bash
curl http://localhost:5003/transcribe -F audio=@clip.wav -F model=whisper-large-v3-turbo
```

Interactive docs: http://localhost:5003/docs

## Configuration

Copy `.env.example` to `.env` and fill it in:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Enables the OpenAI models |
| `GROQ_API_KEY` | Enables the Groq models |

The Silero VAD model is downloaded from `torch.hub` on startup, so the first start needs internet access.

> In the root `docker-compose.yml`, `kokoro-tts` and `sesame-tts` also load this `.env`.

## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build stt-service`.

**Locally (without Docker):** this needs `ffmpeg` and `libsndfile` on the system.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5003 --reload
```

The image is large because it installs PyTorch, which is only used for VAD.

## License

[MIT](../../LICENSE) © Matthias Raffeiner
