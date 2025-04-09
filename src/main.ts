import { Application, Router } from "oak";
import * as log from "https://deno.land/std@0.224.0/log/mod.ts";
import { format } from "https://deno.land/std@0.224.0/datetime/format.ts";
import { loadSync } from "dotenv";
import OBSWebSocket from "obs-websocket-js";

// --- Environment Variables ---

// --- Logging Setup ---
log.setup({
  handlers: {
    console: new log.ConsoleHandler("INFO", {
      // Default to INFO level
      useColors: false,
      formatter: (record: log.LogRecord) => {
        const extra =
          record.args && record.args.length > 0
            ? " " + record.args.map(String).join(" ")
            : "";
        return `[${format(record.datetime, "yyyy-MM-dd HH:mm:ss")}] - ${
          record.levelName
        }: ${record.msg}${extra}`;
      },
    }),
  },
  loggers: {
    default: {
      level: "INFO",
      handlers: ["console"],
    },
  },
});
const logger = log.getLogger();

loadSync({ export: true, allowEmptyValues: true }); // Load .env file
const obsPassword = Deno.env.get("OBS_WEBSOCKET_PASSWORD");
const obsAddress = Deno.env.get("OBS_WEBSOCKET_ADDRESS");
const obsSubtitleSourceName = Deno.env.get("OBS_SUBTITLE_SOURCE_NAME");
const port = parseInt(Deno.env.get("PORT") || "5006"); // Default port if not set

// --- Application Setup ---
const obs = new OBSWebSocket();
const app = new Application();
const router = new Router();

// --- OBS Connection Handling ---
let isObsConnected = false;
let isConnecting = false; // Flag to prevent concurrent connection attempts
const reconnectDelay = 5000; // Reconnect delay in milliseconds (5 seconds)

/**
 * Attempts to connect to the OBS WebSocket server using credentials from environment variables.
 * Updates the `isObsConnected` flag based on the connection status.
 */
async function connectToObs() {
  if (isConnecting) {
    logger.info("Connection attempt already in progress.");
    return;
  }
  isConnecting = true;
  isObsConnected = false; // Assume disconnected until successful
  try {
    logger.info(`Attempting to connect to OBS at ${obsAddress}...`);
    const { obsWebSocketVersion, negotiatedRpcVersion } = await obs.connect(
      obsAddress,
      obsPassword
    );
    logger.info(
      `Connected to OBS: ws version ${obsWebSocketVersion}, RPC version ${negotiatedRpcVersion}`
    );
    isObsConnected = true;
  } catch (error: unknown) {
    if (error instanceof Error) {
      logger.error("Failed to connect to OBS:", error.message);
    } else {
      logger.error("Failed to connect to OBS with unknown error:", error);
    }
    isObsConnected = false;
    // Schedule reconnect on failure
    setTimeout(connectToObs, reconnectDelay);
  } finally {
    isConnecting = false; // Allow next attempt
  }
}

obs.on("ConnectionClosed", () => {
  logger.warn(
    `OBS connection closed. Attempting reconnect in ${
      reconnectDelay / 1000
    }s...`
  );
  isObsConnected = false;
  if (!isConnecting) {
    // Avoid scheduling multiple reconnects rapidly
    setTimeout(connectToObs, reconnectDelay);
  }
});

obs.on("ConnectionError", (err: Error) => {
  logger.error(
    "OBS connection error:",
    err.message,
    `Attempting reconnect in ${reconnectDelay / 1000}s...`
  );
  isObsConnected = false;
  if (!isConnecting) {
    // Avoid scheduling multiple reconnects rapidly
    setTimeout(connectToObs, reconnectDelay);
  }
});

// Initial connection attempt
await connectToObs();

// --- API Endpoints ---

/**
 * GET / - Health check endpoint.
 * Returns the service status and OBS connection state.
 */
router.get("/", (ctx) => {
  ctx.response.body = { status: "running", obsConnected: isObsConnected };
});

/**
 * GET /scenes - Retrieves the list of scenes from OBS.
 * Requires an active OBS connection.
 */
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
    logger.error("Error getting scenes:", error);
    ctx.response.status = 500;
    ctx.response.body = { error: "Failed to get scenes from OBS" };
  }
});

/**
 * POST /subtitle - Updates the text of a specified OBS text source.
 * Expects a JSON body with a "text" property.
 * Requires an active OBS connection and the OBS_SUBTITLE_SOURCE_NAME env var.
 */
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
    const body = ctx.request.body();
    if (body.type !== "json") {
      ctx.response.status = 400; // Bad Request
      ctx.response.body = { error: "Request body must be JSON" };
      return;
    }
    const { text } = await body.value;

    if (typeof text !== "string") {
      ctx.response.status = 400; // Bad Request
      ctx.response.body = {
        error: "JSON body must contain a 'text' property of type string",
      };
      return;
    }

    logger.debug(
      `Setting subtitle source "${obsSubtitleSourceName}" text to: "${text}"`
    );

    // Update the text source settings in OBS
    await obs.call("SetInputSettings", {
      inputName: obsSubtitleSourceName,
      inputSettings: {
        text: text, // Assumes the target source uses a 'text' property for its content
      },
    });

    ctx.response.status = 200;
    ctx.response.body = { success: true, textSet: text };
  } catch (error: unknown) {
    logger.error("Error setting subtitle text:", error);
    let errorMessage = "Failed to set subtitle text in OBS";
    if (error instanceof Error) {
      errorMessage = error.message; // Use specific error message if available
    }
    ctx.response.status = 500;
    ctx.response.body = { error: errorMessage };
  }
});

// --- App Setup ---
app.use(router.routes());
app.use(router.allowedMethods());

app.addEventListener("listen", ({ hostname, port, secure }) => {
  logger.info(
    `OBS Service listening on: ${secure ? "https://" : "http://"}${
      hostname ?? "localhost"
    }:${port}`
  );
});

await app.listen({ port });
