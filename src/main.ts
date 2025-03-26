import * as log from "https://deno.land/std@0.224.0/log/mod.ts";
import {
  Client,
  GatewayIntentBits,
  VoiceChannel,
  ChannelType,
} from "discord.js";
import {
  AudioPlayer,
  AudioReceiveStream,
  createAudioPlayer,
  createAudioResource,
  EndBehaviorType,
  joinVoiceChannel,
  NoSubscriberBehavior,
  VoiceConnection,
} from "@discordjs/voice";
import { Buffer } from "node:buffer";
import { spawn } from "node:child_process";
import { Transform } from "node:stream";
import { createRequire } from "node:module";
import { Readable } from "node:stream";

const require = createRequire(import.meta.url);
const { OpusEncoder } = require("@discordjs/opus");

log.setup({
  handlers: {
    console: new log.ConsoleHandler("INFO", {
      useColors: false,
      formatter: (record: log.LogRecord) => {
        const extra =
          record.args && record.args.length > 0
            ? " " + record.args.map(String).join(" ")
            : "";
        return `[${record.datetime.toISOString()}] - ${record.levelName}: ${
          record.msg
        }${extra}`;
      },
    }),
  },

  loggers: {
    default: {
      level: "INFO",
      handlers: ["console"],
    },
  },
});

const logger = log.getLogger();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildVoiceStates,
  ],
});

let connection: VoiceConnection | null = null;
let audioPlayer: AudioPlayer | null = null;
let audioWebSocket: WebSocket | null = null;

const activeStreams = new Map<string, AudioReceiveStream>();

client.on("ready", () => {
  logger.info(`Logged in as ${client.user?.tag}!`);
});

const token = Deno.env.get("DISCORD_TOKEN");
if (!token) {
  throw new Error("DISCORD_TOKEN environment variable not set.");
}
client.login(token);

async function connectToVoiceChannel(guildId: string, channelId: string) {
  logger.info(
    "connectToVoiceChannel called with guildId: %s, channelId: %s",
    guildId,
    channelId
  ); // Log
  if (connection) {
    return;
  }
  const guild = await client.guilds.fetch(guildId);
  const channel = await guild.channels.fetch(channelId);

  if (!channel || channel.type !== ChannelType.GuildVoice) {
    throw new Error("Invalid channel ID: Not a voice channel");
  }

  audioPlayer = createAudioPlayer({
    behaviors: {
      noSubscriber: NoSubscriberBehavior.Pause,
    },
  });

  audioPlayer.on("stateChange", (_, newState) => {
    logger.info("Audio player state changed:", newState.status);
    if (newState.status === "idle") {
      audioWebSocket?.send(JSON.stringify({ type: "playback_complete" }));
    }
  });

  connection = joinVoiceChannel({
    channelId: channel.id,
    guildId: channel.guild.id,
    selfDeaf: false,
    selfMute: false,
    adapterCreator: (channel as VoiceChannel).guild.voiceAdapterCreator,
  });

  connection.subscribe(audioPlayer);
  logger.info(
    `Connected to voice channel ${channel.name} in guild ${guild.name}`
  );

  // Set your audio configuration (Discord typically sends mono audio)
  const SAMPLE_RATE = 48000;
  const CHANNELS = 1;

  connection.receiver.speaking.on("start", async (userId) => {
    try {
      const user = await client.users.fetch(userId);
      const username = user.displayName;
      logger.info(`${username} started speaking`);

      // Clear any existing timeout for this user
      if (!connection) {
        logger.error("Connection is null when user started speaking.");
        return;
      }

      if (activeStreams.has(userId) && activeStreams.get(userId)) {
        logger.info(
          `${username} started speaking during active stream. No action taken.`
        );
        return;
      }

      // Start new opus stream for user
      const opusStream = connection.receiver.subscribe(userId, {
        end: {
          behavior: EndBehaviorType.AfterSilence,
          duration: 500,
        },
      });
      activeStreams.set(userId, opusStream);

      // Initialize the Opus decoder
      const opusCodec = new OpusEncoder(SAMPLE_RATE, CHANNELS);
      const opusToPCM = new Transform({
        transform(chunk, _encoding, callback) {
          try {
            const pcmData = opusCodec.decode(chunk);
            callback(null, pcmData);
          } catch (err) {
            if (err instanceof Error) {
              callback(err);
            } else {
              callback(new Error("Unknown Error"));
            }
          }
        },
      });

      // Spawn ffmpeg to convert raw PCM to WAV
      const ffmpeg = spawn("ffmpeg", [
        "-loglevel",
        "error",
        "-f",
        "s16le",
        "-ar",
        SAMPLE_RATE.toString(),
        "-ac",
        CHANNELS.toString(),
        "-i",
        "pipe:0",
        "-c:a",
        "pcm_s16le",
        "-f",
        "wav",
        "pipe:1",
      ]);

      // Pipe the Opus stream through the decoder and into ffmpeg
      opusStream.pipe(opusToPCM).pipe(ffmpeg.stdin);

      // Collect the WAV data chunks
      const wavChunks: Buffer[] = [];
      ffmpeg.stdout.on("data", (chunk) => {
        wavChunks.push(chunk);
        logger.info(
          `ffmpeg out chunk size: ${chunk.length} total chunks: ${wavChunks.length}`
        );
      });

      // Log any ffmpeg errors
      ffmpeg.stderr.on("data", (data) => {
        logger.error(`ffmpeg stderr: ${data}`);
      });

      // When the session is complete, end the ffmpeg input to finalize the WAV file.
      opusStream.on("end", () => {
        logger.info(`Opus stream for ${username} ended, closing ffmpeg`);
        ffmpeg.stdin.end();
      });

      // Finalize and process audio buffer
      ffmpeg.on("close", (code) => {
        if (code !== 0) {
          logger.error(`ffmpeg exited with code ${code}`);
        } else {
          logger.info(
            `Stream finished, processing ${wavChunks.length} chunks for ${username}`
          );
          const finalBuffer = Buffer.concat(wavChunks);
          processAudio(username, finalBuffer);
          logger.info(
            `Finished processing audio for ${username}, final buffer size: ${finalBuffer.length}`
          );
          activeStreams.get(userId)?.destroy();
          activeStreams.delete(userId);
        }
      });
    } catch (error) {
      logger.error("Error processing audio:", error);
    }
  });

  connection.receiver.speaking.on("end", async (userId) => {
    const user = await client.users.fetch(userId);
    const username = user.displayName;
    logger.info(`${username} stopped speaking`);
  });

  // Function to process audio data and send it to the WebSocket
  function processAudio(username: string, audioBuffer: Buffer) {
    if (audioWebSocket?.readyState === WebSocket.OPEN) {
      // Encode username as UTF-8 bytes
      const usernameBytes = new TextEncoder().encode(username);
      const usernameLength = usernameBytes.length;

      // Create a buffer to hold username length, username, and audio data
      const combinedBuffer = new Uint8Array(
        4 + usernameLength + audioBuffer.length
      );

      // Write username length (4 bytes)
      const dataView = new DataView(combinedBuffer.buffer);
      dataView.setUint32(0, usernameLength, false); // Big-endian

      // Write username bytes
      combinedBuffer.set(usernameBytes, 4);

      // Write audio data
      combinedBuffer.set(audioBuffer, 4 + usernameLength);

      // Send the combined buffer
      audioWebSocket.send(combinedBuffer);
    } else {
      logger.info("Audio websocket not open");
    }
  }
}

