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

client.on("ready", () => {
  console.log(`Logged in as ${client.user?.tag}!`);
});

const token = Deno.env.get("DISCORD_TOKEN");
if (!token) {
  throw new Error("DISCORD_TOKEN environment variable not set.");
}
client.login(token);

async function connectToVoiceChannel(guildId: string, channelId: string) {
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
}

function disconnectFromVoiceChannel() {
  if (connection) {
    connection.destroy();
    connection = null;
    audioStreams.clear();
    console.log("Disconnected from voice channel");
  }
}

// Helper function for API responses
function apiResponse(body: string, status = 200) {
  return new Response(body, { status });
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

  socket.onopen = () => {
    console.log("WebSocket connection established");
  };

  socket.onmessage = (event: MessageEvent) => {
    console.log("Received message from WebSocket client:", event.data);
    // In this example, we don't expect messages from the client,
    // but you could handle them here if needed.
  };

  socket.onclose = () => {
    console.log("WebSocket connection closed");
  };

  socket.onerror = (event: Event) => {
    console.error("WebSocket error:", event);
  };
  return { socket, response };
}

// Combined API and WebSocket server
const handler = async (request: Request): Promise<Response> => {
  const url = new URL(request.url);

  if (request.headers.get("upgrade") === "websocket") {
    const { socket, response } = handleWebSocket(request);
    audioWebSocket = socket;
    return response;
  }

  if (url.pathname === "/join-voice") {
    try {
      const { guildId, channelId } = await request.json();
      if (!guildId || !channelId) {
        return apiResponse("Missing guildId or channelId", 400);
      }
      await connectToVoiceChannel(guildId, channelId);
      return apiResponse("Connected to voice channel");
    } catch (error) {
      return handleApiError(error);
    }
  } else if (url.pathname === "/leave-voice") {
    disconnectFromVoiceChannel();
    return apiResponse("Disconnected from voice channel");
  } else if (url.pathname === "/record") {
    const { userId } = await request.json();

    if (!connection) {
      return apiResponse("Not connected to a voice channel", 400);
    }
    if (!userId) {
      return apiResponse("Missing userId", 400);
    }

    try {
      const stream = connection.receiver.subscribe(userId, {
        end: {
          behavior: 1, //EndBehaviorType.AfterSilence,
          duration: 500,
        },
      });

      // Send data to WebSocket server (itself now)
      stream.on("data", (chunk: Uint8Array) => {
        if (audioWebSocket?.readyState === WebSocket.OPEN) {
          audioWebSocket.send(chunk);
        }
      });
      audioStreams.add(userId);

      return apiResponse(`Recording started for user ${userId}`);
    } catch (error) {
      return handleApiError(error);
    }
  } else if (url.pathname === "/health") {
    return apiResponse("OK");
  }

  return apiResponse("Not Found", 404);
};

Deno.serve({ port: 5004 }, handler);
