FROM denoland/deno:ubuntu-2.2.5

USER deno
WORKDIR /home/deno

COPY deno.json .
COPY src ./src
RUN deno cache src/main.ts --config deno.json

EXPOSE 5005

CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-env", "src/main.ts"]