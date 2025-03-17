import * as log from "https://deno.land/std@0.224.0/log/mod.ts";
import {
  Client,
  GatewayIntentBits,
  VoiceChannel,
  ChannelType,
} from "discord.js";
import {
  AudioReceiveStream,
  joinVoiceChannel,
  VoiceConnection,
} from "@discordjs/voice";
import { opus } from "prism-media";
import { Buffer } from "node:buffer";

import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const wave = require("wavefile");

log.setup({
  handlers: {
    console: new log.ConsoleHandler("INFO", {
      useColors: false,
      formatter: (record: log.LogRecord) =>
        `[${record.datetime.toISOString()}] - ${record.levelName}: ${
          record.msg
        }`,
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
let audioWebSocket: WebSocket | null = null;
const activeStreams = new Map();

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

  connection = joinVoiceChannel({
    channelId: channel.id,
    guildId: channel.guild.id,
    selfDeaf: false,
    selfMute: false,
    adapterCreator: (channel as VoiceChannel).guild.voiceAdapterCreator,
  });
  logger.info(
    `Connected to voice channel ${channel.name} in guild ${guild.name}`
  );

  let pcmData: Buffer[] = [];

  connection.receiver.speaking.on("start", async (userId) => {
    const user = await client.users.fetch(userId);
    const username = user.displayName;
    logger.info(`${username} started speaking`);

    if (!connection) {
      logger.error("Connection is null when user started speaking.");
      return;
    }

    const stream: AudioReceiveStream = connection.receiver.subscribe(userId);
    activeStreams.set(userId, stream);

    const decoder = new opus.Decoder({
      channels: 2,
      frameSize: 960,
      rate: 48000,
    });

    stream.pipe(decoder);
    decoder.on("data", (chunk) => {
      pcmData.push(chunk);
    });
  });

  connection.receiver.speaking.on("end", async (userId) => {
    const user = await client.users.fetch(userId);
    const username = user.displayName;
    logger.info(`${username} stopped speaking`);

    activeStreams.get(userId)?.destroy();
    activeStreams.delete(userId);

    const concatenatedPcmData = Buffer.concat(pcmData);

    // Deinterleave stereo pcm data
    const totalFrames = concatenatedPcmData.length / 4;
    const leftChannel = new Int16Array(totalFrames);
    const rightChannel = new Int16Array(totalFrames);
    for (let i = 0; i < totalFrames; i++) {
      // For each frame, read 2 bytes for left and 2 bytes for right.
      leftChannel[i] = concatenatedPcmData.readInt16LE(i * 4);
      rightChannel[i] = concatenatedPcmData.readInt16LE(i * 4 + 2);
    }

    // Convert to wav
    const wav = new wave.WaveFile();
    wav.fromScratch(2, 48000, "16", [leftChannel, rightChannel]);

    if (audioWebSocket?.readyState === WebSocket.OPEN) {
      // Encode username as UTF-8 bytes
      const usernameBytes = new TextEncoder().encode(username);
      const usernameLength = usernameBytes.length;

      // Create a buffer to hold username length, username, and audio data
      const audioBuffer = wav.toBuffer();
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

    pcmData = [];
  });
}

function disconnectFromVoiceChannel() {
  if (connection) {
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
