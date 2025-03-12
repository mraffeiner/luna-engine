import { Client, GatewayIntentBits, Events } from "./deps.ts";
import { DISCORD_TOKEN } from "./config.ts";
import { connectToVoiceChannel, disconnectFromVoiceChannel } from "./voice.ts";

// Create Discord client with necessary intents
export const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.MessageContent,
  ],
});

// Initialize bot
export async function initializeBot() {
  if (!DISCORD_TOKEN) {
    throw new Error("DISCORD_TOKEN is required but not set");
  }

  // Set up event handlers
  setupEventHandlers();

  // Login to Discord
  try {
    await client.login(DISCORD_TOKEN);
    console.log("Discord bot logged in successfully");
  } catch (error: unknown) {
    console.error("Failed to login to Discord:", error);
    throw error;
  }

  return client;
}

// Set up event handlers for the Discord client
function setupEventHandlers() {
  // Ready event
  client.on(Events.ClientReady, () => {
    console.log(`Logged in as ${client.user?.tag}`);
  });

  // Message event
  client.on(Events.MessageCreate, async (message) => {
    // Ignore messages from bots
    if (message.author.bot) return;

    // Simple command handling
    if (message.content.startsWith("!join")) {
      // Join voice channel command
      const voiceChannel = message.member?.voice.channel;
      if (!voiceChannel) {
        await message.reply("You need to be in a voice channel first!");
        return;
      }

      try {
        connectToVoiceChannel(voiceChannel);
        await message.reply(`Joined voice channel: ${voiceChannel.name}`);
      } catch (error: unknown) {
        console.error("Error joining voice channel:", error);
        await message.reply("Failed to join voice channel");
      }
    } else if (message.content.startsWith("!leave")) {
      // Leave voice channel command
      if (!message.guild) return;

      disconnectFromVoiceChannel(message.guild.id);
      await message.reply("Left voice channel");
    }
  });

  // Error event
  client.on("error", (error) => {
    console.error("Discord client error:", error);
  });
}

// Shutdown the bot gracefully
export function shutdownBot() {
  console.log("Shutting down Discord bot...");

  // Disconnect from all voice channels
  for (const guild of client.guilds.cache.values()) {
    disconnectFromVoiceChannel(guild.id);
  }

  // Destroy the client
  client.destroy();
  console.log("Discord bot shut down successfully");
}
