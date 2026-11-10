# app: Luna Engine dashboard

The web dashboard and engine loop for [Luna Engine](../README.md), plus the optional Tauri desktop wrapper.

- **Stack:** SvelteKit (static adapter), Svelte 5, Tailwind 4, TypeScript. It is built with Deno and served by Nginx.
- **Container:** `luna-engine`, on port 8080
- **Nginx** (`nginx.conf`) serves the built SPA and proxies `/api/<name>/` to `http://<name>-service:<port>/` inside the compose network.

## Development

The dashboard calls every backend through relative `/api/<service>/` paths, which only Nginx resolves inside the compose network. The simplest workflow is to run the full stack and rebuild this container after making changes. From the repo root:

```bash
docker compose up -d --build luna-engine
```

`deno task dev` (Vite) serves the UI with hot reload, but its `/api` proxy is out of date. It sends everything to `localhost:5000` and strips only `/api`, so `/api/llm/models` ends up at docker-service as `/llm/models`. Until `vite.config.ts` gets one proxy entry per service that mirrors `nginx.conf`, use the compose-served UI on port 8080 for anything that calls a backend.

Code checks, run from `app/`:

```bash
deno install            # or npm install
deno task check         # svelte-check / type check
deno task lint          # prettier + eslint
deno task format
```

`package.json` also has `compose:*` scripts that run `docker compose -f ../docker-compose.yml ...`.

## Layout

```
src/
├── routes/                 # single-page app shell (+layout, +page)
└── lib/
    ├── components/         # Sidebar, cards, controls, banners
    ├── pages/
    │   ├── EnginePage.svelte   # the think → speak loop
    │   ├── prompt/             # prompt templates and sections
    │   └── services/<name>/    # one page + API client per service
    └── shared/             # global state, constants, text utils
src-tauri/                  # Tauri 2 desktop wrapper
nginx.conf                  # static hosting + /api reverse proxy
Dockerfile                  # Deno build → nginx:alpine
```

## Desktop app (Tauri)

```bash
cd src-tauri && cargo build      # or: deno task tauri:build
```

It needs Rust 1.77.2+ and the [Tauri 2 Linux prerequisites](https://v2.tauri.app/start/prerequisites/#linux). `src-tauri/icons/icon.png` is a blank placeholder. Tauri uses it as the window icon and won't compile without it, so replace it rather than delete it.

Run the resulting binary **from the repo root**, because it runs `docker compose` in its current working directory. It waits up to 60 s for `http://localhost:8080` to respond, then opens the window. Closing the window exits the app, which runs `docker compose stop` first.
