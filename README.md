# Luna Engine

Control center for **Luna**, an AI VTuber. Luna Engine is a SvelteKit web dashboard that drives the conversation loop. It takes in chat and voice, generates a reply with an LLM, speaks it with TTS, and then sends the result to OBS, VTube Studio and Discord. Each capability runs as its own small Docker microservice, and everything lives in this repo.

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

The engine loop lives in the browser (`app/src/lib/pages/EnginePage.svelte`):

1. New chat messages, transcribed speech and alerts are added to the **prompt**. The prompt is a system prompt plus named sections such as `conversation`, and you can edit and save templates on the *Prompt Templates* page. Templates are stored in the browser's `localStorage`.
2. **Think**: the prompt goes to the selected LLM. There is an optional *prepass*, where a second LLM call rewrites the first answer.
3. **Speak**: the reply is synthesized with the selected TTS engine and played in the browser. It is also sent to Discord when that is enabled, and the text is shown as a subtitle. With *interruptable* turned on, the reply is split at punctuation so new input can cut it off.
4. The spoken text is added to the `conversation` section, and the loop waits for the next trigger.

Engine modes:

- **REACT** (default): Luna only responds when there is new input.
- **AUTO**: Luna keeps talking even without new input.

The engine starts paused.

## Repository layout

```
luna-engine/
├── app/                  # dashboard: SvelteKit + Nginx, plus the Tauri desktop wrapper
├── services/
│   ├── docker/   llm/   tts/   stt/   discord/
│   └── alerts/   obs/   vts/   chat/
├── docker-compose.yml    # the whole stack
└── output/tts/           # TTS audio saved with "Save TTS" (git-ignored)
```

| Folder | Container | Port | Stack | Purpose |
|---|---|---|---|---|
| [`app/`](app/) | `luna-engine` | 8080 | SvelteKit, Nginx, Tauri | Dashboard, engine loop, `/api/<service>/` reverse proxy |
| [`services/docker/`](services/docker/) | `docker-service` | 5000 | Python, FastAPI | Start and stop service containers, stream their logs |
| [`services/llm/`](services/llm/) | `llm-service` | 5001 | Python, FastAPI | Streams LLM replies from OpenAI, Groq, Gemini or a local OpenAI-compatible server |
| [`services/tts/`](services/tts/) | `tts-service` | 5002 | Python, FastAPI | One TTS API on top of Azure, Kokoro and Sesame |
| [`services/stt/`](services/stt/) | `stt-service` | 5003 | Python, FastAPI | Speech-to-text with Whisper (OpenAI or Groq) and Silero VAD |
| [`services/discord/`](services/discord/) | `discord-service` | 5004 | Deno, discord.js | Joins a voice channel, streams users' speech out and plays Luna's audio in |
| [`services/alerts/`](services/alerts/) | `alerts-service` | 5005 | Deno, Oak | Relays StreamElements alerts (follows, subs, tips and so on) over a WebSocket |
| [`services/obs/`](services/obs/) | `obs-service` | 5006 | Deno, Oak | Writes subtitles to an OBS text source and lists scenes |
| [`services/vts/`](services/vts/) | `vts-service` | 5007 | Python, FastAPI | Controls VTube Studio model parameters through the plugin API |
| [`services/chat/`](services/chat/) | `chat-service` | 8005 | Python, FastAPI | Twitch and YouTube live chat, sent to the UI over a WebSocket |

Each folder has its own README with its API and configuration.

Two more containers come from third-party images:

| Container | Port | What it should be |
|---|---|---|
| `kokoro-tts` | 8880 | [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)'s GPU image (`ghcr.io/remsky/kokoro-fastapi-gpu`). compose pulls it automatically |
| `sesame-tts` | 8000 | An OpenAI-compatible Sesame CSM-1B server exposing `/v1/audio/speech`, tagged as `sesame-tts`. It only starts with `--profile experimental` |

Both need an NVIDIA GPU with the NVIDIA Container Toolkit installed.

## Setup

### Prerequisites

Luna Engine is developed and run on **Linux**. Other platforms aren't tested or maintained.

