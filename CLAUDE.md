# CLAUDE.md: llm-service

Part of the **Luna Engine** multi-repo system (AI VTuber). Sibling repos live in `../`, and the hub is `../luna-engine` (read its `CLAUDE.md` for the big picture). This service generates Luna's replies by streaming chat completions from OpenAI-compatible providers. See `README.md` for the API and env vars.

- **Stack:** Python 3.11, FastAPI, uvicorn, `openai` (AsyncOpenAI), httpx
- **Port:** 5001. The UI reaches it through Nginx at `/api/llm/`
- **Single file:** `src/app.py`

## Commands

```bash
# from ../luna-engine (normal workflow)
docker compose up -d --build llm-service
docker compose logs -f llm-service

# standalone / local
docker compose up -d --build
pip install -r requirements.in && uvicorn src.app:app --port 5001 --reload
```

There are no tests. Verify with `curl localhost:5001/models` and a streaming `curl -N` against `/generate` (see the README), or through the dashboard's LLM page.

## How it works

- There is one `AsyncOpenAI` client per provider: `openai`, `groq`, `google` (Gemini through its OpenAI-compatible base URL) and `local` (default `http://host.docker.internal:1234/v1`, i.e. LM Studio on the host).
- `GET /models` asks each configured provider for its model list concurrently. Local models are only included if the local server responds.
- `POST /generate` takes `{provider, model, system_prompt, prompt}` and returns a `StreamingResponse` of plain-text deltas. The UI reads the stream to the end, then normalizes the text and sends it to TTS.
- To add a provider, add another OpenAI-compatible client and register it in both the `/models` fan-out and the `client_map` in `stream_from_openai_compatible`.

## Conventions (shared by all Python Luna services)

- Logging format: `[%(asctime)s] - %(levelname)s: %(message)s` with datefmt `%Y/%m/%d %H:%M:%S`. The `lifespan` hook re-formats the `uvicorn.access` logger to match.
- `GET /health` returns `{"status": "OK", "timestamp": <iso>}`.
- Dependencies are listed in `requirements.in` without pins.

## Gotchas

- `requirements.in` is **UTF-16 encoded** (with a BOM). pip handles it, but plain-text tools and diffs may show it as binary. Keep the encoding unless you're asked to convert it.
- On Linux, `host.docker.internal` requires an `extra_hosts` entry in compose.

## Cross-repo contract

Consumer: `../luna-engine/src/lib/pages/services/llm/llmService.ts`. The dashboard's default response model and prepass settings are configured there, not here.

## Working rules

- Default branch is `development`. Use feature branches and don't push unless asked.
- Never read or print `.env`, which holds API keys (enforced in `.claude/settings.json`).
