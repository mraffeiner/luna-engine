import { initializeBot, shutdownBot } from "./bot.ts";
import { startApiServer } from "./api.ts";

console.log("Starting Discord microservice...");

// Handle shutdown signals
function setupShutdownHandlers() {
  const shutdown = () => {
    console.log("Received shutdown signal");
    shutdownBot();
    Deno.exit(0);
  };

  // Handle SIGINT (Ctrl+C)
  Deno.addSignalListener("SIGINT", shutdown);

  // Handle SIGTERM (Docker stop)
  Deno.addSignalListener("SIGTERM", shutdown);
}

// Main function
async function main() {
  try {
    // Initialize the Discord bot
    await initializeBot();

    // Start the API server
    startApiServer();

    // Set up shutdown handlers
    setupShutdownHandlers();

    console.log("Discord microservice is running");
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("Failed to start Discord microservice:", errorMessage);
    Deno.exit(1);
  }
}

// Run the main function
main();
