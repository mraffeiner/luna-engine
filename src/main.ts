import * as log from "https://deno.land/std@0.224.0/log/mod.ts";
import { format } from "https://deno.land/std@0.224.0/datetime/format.ts";
import { Application, Router, Context, Next } from "oak";
import { io, Socket } from "socket.io-client";

// --- Logging Setup ---
log.setup({
  handlers: {
    console: new log.ConsoleHandler("DEBUG", {
      // Set to DEBUG for more verbose output during testing
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
    alerts: {
      level: "INFO",
      handlers: ["console"],
    },
  },
});

const logger = log.getLogger();
const alertsLogger = log.getLogger("alerts");

// --- Environment Variables ---
const PORT = parseInt(Deno.env.get("PORT") || "5005");
const STREAM_ELEMENTS_JWT = Deno.env.get("STREAMELEMENTS_JWT_TOKEN");

if (!STREAM_ELEMENTS_JWT) {
  logger.critical("STREAMELEMENTS_JWT_TOKEN environment variable is not set!");
  Deno.exit(1);
}

// --- WebSocket Server Setup ---
const connectedClients = new Set<WebSocket>();

function broadcastAlert(alertData: unknown) {
  const message = JSON.stringify(alertData);
  alertsLogger.debug(
    `Broadcasting alert to ${connectedClients.size} clients:`,
    alertData
  );
  for (const client of connectedClients) {
    if (client.readyState === WebSocket.OPEN) {
      try {
        client.send(message);
      } catch (error) {
        logger.error("Failed to send message to client:", error);
        // Optionally remove client if send fails repeatedly
      }
    } else if (
      client.readyState === WebSocket.CLOSING ||
      client.readyState === WebSocket.CLOSED
    ) {
      // Clean up closed connections
      connectedClients.delete(client);
      logger.info(
        `Removed closed WebSocket client. Total clients: ${connectedClients.size}`
      );
    }
  }
}

// --- Event Processing Logic ---

interface StandardizedAlert {
  id: string;
  type:
    | "follow"
    | "sub"
    | "resub"
    | "giftsub"
    | "communitygiftsub"
    | "tip"
    | "cheer"
    | "raid"
    | "host"
    | "test"
    | "communityGiftPurchase" // Added
    | "redemption" // Added
    | "merch" // Added
    | "charityCampaignDonation" // Added
    | "unknown";
  platform: "twitch" | "youtube" | "facebook" | "trovo" | "unknown";
  timestamp: string;
  user?: string;
  recipient?: string;
  amount?: number;
  currency?: string;
  message?: string;
  tier?: string;
  isGift?: boolean;
  isCommunity?: boolean;
  gifter?: string;
  originalEventName: string;
}

// Helper to safely get properties from unknown data object
function safeGet(
  data: unknown,
  prop: string,
  defaultValue: unknown = undefined
): unknown {
  // Refined type check to ensure data is indexable
  return typeof data === "object" &&
    data !== null &&
    Object.prototype.hasOwnProperty.call(data, prop)
    ? (data as Record<string, unknown>)[prop] // Assert data is indexable
    : defaultValue;
}

function processStreamElementsEvent(
  eventType: string,
  rawData: unknown, // Change to unknown
  // Add optional platform parameter to preserve it during recursion
  initialPlatform?: StandardizedAlert["platform"]
): StandardizedAlert | null {
  const timestamp = new Date().toISOString();
  // Assert types for values we expect to be strings or numbers if present
  const id = safeGet(rawData, "_id", `${eventType}-${Date.now()}`) as string;
  // Use initialPlatform if provided, otherwise determine from rawData
  const platform =
    initialPlatform ??
    (safeGet(rawData, "provider", "unknown") as StandardizedAlert["platform"]); // Assert specific platform type
  let standardizedType: StandardizedAlert["type"] = "unknown";
  // Try 'displayName', then 'name', then 'username'
  let user = (safeGet(rawData, "displayName") ??
    safeGet(rawData, "name") ??
    safeGet(rawData, "username")) as string | undefined;
  let amount = safeGet(rawData, "amount") as number | undefined;
  let message = safeGet(rawData, "message") as string | undefined;
  let recipient: string | undefined = undefined;
  let currency: string | undefined = undefined;
  let tier: string | undefined = undefined;
  let isGift: boolean | undefined = undefined;
  let isCommunity: boolean | undefined = undefined;
  let gifter: string | undefined = undefined;

  // Normalize eventType (remove '-latest', handle 'test')
  const baseEventType = eventType.replace("-latest", "");

  switch (baseEventType) {
    case "follow": // Corrected from "follower"
      standardizedType = "follow";
      break;
    case "subscriber":
      // Need to differentiate sub types
      isGift = safeGet(rawData, "gifted", false) as boolean | undefined;
      gifter = safeGet(rawData, "sender") as string | undefined; // Often 'sender' for gifts
      amount = safeGet(rawData, "amount", 1) as number | undefined; // Months or count
      tier = safeGet(rawData, "tier") as string | undefined;
      // Check amount is defined before using in calculation
      isCommunity = amount !== undefined && amount > 1 && isGift; // Basic heuristic for community gift

      if (isCommunity) {
        standardizedType = "communitygiftsub";
        user = undefined; // User field might be irrelevant for community gifts
      } else if (isGift) {
        standardizedType = "giftsub";
        recipient = user; // The 'name' is the recipient
        user = gifter; // The 'sender' is the user doing the action
      } else {
        // Check for resub (amount > 1 is often used)
        // Check amount is defined before using in comparison
        standardizedType = amount !== undefined && amount > 1 ? "resub" : "sub";
      }
      break;
    case "host":
      standardizedType = "host";
      // 'name' is hoster, 'amount' is viewers
      break;
    case "raid":
      standardizedType = "raid";
      // 'name' is raider, 'amount' is viewers
      break;
    case "cheer":
      standardizedType = "cheer";
      // 'name' is cheerer, 'amount' is bits
      break;
    case "tip":
      standardizedType = "tip";
      currency = safeGet(rawData, "currency", "USD") as string | undefined;
      // 'name' is tipper, 'amount' is currency value
      break;
    case "test": // Handle the generic test event
    case "event": {
      // Handle the generic event wrapper if used
      // Try to infer type from nested data if possible
      const nestedType = safeGet(rawData, "type") as string | undefined; // Sometimes 'type' is nested
      const nestedData = safeGet(rawData, "data", rawData); // Keep as unknown for recursive call
      if (nestedType && nestedType !== baseEventType) {
        // Recursively process nested event, passing the original platform
        return processStreamElementsEvent(nestedType, nestedData, platform);
      } else {
        // If it's just a test wrapper, mark as test
        standardizedType = "test";
        // Assert types for nested data access
        // Try 'displayName', then 'name' then 'username' from nested data
        user = (safeGet(nestedData, "displayName") ??
          safeGet(nestedData, "name") ??
          safeGet(nestedData, "username")) as string | undefined;
        amount = safeGet(nestedData, "amount", amount) as number | undefined;
        message = safeGet(nestedData, "message", message) as string | undefined;
      }
      break;
    }
    // --- New cases will be inserted here ---
    case "communityGiftPurchase":
      standardizedType = "communitygiftsub"; // Map to existing community gift type
      // User might be buyer, amount might be count
      break;
    case "redemption":
      standardizedType = "redemption";
      // User is redeemer, message might contain reward name/details
      break;
    case "merch":
      standardizedType = "merch";
      // User is buyer, message/data might contain item details
      break;
    case "charityCampaignDonation":
      standardizedType = "charityCampaignDonation";
      // User is donor, amount is donation amount, currency might be present
      currency = safeGet(rawData, "currency", "USD") as string | undefined;
      break;

    default:
      alertsLogger.warn(`Unhandled event type: ${eventType}`);
      // Still create a basic standardized object
      standardizedType = "unknown";
      break;
  }

  return {
    id,
    type: standardizedType,
    platform,
    timestamp,
    user,
    recipient,
    amount,
    currency,
    message,
    tier,
    isGift,
    isCommunity,
    gifter,
    originalEventName: eventType,
  };
}

function connectToStreamElements() {
  logger.info("Attempting to connect to StreamElements...");
  // Ensure type safety for the socket object
  const socket: Socket = io("https://realtime.streamelements.com", {
    transports: ["websocket"],
    forceNew: true,
  });

  socket.on("connect", () => {
    logger.info(
      "Socket connected to StreamElements. Attempting authentication..."
    );
    // Authenticate using emit *after* connection is established
    socket.emit("authenticate", { method: "jwt", token: STREAM_ELEMENTS_JWT });
  });

  socket.on("authenticated", (data: unknown) => {
    logger.info("Successfully authenticated with StreamElements:", data);
  });

  socket.on("unauthorized", (error: unknown) => {
    // Critical error
    logger.error(
      "StreamElements authentication failed! Check JWT Token.",
      error
    );
  });

  socket.on("disconnect", (reason: string) => {
    logger.warn(`Disconnected from StreamElements: ${reason}.`);
  });

  socket.on("connect_error", (error: Error) => {
    logger.error("StreamElements connection error:", error.message, error);
  });

  // --- Event Listeners ---

  // Catch-all listener for observing all incoming events during development/debugging
  socket.onAny((eventName: string, ...args: unknown[]) => {
    alertsLogger.debug(
      `>>> Received ANY event [${eventName}]:`,
      JSON.stringify(args, null, 2) // Log the arguments/payload
    );
  });

  // Listen for specific documented event types
  const eventTypes = [
    "follower",
    "subscriber",
    "host",
    "raid",
    "cheer",
    "tip",
    "test",
    "event",
  ];

  eventTypes.forEach((eventType) => {
    socket.on(eventType, (rawData: unknown) => {
      // Process the raw data into a standardized format
      const processedAlert = processStreamElementsEvent(eventType, rawData);

      if (processedAlert) {
        alertsLogger.info(
          `Processed event [${eventType}] to type [${processedAlert.type}]:`,
          processedAlert
        );
        // Broadcast the standardized alert to connected clients
        broadcastAlert(processedAlert);
      } else {
        alertsLogger.debug(
          `Event [${eventType}] skipped or failed processing.`
        );
      }
    });
  });
}

// --- Oak Application (HTTP Server & WS Endpoint) ---
const app = new Application();
const router = new Router();

router.get("/health", (ctx: Context) => {
  logger.info("Health check requested.");
  ctx.response.body = { status: "OK", timestamp: new Date() };
  ctx.response.status = 200;
});

// WebSocket Route
router.get("/ws", (ctx: Context) => {
  if (!ctx.isUpgradable) {
    ctx.throw(501);
  }
  const ws = ctx.upgrade();
  logger.info("WebSocket client connected.");
  connectedClients.add(ws);
  ws.onopen = () =>
    logger.info(`Client added. Total clients: ${connectedClients.size}`);

  ws.onmessage = (event: MessageEvent) => {
    logger.debug("Received message from client:", event.data);
    if (event.data === "ping") {
      ws.send("pong");
    }
  };

  ws.onerror = (e: Event | ErrorEvent) => {
    logger.error("WebSocket error:", e);
    // Ensure cleanup happens correctly
    if (connectedClients.has(ws)) {
      connectedClients.delete(ws);
      logger.info(
        `Client removed due to error. Total clients: ${connectedClients.size}`
      );
    }
  };

  ws.onclose = () => {
    if (connectedClients.has(ws)) {
      connectedClients.delete(ws);
      logger.info(
        `WebSocket client disconnected. Total clients: ${connectedClients.size}`
      );
    } else {
      logger.warn("Attempted to remove already removed client on close.");
    }
  };
});

// Log requests middleware
app.use(async (ctx: Context, next: Next) => {
  await next();
  const rt = ctx.response.headers.get("X-Response-Time");
  logger.info(
    `${ctx.request.method} ${ctx.request.url} - ${ctx.response.status} - ${rt}`
  );
});

// Timing middleware
app.use(async (ctx: Context, next: Next) => {
  const start = Date.now();
  await next();
  const ms = Date.now() - start;
  ctx.response.headers.set("X-Response-Time", `${ms}ms`);
});

app.use(router.routes());
app.use(router.allowedMethods());

// --- Start Services ---
logger.info(`Starting Alerts Service on port ${PORT}...`);

// Start StreamElements connection
connectToStreamElements();

// Start Oak HTTP server
// Add error handling for server start
try {
  await app.listen({ port: PORT });
} catch (error) {
  logger.critical("Failed to start Oak server:", error);
  Deno.exit(1);
}
