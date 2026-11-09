# Luna Engine

Control center for **Luna**, an AI VTuber. Luna Engine is a SvelteKit web dashboard that drives the conversation loop. It takes in chat and voice, generates a reply with an LLM, speaks it with TTS, and then sends the result to OBS, VTube Studio and Discord. Each capability runs as its own small Docker microservice.

This repo contains:

- **The dashboard**: SvelteKit + Svelte 5 + Tailwind 4, built to static files and served by Nginx. Nginx also proxies `/api/<service>/` to each backend.
- **The orchestration**: `docker-compose.yml` brings up the whole stack.
- **An optional desktop wrapper** (`src-tauri/`): a Tauri 1.x app that runs `docker compose up`, waits for the dashboard, opens it in a native window, and stops the stack when the window closes.

## How it works

```
 Twitch / YouTube chat ──► chat-service ──┐
 Microphone (browser) ───► stt-service ───┤
 Discord voice ──────────► discord-service┤      ┌──────────────────────┐
 StreamElements alerts ──► alerts-service ┴────► │  Luna Engine (UI)    │
                                                 │  prompt → LLM → TTS  │
                                                 └─────────┬────────────┘
             llm-service ◄── generate reply ───────────────┤
             tts-service ◄── synthesize speech ────────────┤
                 ├─ kokoro-tts (local, GPU)                │
                 ├─ sesame-tts (local, GPU, experimental)  │
                 └─ Azure Speech (cloud)                   │
             obs-service ◄── subtitles ────────────────────┤
             vts-service ◄── avatar parameters ────────────┤
         discord-service ◄── play audio in voice channel ──┘
          docker-service ◄── start/stop containers, stream logs
```

The engine loop lives in the browser (`src/lib/pages/EnginePage.svelte`):

1. New chat messages, transcribed speech and alerts are added to the **prompt**. The prompt is a system prompt plus named sections such as `conversation`, and you can edit and save templates on the *Prompt Templates* page. Templates are stored in the browser's `localStorage`.
2. **Think**: the prompt goes to the selected LLM. There is an optional *prepass*, where a second LLM call rewrites the first answer.
3. **Speak**: the reply is synthesized with the selected TTS engine and played in the browser. It is also sent to Discord when that is enabled, and the text is shown as a subtitle. With *interruptable* turned on, the reply is split at punctuation so new input can cut it off.
4. The spoken text is added to the `conversation` section, and the loop waits for the next trigger.

Engine modes:

- **REACT** (default): Luna only responds when there is new input.
- **AUTO**: Luna keeps talking even without new input.

The engine starts paused.

## Repositories

Every service is its own repo and must be cloned **next to** this one. The compose file builds them from `../<service>`.

