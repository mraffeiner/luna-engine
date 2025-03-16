# Stage 1: Build the SvelteKit application with Deno
FROM denoland/deno:ubuntu-2.2.3 AS build

WORKDIR /app

# Copy dependency files
COPY deno.lock* .
COPY package.json .
COPY svelte.config.js .
COPY vite.config.ts .
COPY tsconfig.json .

# Copy source code
COPY src/ ./src/
COPY static/ ./static/

# Install dependencies and build the application
RUN deno install
RUN deno task build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy the built assets from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy our custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]