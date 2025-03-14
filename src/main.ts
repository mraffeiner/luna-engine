import {
  Client,
  GatewayIntentBits,
  VoiceChannel,
  ChannelType,
} from "discord.js";
import { joinVoiceChannel, VoiceConnection } from "@discordjs/voice";

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
const audioStreams = new Set();
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
    adapterCreator: (channel as VoiceChannel).guild.voiceAdapterCreator,
  });
  console.log(
    `Connected to voice channel ${channel.name} in guild ${guild.name}`
  );

  connection.receiver.speaking.on("start", (userId) => {
    console.log(`User ${userId} started speaking`);
    const stream = connection!.receiver.subscribe(userId);
    activeStreams.set(userId, stream);

    stream.on("data", (chunk: Uint8Array) => {
      // Send the chunk through the WebSocket connection.
      if (audioWebSocket?.readyState === WebSocket.OPEN) {
        audioWebSocket.send(chunk);
      }
    });
  });

  connection.receiver.speaking.on("end", (userId) => {
    console.log(`User ${userId} stopped speaking`);
    const stream = activeStreams.get(userId);
    if (stream) {
      stream.destroy();
      activeStreams.delete(userId);
    }
  });
}

function disconnectFromVoiceChannel() {
  if (connection) {
    connection.destroy();
    connection = null;
    audioStreams.clear();
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
