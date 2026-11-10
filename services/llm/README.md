# llm-service

LLM backend for [Luna Engine](../../README.md). It gives one streaming API over several OpenAI-compatible providers, so the dashboard can switch models without caring where they run.

Supported providers:

- **OpenAI**
- **Groq**
- **Google Gemini** (through its OpenAI-compatible endpoint)
- **Local**: any OpenAI-compatible server such as Ollama, LM Studio or llama.cpp. The default is `http://host.docker.internal:11434/v1` (Ollama)

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
  "model": "gpt-6-luna",
  "system_prompt": "You are Luna...",
  "prompt": "Chat: hi Luna!"
}
```

Example:

```bash
curl -N http://localhost:5001/generate \
  -H 'Content-Type: application/json' \
  -d '{"provider":"openai","model":"gpt-6-luna","system_prompt":"Be brief.","prompt":"Hello!"}'
```

Interactive docs: http://localhost:5001/docs

## Configuration

Copy `.env.example` to `.env` and fill it in. Set the variables for the providers you want to use. A provider without its key is skipped.

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_BASE_URL` | Groq OpenAI-compatible endpoint, e.g. `https://api.groq.com/openai/v1` |
| `GEMINI_API_KEY` | Google AI Studio API key |
| `GOOGLE_BASE_URL` | Gemini OpenAI-compatible endpoint, e.g. `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `LOCAL_BASE_URL` | Local OpenAI-compatible server (default `http://host.docker.internal:11434/v1`, Ollama). `.env.example` also has the LM Studio URL as a commented line |

> `host.docker.internal` is mapped to the host through `extra_hosts` in compose. The local server must listen on an address the container can reach, see [Troubleshooting](#troubleshooting).

### Local models

The `local` provider works with any OpenAI-compatible server. Its models appear in `GET /models` once `<LOCAL_BASE_URL>/models` responds.

| Server | `LOCAL_BASE_URL` | Make it reachable from Docker |
|---|---|---|
| Ollama (default) | `http://host.docker.internal:11434/v1` | Set `OLLAMA_HOST=0.0.0.0` |
| LM Studio | `http://host.docker.internal:1234/v1` | Enable *Serve on Local Network* |

## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build llm-service`.

**Locally (without Docker):**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5001 --reload
```

## Troubleshooting

### Local models don't appear in `/models`
The service only lists local models when `<LOCAL_BASE_URL>/models` answers. The log line `Checking local LLM availability at ...` shows the URL it tried.
- Run `curl <LOCAL_BASE_URL>/models` on the host, with `localhost` in place of `host.docker.internal`, to check that the server answers at all.
- The server has to listen on an address containers can reach, not only `127.0.0.1`. LM Studio: enable *Serve on Local Network*. Ollama: set `OLLAMA_HOST=0.0.0.0`, e.g. with `sudo systemctl edit ollama` and `Environment="OLLAMA_HOST=0.0.0.0"` when it runs as a systemd service.
- A host firewall may block traffic from Docker. See [Troubleshooting](../../README.md#troubleshooting) in the root README.

### `Authentication error with <provider> API`
The API key for that provider is missing or invalid in `.env`. After changing `.env`, recreate the container with `docker compose up -d llm-service`. `docker compose restart` doesn't reload `.env` files.

## License

[MIT](../../LICENSE) © Matthias Raffeiner
