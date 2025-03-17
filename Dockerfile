FROM denoland/deno:ubuntu-2.2.3

USER deno
WORKDIR /home/deno

COPY deno.json .
RUN deno install --allow-scripts=npm:@discordjs/opus@0.10.0

COPY src ./src

RUN deno cache src/main.ts

EXPOSE 5004

CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-env", "--allow-ffi", "src/main.ts"]