function playAudio(audioBuffer: ArrayBuffer) {
  if (!audioPlayer || !connection) {
    logger.error("No active voice connection");
    return;
  }

  if (audioPlayer.state.status !== "idle") {
    audioPlayer.stop();
  }

  const stream = Readable.from([new Uint8Array(audioBuffer)]);

  // Create an audio resource from ffmpeg's stdout
  const resource = createAudioResource(stream);
  audioPlayer.play(resource);
}

function disconnectFromVoiceChannel() {
  if (connection) {
    activeStreams.forEach((stream) => {
      stream.destroy();
    });
    activeStreams.clear();
    audioPlayer?.stop();
    audioPlayer?.removeAllListeners();
    audioPlayer = null;

    connection.destroy();
    connection = null;
    logger.info("Disconnected from voice channel");
  }
}

// Helper function for API responses
function apiResponse(body: string, status = 200) {
  return new Response(JSON.stringify({ message: body }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// Helper function to handle API errors
function handleApiError(error: unknown) {
  if (error instanceof Error) {
    return apiResponse(error.message, 500);
  }
  return apiResponse("An unknown error occurred", 500);
}

function handleWebSocket(request: Request) {
  const { socket, response } = Deno.upgradeWebSocket(request);
  audioWebSocket = socket; // Store the WebSocket connection

  audioWebSocket.onopen = () => {
    logger.info("WebSocket connection established");
  };

  audioWebSocket.onmessage = (event: MessageEvent) => {
    logger.info("Received message from WebSocket client:", event.data);
    if (event.data instanceof ArrayBuffer) {
      try {
        playAudio(event.data);
      } catch (error) {
        logger.error("Error trying to play received buffer:", error);
      }
    } else {
      logger.error(
        "Received unsupported data from WebSocket client:",
        event.data
      );
    }
  };

  audioWebSocket.onclose = () => {
    logger.info("WebSocket connection closed");
    audioWebSocket = null;
  };

  audioWebSocket.onerror = (event: Event) => {
    logger.error("WebSocket error:", event);
  };
  return response;
}

// Combined API and WebSocket server
const handler = async (request: Request): Promise<Response> => {
  logger.info("Request received:", request.url); // Log every request
  const url = new URL(request.url);

  if (request.headers.get("upgrade") === "websocket") {
    return handleWebSocket(request);
  }

  if (url.pathname === "/join-voice") {
    try {
      logger.info("Handling /join-voice request"); // Log
      const { guildId, channelId } = await request.json();
      logger.info("Parsed request body:", { guildId, channelId }); // Log parsed body
      if (!guildId || !channelId) {
        return apiResponse("Missing guildId or channelId", 400);
      }
      await connectToVoiceChannel(guildId, channelId);
      logger.info("connectToVoiceChannel called"); // Log
      return apiResponse("Connected to voice channel");
    } catch (error) {
      logger.error("Error in /join-voice handler:", error); // Log errors
      return handleApiError(error);
    }
  } else if (url.pathname === "/leave-voice") {
    disconnectFromVoiceChannel();
    return apiResponse("Disconnected from voice channel");
  } else if (url.pathname === "/health") {
    return apiResponse("OK");
  }

  return apiResponse("Not Found", 404);
};

Deno.serve({ port: 5004 }, handler);
