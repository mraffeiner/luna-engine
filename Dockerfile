FROM denoland/deno:ubuntu-2.2.5

USER root

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER deno
WORKDIR /home/deno

COPY deno.json .
RUN deno install --allow-scripts=npm:@discordjs/opus@0.10.0

COPY src ./src

RUN deno cache src/main.ts

EXPOSE 5004

CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-run", "--allow-ffi", "--allow-env", "src/main.ts"]