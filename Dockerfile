FROM denoland/deno:ubuntu-2.2.3

USER deno
WORKDIR /home/deno

# Install dependencies
COPY deno.json .
RUN deno install --allow-scripts=npm:@discordjs/opus@0.10.0

# Copy source code
COPY src ./src

# Cache the main application
RUN deno cache src/main.ts

# Expose API port
EXPOSE 5004

# Run the application
CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-env", "--allow-ffi", "src/main.ts"]