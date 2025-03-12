FROM denoland/deno:1.41.3

WORKDIR /app

# Cache dependencies as a separate layer
COPY src/deps.ts .
RUN deno cache deps.ts

# Copy source code
COPY src ./src

# Cache the main application
RUN deno cache src/mod.ts

# Expose API port
EXPOSE 5004

# Run the application
CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-env", "src/mod.ts"]