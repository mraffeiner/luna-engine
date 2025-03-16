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
  console.log(`Logged in as ${client.user?.tag}!`);
});

const token = Deno.env.get("DISCORD_TOKEN");
if (!token) {
  throw new Error("DISCORD_TOKEN environment variable not set.");
}
client.login(token);

async function connectToVoiceChannel(guildId: string, channelId: string) {
  console.log(
    "connectToVoiceChannel called with guildId:",
    guildId,
    "channelId:",
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
  console.log(
    `Connected to voice channel ${channel.name} in guild ${guild.name}`
  );

  let pcmData: Buffer[] = [];

  connection.receiver.speaking.on("start", async (userId) => {
    const user = await client.users.fetch(userId);
    const username = user.displayName;
    console.log(`${username} started speaking`);

    if (!connection) {
      console.error("Connection is null when user started speaking.");
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
    console.log(`${username} stopped speaking`);

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
      console.log("Audio websocket not open");
    }

    pcmData = [];
  });
}

function disconnectFromVoiceChannel() {
  if (connection) {
    connection.destroy();
    connection = null;
    console.log("Disconnected from voice channel");
  }
  if (audioWebSocket) {
    audioWebSocket.close();
    audioWebSocket = null;
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
    console.log("WebSocket connection established");
  };

  audioWebSocket.onmessage = (event: MessageEvent) => {
    console.log("Received message from WebSocket client:", event.data);
    // We don't expect messages *from* the client in this example,
    // but you could handle them here if needed.
  };

  audioWebSocket.onclose = () => {
    console.log("WebSocket connection closed");
    audioWebSocket = null;
  };

  audioWebSocket.onerror = (event: Event) => {
    console.error("WebSocket error:", event);
  };
  return response;
}

// Combined API and WebSocket server
const handler = async (request: Request): Promise<Response> => {
  console.log("Request received:", request.url); // Log every request
  const url = new URL(request.url);

  if (request.headers.get("upgrade") === "websocket") {
    return handleWebSocket(request);
  }

  if (url.pathname === "/join-voice") {
    try {
      console.log("Handling /join-voice request"); // Log
      const { guildId, channelId } = await request.json();
      console.log("Parsed request body:", { guildId, channelId }); // Log parsed body
      if (!guildId || !channelId) {
        return apiResponse("Missing guildId or channelId", 400);
      }
      await connectToVoiceChannel(guildId, channelId);
      console.log("connectToVoiceChannel called"); // Log
      return apiResponse("Connected to voice channel");
    } catch (error) {
      console.error("Error in /join-voice handler:", error); // Log errors
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
