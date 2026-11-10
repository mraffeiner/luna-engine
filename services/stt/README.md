# stt-service

Speech-to-text backend for [Luna Engine](../../README.md). The dashboard records the microphone in the browser and uploads the clip here to be transcribed.

Before transcription, the audio goes through **[Silero VAD](https://github.com/snakers4/silero-vad)**, which removes silence and keeps only the speech. Clips without speech return `*noises*` without calling the API at all, and less audio is sent for the rest. Transcription itself uses Whisper models from **OpenAI** or **Groq**.

- **Stack:** Python 3.11, FastAPI, PyTorch (Silero VAD), ffmpeg, `openai`, `groq`
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

## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build stt-service`.

**Locally (without Docker):** this needs `ffmpeg` on the system.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5003 --reload
```

The image is large because it installs PyTorch, which is only used for VAD.

## Troubleshooting

### Every `/transcribe` call fails right after startup
The Silero VAD model is downloaded from `torch.hub` when the service starts. If that fails, for example without internet access, transcription can't work. Check the log for the VAD loading error and restart the service once it has internet access.

### `/models` is empty or misses a provider
Only providers with an API key in `.env` are listed. After changing `.env`, recreate the container with `docker compose up -d stt-service`.

### Every transcription is `*noises*`
Voice activity detection found no speech in the clip, so it wasn't sent to the API. Check that the microphone works, that the right input device is selected in the browser, and that the input level isn't too low.

## License

[MIT](../../LICENSE) © Matthias Raffeiner
