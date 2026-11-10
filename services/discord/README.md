# discord-service

Discord voice bridge for [Luna Engine](../../README.md). A Discord bot joins a voice channel so Luna can talk with people there:

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

### Bot setup

1. Create an application and add a bot.
2. Under **Privileged Gateway Intents**, enable **Message Content**.
3. Invite the bot with the `bot` scope and the **Connect** and **Speak** voice permissions.
4. To get guild and channel IDs, turn on Developer Mode in Discord and use right-click → **Copy ID**.

## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build discord-service`.

**Locally (without Docker):** this needs Deno 2 and ffmpeg. `deno install --allow-scripts` can't set up the native `@discordjs/opus` binary under Deno (see the comment in the `Dockerfile`), so install without scripts and then put the prebuilt binary in place the way the Dockerfile does.

```bash
deno install
deno task start        # reads .env via --env-file
```

## Troubleshooting

### The bot joins the channel but no speech arrives and nothing plays
Discord requires end-to-end encrypted voice (DAVE). It needs `@discordjs/voice` 0.19 or newer, which `deno.json` pins. If the connection never becomes ready, `/join-voice` returns `500` after 20 seconds. The service log shows the voice connection states.

### The bot can't join the channel or stays silent
The bot needs the **Connect** and **Speak** permissions in that channel. Check the invite permissions and any channel-specific overrides.

## License

[MIT](../../LICENSE) © Matthias Raffeiner
