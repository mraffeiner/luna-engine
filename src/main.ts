import { Application, Router } from "oak";
import { loadSync } from "dotenv";
import OBSWebSocket from "obs-websocket-js";

// Load environment variables from .env file
loadSync({ export: true, allowEmptyValues: true }); // Loads into Deno.env, removed 'safe' option
const obsPassword = Deno.env.get("OBS_WEBSOCKET_PASSWORD");
const obsAddress = Deno.env.get("OBS_WEBSOCKET_ADDRESS") || "localhost:4455";
const port = parseInt(Deno.env.get("PORT") || "5006");

const obs = new OBSWebSocket();
const app = new Application();
const router = new Router();

// --- OBS Connection Handling ---
let isObsConnected = false;

async function connectToObs() {
  try {
    console.log(`Attempting to connect to OBS at ${obsAddress}...`);
    const { obsWebSocketVersion, negotiatedRpcVersion } = await obs.connect(
      obsAddress,
      obsPassword
    );
    console.log(
      `Connected to OBS: ws version ${obsWebSocketVersion}, RPC version ${negotiatedRpcVersion}`
    );
    isObsConnected = true;
  } catch (error: unknown) {
    // Explicitly type error as unknown
    if (error instanceof Error) {
      console.error("Failed to connect to OBS:", error.message);
    } else {
      console.error("Failed to connect to OBS with unknown error:", error);
    }
    // Optional: Implement retry logic here
    isObsConnected = false;
    // Example: Retry after 5 seconds
    // setTimeout(connectToObs, 5000);
  }
}

obs.on("ConnectionClosed", () => {
  // Cast to any to bypass type error
  console.warn("OBS connection closed. Attempting to reconnect...");
  isObsConnected = false;
  // Optional: Implement retry logic here
  setTimeout(connectToObs, 5000); // Retry after 5 seconds
});

obs.on("ConnectionError", (err: Error) => {
  // Cast to any to bypass type error
  // Explicitly type err
  console.error("OBS connection error:", err.message); // Access message property
  isObsConnected = false;
  // Optional: Implement retry logic here
});

// Initial connection attempt
await connectToObs();

// --- API Endpoints ---

// Health check
router.get("/", (ctx) => {
  ctx.response.body = { status: "running", obsConnected: isObsConnected };
});

// Placeholder OBS control endpoints
router.get("/scenes", async (ctx) => {
  if (!isObsConnected) {
    ctx.response.status = 503; // Service Unavailable
    ctx.response.body = { error: "OBS not connected" };
    return;
  }
  try {
    const { scenes } = await obs.call("GetSceneList");
    ctx.response.body = scenes;
  } catch (error) {
    console.error("Error getting scenes:", error);
    ctx.response.status = 500;
    ctx.response.body = { error: "Failed to get scenes from OBS" };
  }
});

// Add more endpoints as needed (e.g., set scene, get sources, toggle mute, start/stop stream/record)

// --- App Setup ---
app.use(router.routes());
app.use(router.allowedMethods());

app.addEventListener("listen", ({ hostname, port, secure }) => {
  console.log(
    `OBS Service listening on: ${secure ? "https://" : "http://"}${
      hostname ?? "localhost"
    }:${port}`
  );
});

await app.listen({ port });
