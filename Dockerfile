FROM denoland/deno:1.41.3

WORKDIR /app

# Copy source code
COPY deno.json .
COPY src ./src

# Cache the main application
RUN deno cache src/mod.ts

# Expose API port
EXPOSE 5004

# Run the application
CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-env", "src/mod.ts"]