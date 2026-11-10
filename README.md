# Luna Engine

Control center for **Luna**, an AI VTuber. Luna Engine is a SvelteKit web dashboard that drives the conversation loop. It takes in chat and voice, generates a reply with an LLM, speaks it with TTS, and then sends the result to OBS, VTube Studio and Discord. Each capability runs as its own small Docker microservice, and everything lives in this repo.

## Contents

- [How it works](#how-it-works)
- [Repository layout](#repository-layout)
- [Setup](#setup)
- [Desktop app](#desktop-app)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

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

The engine loop runs in the browser (`app/src/lib/pages/EnginePage.svelte`):

1. New chat messages, transcribed speech and alerts are added to the **prompt**. The prompt is a system prompt plus named sections such as `conversation`. Templates can be edited and saved on the *Prompt Templates* page and are stored in the browser's `localStorage`.
2. **Think**: the prompt goes to the selected LLM. An optional *prepass* lets a second LLM call rewrite the first answer.
3. **Speak**: the reply is synthesized with the selected TTS engine and played in the browser. It is also sent to Discord when that is enabled, and the text is shown as a subtitle. With *interruptable* turned on, the reply is split at punctuation so new input can cut it off.
4. The spoken text is added to the `conversation` section, and the loop waits for the next trigger.

Each prompt section has a character limit. When a section grows past it, its oldest lines are dropped. There is no long-term memory beyond that window.

The engine starts paused and has two modes:

- **REACT** (default): Luna only responds when there is new input.
- **AUTO**: Luna keeps talking even without new input.

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

Each folder has its own README with its API, configuration and troubleshooting.

Two more containers come from third-party images. Both need an NVIDIA GPU with the NVIDIA Container Toolkit:

| Container | Port | Image |
|---|---|---|
| `kokoro-tts` | 8880 | [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)'s GPU image (`ghcr.io/remsky/kokoro-fastapi-gpu`), pulled automatically |
| `sesame-tts` | 8000 | An OpenAI-compatible Sesame CSM-1B server exposing `/v1/audio/speech`, tagged `sesame-tts`. There is no public image, so it has to be built separately. It only starts with `--profile experimental` |

## Setup

### Prerequisites

Luna Engine is developed and run on **Linux**. Other platforms aren't tested or maintained.

- Docker Engine 20.10+ with Compose v2
- An NVIDIA GPU and the NVIDIA Container Toolkit for `kokoro-tts` and `sesame-tts`. Without a GPU, remove those services from `docker-compose.yml` and use Azure TTS.
- [Deno](https://deno.com) 2.x, only for local frontend development
- Rust 1.77.2+ and the [Tauri 2 Linux prerequisites](https://v2.tauri.app/start/prerequisites/#linux), only for the [desktop app](#desktop-app)

### 1. Clone

```bash
git clone https://github.com/mraffeiner/luna-engine.git
cd luna-engine
```

The compose project name is pinned to `luna-engine` in `docker-compose.yml`, so the folder name doesn't matter.

### 2. Configure the services

Services that need configuration read a git-ignored `.env` file in their own folder, starting from the `.env.example` next to it. compose refuses to start if any of these files is missing, even for unused services, so create all of them:

```bash
for d in services/*/; do [ -f "$d.env.example" ] && [ ! -f "$d.env" ] && cp "$d.env.example" "$d.env"; done
touch services/chat/youtube_secret.json   # replace with the OAuth client file if YouTube is used
```

`youtube_secret.json` has to exist before the first start. Otherwise Docker creates a directory with that name for the bind mount.

Then fill in the values for the services you use. Each service's README describes its variables:

| Service | Required `.env` values |
|---|---|
| docker | none, no `.env` |
| llm | at least one of `OPENAI_API_KEY`, `GROQ_API_KEY` + `GROQ_BASE_URL`, `GEMINI_API_KEY` + `GOOGLE_BASE_URL`, or a local server at `LOCAL_BASE_URL` |
| stt | `OPENAI_API_KEY` and/or `GROQ_API_KEY` |
| tts | `AZURE_SUBSCRIPTION` + `AZURE_ENDPOINT` for Azure. The same file is passed to `kokoro-tts` and `sesame-tts`: `HF_TOKEN` for Sesame's gated model, plus optional Kokoro settings |
| discord | `DISCORD_TOKEN`, optionally `DISCORD_GUILD_ID` + `DISCORD_CHANNEL_ID` as the default voice channel |
| chat | Twitch: `TWITCH_OAUTH_TOKEN`, `TWITCH_CLIENT_ID`, `TWITCH_NICK`, `TWITCH_CHANNELS`. YouTube: `YOUTUBE_CHANNEL_ID` plus the `youtube_secret.json` OAuth client file |
| alerts | `STREAMELEMENTS_JWT_TOKEN` |
| obs | `OBS_WEBSOCKET_ADDRESS`, `OBS_WEBSOCKET_PASSWORD`, `OBS_SUBTITLE_SOURCE_NAME` |
| vts | none, no `.env` |

### 3. Prepare programs on the host

Some services connect to programs on the Docker host rather than to other containers:

| Service | Program | Default port |
|---|---|---|
| vts-service | VTube Studio (plugin API) | 8001 |
| obs-service | OBS Studio (obs-websocket) | 4455 |
| llm-service, `local` provider | Ollama (default), LM Studio or another OpenAI-compatible server | 11434 / 1234 |

The compose file maps `host.docker.internal` to the host with `extra_hosts: host-gateway`, so the containers can reach these programs. Each program has to listen on an address the Docker bridge can reach, not only `127.0.0.1`. See [Troubleshooting](#a-service-cant-reach-a-program-on-the-host) if a service can't connect.

### 4. Start the stack

From the repo root:

```bash
docker compose up -d --build
# with the experimental Sesame TTS:
docker compose --profile experimental up -d --build
```

Then open **http://localhost:8080**.

| Command | What it does |
|---|---|
| `docker compose up -d --build <service>` | Rebuild and restart one service, e.g. `llm-service` |
| `docker compose logs -f <service>` | Follow one service's logs |
| `docker compose stop` / `start` | Stop or start the stack without removing containers |
| `docker compose down` | Stop and remove the containers |

The same commands exist as `compose:*` scripts in `app/package.json`.

### 5. Use the dashboard

- **Engine Control Center**: start or pause the engine, switch between REACT and AUTO, toggle the LLM prepass, interruptable speech and saving TTS audio, and see what each stage produced.
- **Docker Service**: start or stop individual service containers and follow their logs live.
- **Prompt Templates**: edit the system prompt and the user prompt sections, and save or load templates.
- **One page per service** (LLM, TTS, STT, Discord, Chat, Alerts, OBS, VTS): pick models and voices, connect accounts, and test each service on its own.

Audio saved with *Save TTS* ends up in `output/tts/`.

## Desktop app

`app/src-tauri/` is an optional Tauri 2 wrapper. It runs `docker compose up`, waits up to 60 seconds for the dashboard, opens it in a native window, and stops the stack when the window is closed.

```bash
cd app/src-tauri && cargo build
cd ../.. && ./app/src-tauri/target/debug/LunaEngine
```

Run the binary from the **repo root**, because it runs `docker compose` in its current working directory. See [`app/README.md`](app/README.md#desktop-app-tauri) for details.

## Security

Luna Engine is a single-user tool meant to run on one machine. None of the services have authentication.

- Every port in `docker-compose.yml` is bound to `127.0.0.1`, so only the local machine can reach the dashboard and the services. Docker's published ports bypass host firewalls such as ufw, so this binding is what keeps the rest of the network out. Without it, anyone who can reach a port can use the configured API keys (llm, tts, stt), play audio in the Discord call or write to OBS.
- To open the dashboard from another device, put port 8080 behind a reverse proxy with authentication rather than publishing it on all interfaces.
- docker-service mounts `/var/run/docker.sock`, which is root-equivalent access to the host. It only acts on containers of the `luna-engine` compose project and returns `404` for any other container.

## Troubleshooting

This section covers problems that affect the whole stack. Problems with a single service are in that service's README:

| Service | Covers |
|---|---|
| [llm](services/llm/README.md#troubleshooting) | Local models not listed, authentication errors |
| [tts](services/tts/README.md#troubleshooting) | Missing engines |
| [stt](services/stt/README.md#troubleshooting) | Transcription failing, models not listed |
| [discord](services/discord/README.md#troubleshooting) | No audio in the voice channel, permissions |
| [chat](services/chat/README.md#troubleshooting) | YouTube login, live chat and quota errors |
| [alerts](services/alerts/README.md#troubleshooting) | No alerts arriving |
| [obs](services/obs/README.md#troubleshooting) | No connection, subtitles not updating |
| [vts](services/vts/README.md#troubleshooting) | Connection and plugin approval |

### `docker compose up` fails with `env file ... not found`

compose needs every `.env` file it references, even for services that aren't used. Run the copy loop from [Configure the services](#2-configure-the-services).

### `services/chat/youtube_secret.json` is a directory

The file was missing when the stack first started, so Docker created a directory for the bind mount. Remove the directory (it's owned by root) and create the file: either the OAuth client JSON or an empty file if YouTube isn't used.

### A service can't reach a program on the host

This applies to vts-service, obs-service and llm-service's `local` provider.

- Check that the program is running and its API or server is enabled on the expected port.
- The program has to listen on an address containers can reach. A server bound to `127.0.0.1` only accepts connections from the host itself, so bind it to `0.0.0.0` or enable its LAN option.
- Host firewalls (ufw, firewalld, nftables) may block traffic from the Docker bridge to the host. Allow the Docker networks (by default inside `172.16.0.0/12`) to reach that port, e.g. with ufw: `sudo ufw allow from 172.16.0.0/12 to any port 4455 proto tcp`.
- From the host, `curl` the program's address to make sure it answers at all.

### Changes to a `.env` file have no effect

`docker compose restart` doesn't reload `.env` files. Recreate the container instead: `docker compose up -d <service>`.

### The desktop app shows an error page

The window opens after waiting up to 60 seconds for the dashboard. On the first start, building the images usually takes longer. Run `docker compose build` once before starting the app.

### The desktop app doesn't compile

Missing system libraries are the usual cause. Install the [Tauri 2 Linux prerequisites](https://v2.tauri.app/start/prerequisites/#linux) for the distribution. If `rustup` reports that no default toolchain is configured, run `rustup default stable`.

## Development

- Frontend: see [`app/README.md`](app/README.md).
- Services: each `services/<name>/README.md` covers its API and how to run it outside Docker.
- A change to a service's API usually also needs a change to its client in `app/src/lib/pages/services/<name>/<name>Service.ts`. With everything in one repo, both go in the same commit.

There are no automated tests.

### Known issues

- The TTS output directory is hard-coded to `output/` inside tts-service. The host side of that mount is `output/tts/` in the repo root.
- `sesame-tts` has no build context and no public image. An OpenAI-compatible Sesame CSM-1B server has to be built separately and tagged `sesame-tts`.

### History

Until November 2026 the services lived in separate repos (`mraffeiner/<name>-service`). Their full histories were merged into this repo, so `git log --follow services/<name>/...` reaches back to each service's first commit.

## License

[MIT](LICENSE) © Matthias Raffeiner
