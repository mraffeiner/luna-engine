# CLAUDE.md: discord-service

Part of the **Luna Engine** multi-repo system (AI VTuber). Sibling repos live in `../`, and the hub is `../luna-engine` (read its `CLAUDE.md` for the big picture). This service is a Discord bot that joins a voice channel. It streams each user's speech to the dashboard (which then calls the STT service) and plays Luna's TTS audio back into the channel. See `README.md` for the API and the WebSocket protocol.

- **Stack:** Deno 2 (npm packages: discord.js 14, @discordjs/voice, @discordjs/opus) and ffmpeg
- **Port:** 5004, with HTTP and WebSocket on the same port. The UI reaches it through Nginx at `/api/discord/`
- **Single file:** `src/main.ts`. It uses the plain `Deno.serve` handler with manual path routing, not Oak

## Commands

```bash
# from ../luna-engine (normal workflow)
docker compose up -d --build discord-service
docker compose logs -f discord-service

# standalone / local (needs ffmpeg)
docker compose up -d --build
deno install --allow-scripts=npm:@discordjs/opus
deno task start                  # loads .env via --env-file
deno check src/main.ts && deno lint
```

There are no tests. Verification needs a real bot token and voice channel: `POST /join-voice {guildId, channelId}`, then speak in the channel and watch the WS frames.

## How it works

- **Incoming audio:** on `receiver.speaking` start, the user's Opus stream goes through the Opus decoder to raw PCM, then into `ffmpeg`, which outputs WAV. The WAV is framed as `[u32 BE name length][name UTF-8][WAV]` and sent as a binary WS frame. JSON events `started_speaking`, `stopped_speaking` and `playback_complete` are also sent.
- **Outgoing audio:** a binary WS frame from the client is played with `createAudioResource` and stops anything that is currently playing.
- There is only **one** WS client (`audioWebSocket`) at a time. A new connection replaces the old one.
- Permissions (`--allow-net --allow-read --allow-run --allow-ffi --allow-env`) are required: `run` for ffmpeg and `ffi` for native opus.

## Conventions (shared by the Deno Luna services)

- Logging uses `std/log` with the formatter `[yyyy-MM-dd HH:mm:ss] - LEVEL: msg`.
- `/health` returns `{status: "OK", timestamp}`.

## Gotchas

- `@discordjs/opus` is a native module. The Dockerfile runs `deno install --allow-scripts=npm:@discordjs/opus@0.10.0` to build it, so a version bump has to change both `deno.json` and the Dockerfile.
- The bot needs the Message Content privileged intent enabled in the developer portal.

## Cross-repo contract

Consumer: `../luna-engine/src/lib/pages/services/discord/discordService.ts`. That file parses the binary frame format, so any change to the framing must be made on both sides.

## Working rules

- Default branch is `development`. Use feature branches and don't push unless asked.
- Never read or print `.env`, which holds the bot token (enforced in `.claude/settings.json`).
