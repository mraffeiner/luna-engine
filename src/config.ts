import { config } from "./deps.ts";

// Load environment variables
try {
  await config({ export: true, envPath: "../.env" });
} catch (e: unknown) {
  const errorMessage = e instanceof Error ? e.message : String(e);
  console.warn("Failed to load .env file:", errorMessage);
}

// Discord configuration
export const DISCORD_TOKEN = Deno.env.get("DISCORD_TOKEN") || "";

// API configuration
export const API_PORT = parseInt(Deno.env.get("DISCORD_API_PORT") || "5004");
export const API_HOST = Deno.env.get("DISCORD_API_HOST") || "0.0.0.0";

// Validate required configuration
if (!DISCORD_TOKEN) {
  console.error("DISCORD_TOKEN is required but not set");
}
