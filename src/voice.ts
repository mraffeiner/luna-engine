import {
  joinVoiceChannel,
  createAudioPlayer,
  VoiceConnectionStatus,
  EndBehaviorType,
} from "@discordjs/voice";
import type { VoiceBasedChannel } from "discord.js";

// Map to track active voice connections by guild ID
const activeConnections = new Map();

// Map to track audio streams by user ID
const audioStreams = new Map();

/**
 * Connect to a voice channel and start listening to speakers
 * @param channel The voice channel to join
 * @returns Object containing connection and cleanup function
 */
export function connectToVoiceChannel(channel: VoiceBasedChannel) {
  const guildId = channel.guild.id;

  // Check if already connected to this guild
  if (activeConnections.has(guildId)) {
    console.log(`Already connected to a voice channel in guild ${guildId}`);
    return activeConnections.get(guildId);
  }

  console.log(
    `Connecting to voice channel: ${channel.name} in guild ${guildId}`
  );

  // Create connection to the voice channel
  const connection = joinVoiceChannel({
    channelId: channel.id,
    guildId: channel.guild.id,
    adapterCreator: channel.guild.voiceAdapterCreator,
    selfDeaf: false,
    selfMute: false,
  });

  // Create audio player
  const player = createAudioPlayer();
  connection.subscribe(player);

  // Set up connection event handlers
  connection.on(VoiceConnectionStatus.Ready, () => {
    console.log(`Voice connection ready in guild ${guildId}`);
  });

  connection.on(VoiceConnectionStatus.Disconnected, () => {
    console.log(`Voice connection disconnected from guild ${guildId}`);
    cleanup();
  });

  // Set up audio receivers for users in the channel
  connection.receiver.speaking.on("start", (userId: string) => {
    console.log(`User ${userId} started speaking`);

    // Check for and destroy existing stream
    if (audioStreams.has(userId)) {
      const oldStream = audioStreams.get(userId);
      if (oldStream) {
        console.log(`Destroying existing stream for user ${userId}`);
        oldStream.destroy();
      }
      audioStreams.delete(userId); // Ensure map entry is removed
    }

    // Create a readable stream for this user's audio
    const audioStream = connection.receiver.subscribe(userId, {
      end: {
        behavior: EndBehaviorType.AfterSilence,
        duration: 500,
      },
    });

    audioStreams.set(userId, audioStream);

    // You can now pipe this stream to other services for processing
    // For example:
    // audioStream.pipe(someProcessingStream);

    audioStream.on("end", () => {
      console.log(`User ${userId} stopped speaking`);
      audioStreams.delete(userId);
    });
  });

  // Cleanup function to disconnect and remove references
  const cleanup = () => {
    try {
      // Destroy all audio streams
      for (const [userId, stream] of audioStreams.entries()) {
        if (stream) {
          stream.destroy();
        }
        audioStreams.delete(userId);
      }

      // Disconnect from voice channel
      connection.destroy();
      activeConnections.delete(guildId);
      console.log(`Cleaned up voice connection for guild ${guildId}`);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      console.error(`Error cleaning up voice connection: ${errorMessage}`);
    }
  };

  // Store the connection and cleanup function
  const connectionData = { connection, cleanup };
  activeConnections.set(guildId, connectionData);

  return connectionData;
}

/**
 * Disconnect from a voice channel in a specific guild
 * @param guildId The ID of the guild to disconnect from
 */
export function disconnectFromVoiceChannel(guildId: string) {
  if (activeConnections.has(guildId)) {
    const { cleanup } = activeConnections.get(guildId);
    cleanup();
    console.log(`Disconnected from voice channel in guild ${guildId}`);
  } else {
    console.log(`Not connected to any voice channel in guild ${guildId}`);
  }
}

/**
 * Get an audio stream for a specific user
 * @param userId The ID of the user to get the audio stream for
 * @returns The audio stream or null if not found
 */
export function getUserAudioStream(userId: string) {
  return audioStreams.get(userId) || null;
}

/**
 * Get all active audio streams
 * @returns Map of user IDs to audio streams
 */
export function getAllAudioStreams() {
  return audioStreams;
}
