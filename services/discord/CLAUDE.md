# CLAUDE.md: discord-service

Part of the **Luna Engine** monorepo (AI VTuber). The root `CLAUDE.md` covers the big picture, and the dashboard lives in `../../app`. This service is a Discord bot that joins a voice channel. It streams each user's speech to the dashboard (which then calls the STT service) and plays Luna's TTS audio back into the channel. See `README.md` for the API and the WebSocket protocol.

- **Stack:** Deno 2 (npm packages: discord.js 14, @discordjs/voice 0.19 with DAVE via `@snazzah/davey`, @discordjs/opus) and ffmpeg
- **Port:** 5004, with HTTP and WebSocket on the same port. The UI reaches it through Nginx at `/api/discord/`
- **Single file:** `src/main.ts`. It uses the plain `Deno.serve` handler with manual path routing, not Oak

## Commands

```bash
# from the repo root (normal workflow)
docker compose up -d --build discord-service
docker compose logs -f discord-service

# local, without Docker (needs ffmpeg; see the opus gotcha below)
deno install
deno task start                  # loads .env via --env-file
deno check src/main.ts && deno lint
```

There are no tests. Verification needs a real bot token and voice channel: `POST /join-voice {guildId, channelId}`, then speak in the channel and watch the WS frames.

## How it works

- **Incoming audio:** on `receiver.speaking` start, the user's Opus stream goes through the Opus decoder to raw PCM, then into `ffmpeg`, which outputs WAV. The WAV is framed as `[u32 BE name length][name UTF-8][WAV]` and sent as a binary WS frame. JSON events `started_speaking`, `stopped_speaking` and `playback_complete` are also sent.
- **Outgoing audio:** a binary WS frame from the client is played with `createAudioResource` and stops anything that is currently playing.
- `/join-voice` waits up to 20 s for the voice connection to reach `Ready` (`entersState`). If it doesn't, the bot leaves and the request returns 500. Voice connection state changes are logged.
- `/join-voice` uses `guildId` and `channelId` from the body and falls back to the `DISCORD_GUILD_ID` / `DISCORD_CHANNEL_ID` env vars when they're empty, which is the dashboard's default.
- There is only **one** WS client (`audioWebSocket`) at a time. A new connection replaces the old one.
- Permissions (`--allow-net --allow-read --allow-run --allow-ffi --allow-env --allow-sys=cpus,networkInterfaces,hostname`) are required: `run` for ffmpeg, `ffi` for native opus, and `sys` because the opus loader reads `process.report` (glibc detection) when it starts.

## Conventions (shared by the Deno Luna services)

- Logging uses `std/log` with the formatter `[yyyy-MM-dd HH:mm:ss] - LEVEL: msg`.
- `/health` returns `{status: "OK", timestamp}`.

## Gotchas

- `@discordjs/opus` is a native module that picks its prebuilt binary by glibc version. Deno always reports glibc 2.38 to npm packages, no 2.38 binary exists, and the source-build fallback can't run under Deno (no `node-gyp`). So `deno install --allow-scripts` fails. The Dockerfile skips the install scripts, downloads the glibc-2.35 binary (matching the Ubuntu 22.04 base) and puts it in the `...-glibc-2.38` folder the loader looks in. A version bump of `@discordjs/opus`, or a base image whose glibc or Deno-reported Node ABI (`node-v108`) changes, has to update `deno.json` and those Dockerfile paths together.
- The bot needs the Message Content privileged intent enabled in the developer portal.
- Since March 2026 Discord rejects voice clients without DAVE (end-to-end encryption). `@discordjs/voice` below 0.19 has no DAVE: the bot still appears in the channel, but the connection never becomes ready, so no speech arrives and playback goes straight to `autopaused`. DAVE comes from the native `@snazzah/davey`, a regular dependency of `@discordjs/voice`. Don't downgrade below 0.19.

## Contract with the app

Consumer: `../../app/src/lib/pages/services/discord/discordService.ts`. That file parses the binary frame format, so any change to the framing must be made on both sides.

## Working rules

- Don't push unless asked.
- Never read or print `.env`, which holds the bot token (enforced in the root `.claude/settings.json`).
