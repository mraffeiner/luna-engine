# llm-service

LLM backend for [Luna Engine](../../README.md). It gives one streaming API over several OpenAI-compatible providers, so the dashboard can switch models without caring where they run.

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
| `LOCAL_BASE_URL` | Local OpenAI-compatible server (default `http://host.docker.internal:1234/v1`) |

> `host.docker.internal` is mapped to the host through `extra_hosts` in compose. The local server must listen on an address the container can reach, e.g. LM Studio's *Serve on Local Network*.

### Local models

The `local` provider works with any OpenAI-compatible server. Its models appear in `GET /models` once `<LOCAL_BASE_URL>/models` responds.

| Server | `LOCAL_BASE_URL` | Make it reachable from Docker |
|---|---|---|
| LM Studio | `http://host.docker.internal:1234/v1` | Enable *Serve on Local Network* |
| Ollama | `http://host.docker.internal:11434/v1` | Set `OLLAMA_HOST=0.0.0.0`, see below |

**Ollama:** by default it listens on `127.0.0.1` only, which the container can't reach. If you start it by hand, run `OLLAMA_HOST=0.0.0.0 ollama serve`. If it runs as a systemd service, run `sudo systemctl edit ollama`, add the following and then `sudo systemctl restart ollama`:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

`ss -ltn | grep 11434` should then show `0.0.0.0:11434` or `*:11434`.

**Firewall:** with a firewall such as ufw, allow traffic from the Docker networks to the server's port:

```bash
sudo ufw allow from 172.16.0.0/12 to any port 11434 proto tcp comment 'Docker -> Ollama'   # 1234 for LM Studio
```

Other machines on your LAN stay blocked by ufw's default deny, even though the server listens on all interfaces.

If the logs say the local LLM is not available, check that the URL in `Checking local LLM availability at ...` is right and run `curl http://localhost:11434/v1/models` on the host.

## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build llm-service`.

**Locally (without Docker):**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.app:app --host 0.0.0.0 --port 5001 --reload
```

## License

[MIT](../../LICENSE) © Matthias Raffeiner
