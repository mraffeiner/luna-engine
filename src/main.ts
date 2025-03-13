import { Client, GatewayIntentBits, VoiceChannel } from "discord.js";
import {
  joinVoiceChannel,
  EndBehaviorType,
  VoiceConnection,
} from "@discordjs/voice";

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildVoiceStates,
  ],
});

let connection: VoiceConnection | null = null;
const audioStreams = new Map();

declare global {
  var audioWebSocket: WebSocket | null;
}
globalThis.audioWebSocket = null;

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
  const channel = (await guild.channels.fetch(channelId)) as VoiceChannel;
  if (!channel || channel.type !== 2) {
    // 2 represents a voice channel
    throw new Error("Invalid channel ID");
  }
  connection = joinVoiceChannel({
    channelId: channel.id,
    guildId: channel.guild.id,
    adapterCreator: channel.guild.voiceAdapterCreator,
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

// Combined API and WebSocket server
const handler = async (request: Request): Promise<Response> => {
  const url = new URL(request.url);

  if (url.pathname === "/join-voice") {
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }
    try {
      const { guildId, channelId } = await request.json();
      if (!guildId || !channelId) {
        return new Response("Missing guildId or channelId", { status: 400 });
      }
      await connectToVoiceChannel(guildId, channelId);
      return new Response("Connected to voice channel");
    } catch (error) {
      if (error instanceof Error) {
        return new Response(error.message, { status: 500 });
      } else {
        return new Response("An unknown error occurred", { status: 500 });
      }
    }
  } else if (url.pathname === "/leave-voice") {
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }
    disconnectFromVoiceChannel();
    return new Response("Disconnected from voice channel");
  } else if (url.pathname === "/record") {
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }
    const { userId } = await request.json();

    if (!connection) {
      return new Response("Not connected to a voice channel", { status: 400 });
    }
    if (!userId) {
      return new Response("Missing userId", { status: 400 });
    }

    try {
      const stream = connection.receiver.subscribe(userId, {
        end: {
          behavior: EndBehaviorType.AfterSilence,
          duration: 500,
        },
      });

      // Send data to WebSocket server (itself now)
      stream.on("data", (chunk: Uint8Array) => {
        if (globalThis.audioWebSocket?.readyState === WebSocket.OPEN) {
          globalThis.audioWebSocket.send(chunk);
        }
      });
      audioStreams.set(userId, stream);

      return new Response(`Recording started for user ${userId}`);
    } catch (error) {
      if (error instanceof Error) {
        return new Response(error.message, { status: 500 });
      } else {
        return new Response("Unknown error", { status: 500 });
      }
    }
  } else if (url.pathname === "/health") {
    return new Response("OK", { status: 200 });
  } else if (request.headers.get("upgrade") === "websocket") {
    // Handle WebSocket upgrade
    const { socket, response } = Deno.upgradeWebSocket(request);
    globalThis.audioWebSocket = socket;

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
      globalThis.audioWebSocket = null;
    };

    socket.onerror = (event: Event) => {
      console.error("WebSocket error:", event);
    };
    return response;
  }

  return new Response("Not Found", { status: 404 });
};

Deno.serve({ port: 5004 }, handler);