- Docker Engine 20.10+ with Compose v2
- An NVIDIA GPU and the NVIDIA Container Toolkit, needed for `kokoro-tts` and `sesame-tts`. Remove those services if you only use Azure TTS.
- [Deno](https://deno.com) 2.x, only needed for local frontend development
- Rust and Cargo plus Tauri 1.x's system libraries (`webkit2gtk-4.0`, `libsoup2`, `gtk3`), only needed to build the desktop app. On Arch-based distros, `webkit2gtk` (4.0) is in the AUR

### 1. Clone

```bash
git clone https://github.com/mraffeiner/luna-engine.git
cd luna-engine
```

Keep the folder name `luna-engine`. The compose project is pinned to that name anyway, because docker-service follows logs on the `luna-engine_default` network.

### 2. Configure the services

Services that need configuration read a `.env` file in their own folder. These files are git-ignored. Each of those services ships a `.env.example` to start from:

```bash
for d in services/*/; do [ -f "$d.env.example" ] && [ ! -f "$d.env" ] && cp "$d.env.example" "$d.env"; done
```

Then fill in the values you need. See each service's README for details. A quick summary:

| Service | Required `.env` values |
|---|---|
| docker | no `.env` (it mounts `/var/run/docker.sock`) |
| llm | at least one of `OPENAI_API_KEY`, `GROQ_API_KEY` + `GROQ_BASE_URL`, `GEMINI_API_KEY` + `GOOGLE_BASE_URL`, or a local server at `LOCAL_BASE_URL` |
| stt | `OPENAI_API_KEY` and/or `GROQ_API_KEY` |
| tts | `AZURE_SUBSCRIPTION` + `AZURE_ENDPOINT` for Azure. This file is also passed to the `kokoro-tts` and `sesame-tts` containers: `HF_TOKEN` for Sesame's gated model, plus optional Kokoro settings |
| discord | `DISCORD_TOKEN`, optionally `DISCORD_GUILD_ID` + `DISCORD_CHANNEL_ID` as the default voice channel |
| chat | Twitch: `TWITCH_OAUTH_TOKEN`, `TWITCH_CLIENT_ID`, `TWITCH_NICK`, `TWITCH_CHANNELS`. YouTube: `YOUTUBE_CHANNEL_ID` (a label; the chat is found through the logged-in account's live broadcast) plus a `youtube_secret.json` OAuth client file |
| alerts | `STREAMELEMENTS_JWT_TOKEN` |
| obs | `OBS_WEBSOCKET_ADDRESS`, `OBS_WEBSOCKET_PASSWORD`, `OBS_SUBTITLE_SOURCE_NAME` |
| vts | no `.env` (it connects to VTube Studio on the host at port 8001) |

> **Note:** compose refuses to start if any service's `.env` is missing, even for services you don't use. The copy loop above creates them all. Also create `services/chat/youtube_secret.json` before the first start (an empty file is fine if you don't use YouTube). Otherwise Docker creates a root-owned *directory* with that name for the bind mount.

### Programs on the host

vts-service, obs-service and llm-service's `local` provider connect to programs running on your machine: VTube Studio (port 8001; it works under Steam Proton), OBS (4455) and LM Studio or a similar server (1234). The compose file maps `host.docker.internal` to the host with `extra_hosts: host-gateway`, so the containers can reach them. Make sure each program listens on an address the Docker bridge can reach, not just `127.0.0.1`. LM Studio, for example, needs *Serve on Local Network*. Also check that your firewall allows traffic from the Docker network.

### 3. Start the stack

From the repo root:

```bash
docker compose up -d --build
# with the experimental Sesame TTS:
docker compose --profile experimental up -d --build
```

Open **http://localhost:8080**.

Useful commands:

| Command | What it does |
|---|---|
| `docker compose up -d --build <service>` | Rebuild and restart one service, e.g. `llm-service` |
| `docker compose logs -f <service>` | Follow one service's logs |
| `docker compose stop` / `start` | Stop or start the stack without removing containers |
| `docker compose down` | Stop and remove the containers |

The same commands exist as `compose:*` scripts in `app/package.json`.

### 4. Use the dashboard

- **Engine Control Center**: start or pause the engine, switch between REACT and AUTO, toggle the LLM prepass, interruptable speech and saving TTS audio, and see what each stage produced.
- **Docker Service**: start or stop individual service containers and follow their logs live.
- **Prompt Templates**: edit the system prompt and the user prompt sections, and save or load templates.
- **One page per service** (LLM, TTS, STT, Discord, Chat, Alerts, OBS, VTS): pick models and voices, connect accounts, and test each service on its own.

Audio saved with *Save TTS* ends up in `output/tts/`.

### Desktop app (optional)

`app/src-tauri/` is a Tauri 1.x wrapper. It runs `docker compose up`, waits for the dashboard, opens it in a native window, and stops the stack when you close the window. See [`app/README.md`](app/README.md#desktop-app-tauri) for build instructions. Run the binary from the **repo root**, where `docker-compose.yml` is.

## Development

- Frontend: see [`app/README.md`](app/README.md).
- Services: each `services/<name>/README.md` covers its API and how to run it outside Docker.
- A change to a service's API usually also needs a change to its client in `app/src/lib/pages/services/<name>/<name>Service.ts`. With everything in one repo, both go in the same commit.

There are no automated tests.

## Known issues

- The TTS output directory is hard-coded to `output/` inside tts-service. The host side of that mount is `output/tts/` in the repo root.
- `sesame-tts` has no build context and no public image. You have to build an OpenAI-compatible Sesame CSM-1B server yourself and tag it `sesame-tts`.

## History

Until November 2026 the services lived in separate repos (`mraffeiner/<name>-service`). Their full histories were merged into this repo, so `git log --follow services/<name>/...` reaches back to each service's first commit.

## License

[MIT](LICENSE) © Matthias Raffeiner
