import { Application, Router } from "oak";
import { loadSync } from "dotenv";
import OBSWebSocket from "obs-websocket-js";

// Load environment variables from .env file
loadSync({ export: true, allowEmptyValues: true });
const obsPassword = Deno.env.get("OBS_WEBSOCKET_PASSWORD");
const obsAddress = Deno.env.get("OBS_WEBSOCKET_ADDRESS");
const obsSubtitleSourceName = Deno.env.get("OBS_SUBTITLE_SOURCE_NAME");
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
    isObsConnected = false;
  }
}

obs.on("ConnectionClosed", () => {
  console.warn("OBS connection closed.");
  isObsConnected = false;
});

obs.on("ConnectionError", (err: Error) => {
  // Cast to any to bypass type error
  // Explicitly type err
  console.error("OBS connection error:", err.message);
  isObsConnected = false;
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

// Endpoint to update subtitle text source
router.post("/subtitle", async (ctx) => {
  if (!isObsConnected) {
    ctx.response.status = 503; // Service Unavailable
    ctx.response.body = { error: "OBS not connected" };
    return;
  }
  if (!obsSubtitleSourceName) {
    ctx.response.status = 500;
    ctx.response.body = {
      error: "OBS_SUBTITLE_SOURCE_NAME environment variable not set",
    };
    return;
  }

  try {
    const body = ctx.request.body(); // Content type based body resolution
    if (body.type !== "json") {
      ctx.response.status = 400; // Bad Request
      ctx.response.body = { error: "Request body must be JSON" };
      return;
    }
    const { text } = await body.value; // Read JSON body content

    if (typeof text !== "string") {
      ctx.response.status = 400; // Bad Request
      ctx.response.body = {
        error: "JSON body must contain a 'text' property of type string",
      };
      return;
    }

    console.log(
      `Setting subtitle source "${obsSubtitleSourceName}" text to: "${text}"`
    );

    // Use SetInputSettings to change the text of the source
    await obs.call("SetInputSettings", {
      inputName: obsSubtitleSourceName,
      inputSettings: {
        text: text, // Assuming the source uses a 'text' property
      },
      // overlay: true // Might be needed depending on source type/OBS version? Test this.
    });

    ctx.response.status = 200;
    ctx.response.body = { success: true, textSet: text };
  } catch (error: unknown) {
    console.error("Error setting subtitle text:", error);
    // Check for specific OBS errors if possible (e.g., source not found)
    let errorMessage = "Failed to set subtitle text in OBS";
    if (error instanceof Error) {
      errorMessage = error.message; // More specific error from obs-websocket-js
    }
    ctx.response.status = 500;
    ctx.response.body = { error: errorMessage };
  }
});

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
