FROM denoland/deno:ubuntu-2.2.5

USER root

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER deno
WORKDIR /home/deno

COPY deno.json .
RUN deno install

# @discordjs/opus picks its prebuilt binary by glibc version, but Deno always
# reports glibc 2.38 to npm packages (this image has 2.35), and no 2.38 build
# exists. Install the real 2.35 binary under the path the loader looks for.
ARG OPUS_PREBUILD=opus-v0.10.0-node-v108-napi-v3-linux-x64-glibc-2.35.tar.gz
ADD --chown=deno:deno https://github.com/discordjs/opus/releases/download/v0.10.0/${OPUS_PREBUILD} /tmp/opus.tar.gz
RUN dir=node_modules/.deno/@discordjs+opus@0.10.0/node_modules/@discordjs/opus/prebuild && \
    mkdir -p "$dir" && \
    tar -xzf /tmp/opus.tar.gz -C "$dir" && \
    mv "$dir/node-v108-napi-v3-linux-x64-glibc-2.35" "$dir/node-v108-napi-v3-linux-x64-glibc-2.38" && \
    rm /tmp/opus.tar.gz

COPY src ./src

RUN deno cache src/main.ts

EXPOSE 5004

CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-run", "--allow-ffi", "--allow-env", "--allow-sys=cpus,networkInterfaces,hostname", "src/main.ts"]