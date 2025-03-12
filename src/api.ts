import { API_PORT, API_HOST } from "./config.ts";
import { client } from "./bot.ts";
import { getUserAudioStream, getAllAudioStreams } from "./voice.ts";

// Create HTTP server
export function startApiServer() {
  console.log(`Starting API server on ${API_HOST}:${API_PORT}`);

  // Start the server
  Deno.serve(
    {
      port: API_PORT,
      hostname: API_HOST,
    },
    handleRequest
  );

  console.log(`API server running at http://${API_HOST}:${API_PORT}/`);
}

// Handle HTTP requests
async function handleRequest(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const path = url.pathname;

  // CORS headers
  const headers = new Headers({
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  });

  // Handle preflight requests
  if (request.method === "OPTIONS") {
    return new Response(null, { headers });
  }

  try {
    // Health check endpoint
    if (path === "/health") {
      return new Response(
        JSON.stringify({
          status: "ok",
          connected: client.isReady(),
          guilds: client.guilds.cache.size,
        }),
        { headers: { ...headers, "Content-Type": "application/json" } }
      );
    }

    // Get voice channels endpoint
    if (path === "/voice-channels") {
      const guildId = url.searchParams.get("guildId");

      if (!guildId) {
        return new Response(
          JSON.stringify({ error: "guildId parameter is required" }),
          {
            status: 400,
            headers: { ...headers, "Content-Type": "application/json" },
          }
        );
      }

      const guild = client.guilds.cache.get(guildId);
      if (!guild) {
        return new Response(JSON.stringify({ error: "Guild not found" }), {
          status: 404,
          headers: { ...headers, "Content-Type": "application/json" },
        });
      }

      // Get all voice channels in the guild
      const voiceChannels = guild.channels.cache
        .filter((channel) => channel.isVoiceBased())
        .map((channel) => ({
          id: channel.id,
          name: channel.name,
          members: channel.members?.size || 0,
        }));

      return new Response(JSON.stringify({ voiceChannels }), {
        headers: { ...headers, "Content-Type": "application/json" },
      });
    }

    // Join voice channel endpoint
    if (path === "/join-voice" && request.method === "POST") {
      const body = await request.json();
      const { guildId, channelId } = body;

      if (!guildId || !channelId) {
        return new Response(
          JSON.stringify({ error: "guildId and channelId are required" }),
          {
            status: 400,
            headers: { ...headers, "Content-Type": "application/json" },
          }
        );
      }

      const guild = client.guilds.cache.get(guildId);
      if (!guild) {
        return new Response(JSON.stringify({ error: "Guild not found" }), {
          status: 404,
          headers: { ...headers, "Content-Type": "application/json" },
        });
      }

      const channel = guild.channels.cache.get(channelId);
      if (!channel || !channel.isVoiceBased()) {
        return new Response(
          JSON.stringify({ error: "Voice channel not found" }),
          {
            status: 404,
            headers: { ...headers, "Content-Type": "application/json" },
          }
        );
      }

      try {
        // Import dynamically to avoid circular dependency
        const { connectToVoiceChannel } = await import("./voice.ts");
        connectToVoiceChannel(channel);

        return new Response(
          JSON.stringify({
            success: true,
            message: `Joined voice channel: ${channel.name}`,
          }),
          { headers: { ...headers, "Content-Type": "application/json" } }
        );
      } catch (error: unknown) {
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        console.error("Error joining voice channel:", error);
        return new Response(
          JSON.stringify({
            error: "Failed to join voice channel",
            details: errorMessage,
          }),
          {
            status: 500,
            headers: { ...headers, "Content-Type": "application/json" },
          }
        );
      }
    }

    // Leave voice channel endpoint
    if (path === "/leave-voice" && request.method === "POST") {
      const body = await request.json();
      const { guildId } = body;

      if (!guildId) {
        return new Response(JSON.stringify({ error: "guildId is required" }), {
          status: 400,
          headers: { ...headers, "Content-Type": "application/json" },
        });
      }

      // Import dynamically to avoid circular dependency
      const { disconnectFromVoiceChannel } = await import("./voice.ts");
      disconnectFromVoiceChannel(guildId);

      return new Response(
        JSON.stringify({ success: true, message: "Left voice channel" }),
        { headers: { ...headers, "Content-Type": "application/json" } }
      );
    }

    // Stream audio endpoint
    if (path.startsWith("/audio-stream/")) {
      const userId = path.split("/").pop();

      if (!userId) {
        return new Response(JSON.stringify({ error: "User ID is required" }), {
          status: 400,
          headers: { ...headers, "Content-Type": "application/json" },
        });
      }

      const audioStream = getUserAudioStream(userId);
      if (!audioStream) {
        return new Response(
          JSON.stringify({ error: "Audio stream not found for this user" }),
          {
            status: 404,
            headers: { ...headers, "Content-Type": "application/json" },
          }
        );
      }

      // Create a TransformStream to pipe the audio data
      const { readable, writable } = new TransformStream();

      // Pipe the audio stream to the writable side of the transform stream
      const writer = writable.getWriter();

      audioStream.on("data", (chunk: Uint8Array) => {
        writer.write(chunk);
      });

      audioStream.on("end", () => {
        writer.close();
      });

      audioStream.on("error", (err: Error) => {
        console.error("Error in audio stream:", err);
        writer.abort(err);
      });

      // Return the readable side as a streaming response
      return new Response(readable, {
        headers: {
          ...headers,
          "Content-Type": "audio/ogg",
          "Transfer-Encoding": "chunked",
        },
      });
    }

    // List active audio streams
    if (path === "/active-streams") {
      const streams = getAllAudioStreams();
      const activeUsers = Array.from(streams.keys());

      return new Response(
        JSON.stringify({
          activeStreams: activeUsers.length,
          users: activeUsers,
        }),
        { headers: { ...headers, "Content-Type": "application/json" } }
      );
    }

    // Not found
    return new Response(JSON.stringify({ error: "Endpoint not found" }), {
      status: 404,
      headers: { ...headers, "Content-Type": "application/json" },
    });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("Error handling request:", error);
    return new Response(
      JSON.stringify({
        error: "Internal server error",
        details: errorMessage,
      }),
      {
        status: 500,
        headers: { ...headers, "Content-Type": "application/json" },
      }
    );
  }
}
