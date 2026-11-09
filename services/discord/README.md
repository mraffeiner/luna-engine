# discord-service

Discord voice bridge for [Luna Engine](https://github.com/mraffeiner/luna-engine). A Discord bot joins a voice channel so Luna can talk with people there:

- **Incoming:** each user's speech is decoded from Opus, converted to WAV with ffmpeg, and sent to the dashboard over a WebSocket. The dashboard then transcribes it with the STT service.
- **Outgoing:** audio the dashboard sends over the same WebSocket (Luna's TTS) is played in the voice channel.

- **Stack:** Deno 2, discord.js, @discordjs/voice, @discordjs/opus, ffmpeg
- **Port:** 5004 (HTTP and WebSocket on the same port)
- **Proxied by Luna Engine at:** `/api/discord/`

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/join-voice` | Body `{ "guildId": "...", "channelId": "..." }`. Joins that voice channel. Empty or missing fields fall back to `DISCORD_GUILD_ID` / `DISCORD_CHANNEL_ID` |
| `POST` | `/leave-voice` | Leaves the voice channel |
| `WS` | any path (`Upgrade: websocket`) | Audio bridge, described below. Only one client is supported |

### WebSocket protocol

**Server to client**

- JSON text events:
  - `{"type":"started_speaking","user":"<name>"}`
  - `{"type":"stopped_speaking","user":"<name>"}`
  - `{"type":"playback_complete"}`
- Binary audio frames: `[uint32 big-endian username length][username UTF-8][WAV bytes]`

**Client to server**

- A binary audio buffer (e.g. WAV), which is played in the voice channel. It interrupts anything that is currently playing.

## Configuration

Copy `.env.example` to `.env` and fill it in:

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Bot token from the [Discord Developer Portal](https://discord.com/developers/applications) |
| `DISCORD_GUILD_ID` | Optional. Default server for `/join-voice` when the dashboard's field is empty |
| `DISCORD_CHANNEL_ID` | Optional. Default voice channel for `/join-voice` when the dashboard's field is empty |

Bot setup:

1. Create an application and add a bot.
2. Under **Privileged Gateway Intents**, enable **Message Content**.
3. Invite the bot with the `bot` scope and the **Connect** and **Speak** voice permissions.
4. To get guild and channel IDs, turn on Developer Mode in Discord and use right-click → **Copy ID**.

## Running

**As part of Luna Engine (recommended):** clone this repo next to `luna-engine/` and run `docker compose up -d --build` from `luna-engine/`.

**Standalone:**

```bash
docker compose up -d --build
```

**Locally (without Docker):** this needs Deno 2 and ffmpeg.

```bash
deno install --allow-scripts=npm:@discordjs/opus
deno task start        # reads .env via --env-file
```

## License

[MIT](LICENSE) © Matthias Raffeiner