| Repo | Port | Stack | Purpose |
|---|---|---|---|
| [`luna-engine`](https://github.com/mraffeiner/luna-engine) | 8080 | SvelteKit, Nginx, Tauri | Dashboard and orchestration (this repo) |
| [`docker-service`](https://github.com/mraffeiner/docker-service) | 5000 | Python, FastAPI | Start and stop service containers, stream their logs |
| [`llm-service`](https://github.com/mraffeiner/llm-service) | 5001 | Python, FastAPI | Streams LLM replies from OpenAI, Groq, Gemini or a local OpenAI-compatible server |
| [`tts-service`](https://github.com/mraffeiner/tts-service) | 5002 | Python, FastAPI | One TTS API on top of Azure, Kokoro and Sesame |
| [`stt-service`](https://github.com/mraffeiner/stt-service) | 5003 | Python, FastAPI | Speech-to-text with Whisper (OpenAI or Groq) and Silero VAD |
| [`discord-service`](https://github.com/mraffeiner/discord-service) | 5004 | Deno, discord.js | Joins a voice channel, streams users' speech out and plays Luna's audio in |
| [`alerts-service`](https://github.com/mraffeiner/alerts-service) | 5005 | Deno, Oak | Relays StreamElements alerts (follows, subs, tips and so on) over a WebSocket |
| [`obs-service`](https://github.com/mraffeiner/obs-service) | 5006 | Deno, Oak | Writes subtitles to an OBS text source and lists scenes |
| [`vts-service`](https://github.com/mraffeiner/vts-service) | 5007 | Python, FastAPI | Controls VTube Studio model parameters through the plugin API |
| [`chat-service`](https://github.com/mraffeiner/chat-service) | 8005 | Python, FastAPI | Twitch and YouTube live chat, sent to the UI over a WebSocket |

Two more containers come from third-party images that you build or pull yourself:

| Container | Port | What it should be |
|---|---|---|
| `kokoro-tts` | 8880 | An OpenAI-compatible Kokoro server exposing `/v1/audio/speech` and `/health`, e.g. [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) (GPU image), tagged as `kokoro-tts` |
| `sesame-tts` | 8000 | An OpenAI-compatible Sesame CSM-1B server exposing `/v1/audio/speech`, tagged as `sesame-tts`. It only starts with `--profile experimental` |

Both need an NVIDIA GPU with the NVIDIA Container Toolkit installed.

## Setup

### Prerequisites

Luna Engine is developed and run on **Linux**. Other platforms aren't tested or maintained.

- Docker Engine 20.10+ with Compose v2
- An NVIDIA GPU and the NVIDIA Container Toolkit, needed for `kokoro-tts` and `sesame-tts`. Remove those services if you only use Azure TTS.
- [Deno](https://deno.com) 2.x, only needed for local frontend development
- Rust and Cargo plus Tauri 1.x's system libraries (`webkit2gtk-4.0`, `libsoup2`, `gtk3`), only needed to build the desktop app. On Arch-based distros, `webkit2gtk` (4.0) is in the AUR

### 1. Clone everything side by side

```bash
mkdir LunaEngine && cd LunaEngine
for r in luna-engine docker-service llm-service tts-service stt-service \
         discord-service alerts-service obs-service vts-service chat-service; do
  git clone https://github.com/mraffeiner/$r.git
done
```

The resulting layout:

```
LunaEngine/
├── luna-engine/      ← run compose from here
├── docker-service/
├── llm-service/
└── ...
```

### 2. Configure each service

Each service reads a `.env` file in its own repo root. These files are git-ignored. Every service repo ships a `.env.example` to start from:

```bash
for d in ../*-service; do [ -f "$d/.env" ] || cp "$d/.env.example" "$d/.env"; done
```

Then fill in the values you need. See each service's README for details. A quick summary:

| Service | Required `.env` values |
|---|---|
| docker-service | none (it mounts `/var/run/docker.sock`) |
| llm-service | at least one of `OPENAI_API_KEY`, `GROQ_API_KEY` + `GROQ_BASE_URL`, `GEMINI_API_KEY` + `GOOGLE_BASE_URL`, or a local server at `LOCAL_BASE_URL` |
| stt-service | `OPENAI_API_KEY` and/or `GROQ_API_KEY` |
| tts-service | `AZURE_SUBSCRIPTION` + `AZURE_ENDPOINT` for Azure. Kokoro and Sesame need no keys |
| discord-service | `DISCORD_TOKEN`, optionally `DISCORD_GUILD_ID` + `DISCORD_CHANNEL_ID` as the default voice channel |
| chat-service | Twitch: `TWITCH_OAUTH_TOKEN`, `TWITCH_CLIENT_ID`, `TWITCH_NICK`, `TWITCH_CHANNELS`. YouTube: `YOUTUBE_CHANNEL_ID` plus a `youtube_secret.json` OAuth client file |
| alerts-service | `STREAMELEMENTS_JWT_TOKEN` |
| obs-service | `OBS_WEBSOCKET_ADDRESS`, `OBS_WEBSOCKET_PASSWORD`, `OBS_SUBTITLE_SOURCE_NAME` |
| vts-service | none (an empty file is fine; it connects to VTube Studio on the host at port 8001) |

> **Note:** compose currently points `kokoro-tts` and `sesame-tts` at `../stt-service/.env`, so that file must exist even if you don't use STT.

> **Note:** compose expects these files to exist even when you don't use the service: an `.env` for every service (the copy loop above handles that), and `chat-service/youtube_secret.json`. Create an empty `youtube_secret.json` if you don't use YouTube.

### Programs on the host

vts-service, obs-service and llm-service's `local` provider connect to programs running on your machine: VTube Studio (port 8001; it works under Steam Proton), OBS (4455) and LM Studio or a similar server (1234). The compose file maps `host.docker.internal` to the host with `extra_hosts: host-gateway`, so the containers can reach them. Make sure each program listens on an address the Docker bridge can reach, not just `127.0.0.1`. LM Studio, for example, needs *Serve on Local Network*. Also check that your firewall allows traffic from the Docker network.

### 3. Start the stack

```bash
cd luna-engine
npm run compose:up          # docker compose up -d --build
# with the experimental Sesame TTS:
docker compose --profile experimental up -d --build
```

Open **http://localhost:8080**.

Other scripts in `package.json`:

| Script | What it does |
|---|---|
| `compose:build` | Build all images |
| `compose:start` / `compose:stop` / `compose:restart` | Start, stop or restart existing containers |
| `compose:recreate` | Rebuild and force-recreate all containers |
| `compose:down` | Stop and remove containers |
| `prune:image` | Remove dangling images |
| `tauri:build` | Build the desktop wrapper (`cargo build` in `src-tauri/`) |
| `build:all` | Build the Docker images and the desktop wrapper |

### 4. Use the dashboard

- **Engine Control Center**: start or pause the engine, switch between REACT and AUTO, toggle the LLM prepass, interruptable speech and saving TTS audio, and see what each stage produced.
- **Docker Service**: start or stop individual service containers and follow their logs live.
- **Prompt Templates**: edit the system prompt and the user prompt sections, and save or load templates.
- **One page per service** (LLM, TTS, STT, Discord, Chat, Alerts, OBS, VTS): pick models and voices, connect accounts, and test each service on its own.

Audio saved with *Save TTS* ends up in `luna-engine/output/tts/`.

## Development

The dashboard calls every backend through relative `/api/<service>/` paths, which Nginx proxies inside the compose network (see `nginx.conf`). The simplest workflow is to run the full stack with compose and rebuild the `luna-engine` container after making changes:

```bash
docker compose up -d --build luna-engine
```

`deno task dev` (Vite) serves the UI with hot reload, but its `/api` proxy is out of date. It sends everything to `localhost:5000` and strips only `/api`, so `/api/llm/models` ends up at docker-service as `/llm/models`. Until `vite.config.ts` gets one proxy entry per service that mirrors `nginx.conf`, use the compose-served UI on port 8080 for anything that calls a backend.

Code checks:

```bash
deno install            # or npm install
deno task check         # svelte-check / type check
deno task lint          # prettier + eslint
deno task format
```

Project layout:

```
src/
├── routes/                 # single-page app shell (+layout, +page)
└── lib/
    ├── components/         # Sidebar, cards, controls, banners
    ├── pages/
    │   ├── EnginePage.svelte   # the think → speak loop
    │   ├── prompt/             # prompt templates and sections
    │   └── services/<name>/    # one page + API client per service
    └── shared/             # global state, constants, text utils
src-tauri/                  # Tauri 1.x desktop wrapper
nginx.conf                  # static hosting + /api reverse proxy
docker-compose.yml          # the whole stack
```

### Desktop app (Tauri)

```bash
cd src-tauri && cargo build      # or: npm run tauri:build
```

`src-tauri/icons/icon.png` is a blank placeholder. Tauri 1.x on Linux refuses to compile without it, so replace it rather than delete it.

Run the resulting binary **from the `luna-engine/` directory**, because it runs `docker compose` in its current working directory. It waits up to 60 s for `http://localhost:8080` to respond and then shows the window. Closing the window runs `docker compose stop`.

## Known issues

- The TTS output directory is hard-coded to `output/` inside `tts-service`. The host side of that mount is `luna-engine/output/tts`.
- `kokoro-tts` and `sesame-tts` have no build context. You have to build or pull their images and tag them yourself.
- There are no automated tests.

## License

[MIT](LICENSE) © Matthias Raffeiner
