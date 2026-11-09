# llm-service

LLM backend for [Luna Engine](https://github.com/mraffeiner/luna-engine). It gives one streaming API over several OpenAI-compatible providers, so the dashboard can switch models without caring where they run.

Supported providers:

- **OpenAI**
- **Groq**
- **Google Gemini** (through its OpenAI-compatible endpoint)
- **Local**: any OpenAI-compatible server such as LM Studio, Ollama or llama.cpp. The default is `http://host.docker.internal:1234/v1` (LM Studio)

The model list is fetched live from each configured provider.

- **Stack:** Python 3.11, FastAPI, `openai` SDK
- **Port:** 5001
- **Proxied by Luna Engine at:** `/api/llm/`

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/models` | Lists the models of every configured provider as `[{ "provider", "id", "name" }]`. Local models are only included if the local server is reachable |
| `POST` | `/generate` | Streams a chat completion as plain text |

`POST /generate` body:

```json
{
  "provider": "openai",          // openai | groq | google | local
  "model": "gpt-4.1-mini",
  "system_prompt": "You are Luna...",
  "prompt": "Chat: hi Luna!"
}
```

Example:

```bash
curl -N http://localhost:5001/generate \
  -H 'Content-Type: application/json' \
  -d '{"provider":"openai","model":"gpt-4.1-mini","system_prompt":"Be brief.","prompt":"Hello!"}'
```

Interactive docs: http://localhost:5001/docs

## Configuration

Create a `.env` file in the repo root. Set the variables for the providers you want to use. A provider without its key is skipped.

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_BASE_URL` | Groq OpenAI-compatible endpoint, e.g. `https://api.groq.com/openai/v1` |
| `GEMINI_API_KEY` | Google AI Studio API key |
| `GOOGLE_BASE_URL` | Gemini OpenAI-compatible endpoint, e.g. `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `LOCAL_BASE_URL` | Local OpenAI-compatible server (default `http://host.docker.internal:1234/v1`) |

> `host.docker.internal` is mapped to the host through `extra_hosts` in compose. The local server must listen on an address the container can reach, e.g. LM Studio's *Serve on Local Network*.

## Running

**As part of Luna Engine (recommended):** clone this repo next to `luna-engine/` and run `docker compose up -d --build` from `luna-engine/`.

**Standalone:**

```bash
docker compose up -d --build
```

**Locally (without Docker):**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5001 --reload
```
