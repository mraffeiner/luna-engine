# CLAUDE.md: luna-engine

Dashboard and orchestrator for **Luna**, an AI VTuber. This is the hub of a multi-repo system. The nine backend services are separate git repos checked out next to this one (`../llm-service`, `../tts-service`, ...). See `README.md` for the full architecture diagram, the service and port table, and user setup.

**Platform: Linux-first.** The stack runs with Docker Engine on Linux, and host apps like VTube Studio (under Proton), OBS and LM Studio are reached through `host.docker.internal` (mapped with `extra_hosts: host-gateway`). Don't add Windows- or macOS-specific code or config.

## What lives here

- **SvelteKit SPA** (`src/`): Svelte 5 (runes), Tailwind 4 and TypeScript, built with `adapter-static` (with an `index.html` fallback).
- **`nginx.conf`**: serves the built SPA and reverse-proxies `/api/<name>/` → `http://<name>-service:<port>/` inside the compose network.
- **`docker-compose.yml`**: builds and runs the whole stack. Each service is built from `../<repo>` and reads `../<repo>/.env`.
- **`src-tauri/`**: optional Tauri **1.x** desktop wrapper (Rust). It runs `docker compose up` in its current working directory, waits for `localhost:8080`, shows the window, and runs `docker compose stop` when the window closes.

## Commands

Deno is the package manager (`deno.lock`; the Dockerfile runs `deno install` and `deno task build`). npm also works for the `package.json` scripts.

```bash
deno install
deno task check         # svelte-kit sync + svelte-check (type check)
deno task lint          # prettier --check + eslint
deno task format        # prettier --write
deno task build         # static build → build/

npm run compose:up      # docker compose up -d --build (whole stack, UI on :8080)
docker compose up -d --build luna-engine   # rebuild only the UI container
docker compose logs -f <service>
cd src-tauri && cargo build                # desktop wrapper (needs webkit2gtk-4.0 / libsoup2)
```

There is **no test suite**. Verify UI changes with `deno task check` and `deno task lint`, then in the running stack at http://localhost:8080.

The `vite dev` proxy in `vite.config.ts` is stale: it sends all of `/api` to `:5000`. Don't rely on `deno task dev` for anything that calls a backend. Use the compose-served UI.

## Code map

```
src/routes/+page.svelte            single page; renders the current page from PAGES
src/lib/shared/constants.ts        PAGES (sidebar entries; serviceId = container name), TTS_ENGINES, platforms
src/lib/shared/shared.svelte.ts    global $state: engineConfig, engineStates, receiveInput, serviceOutput, subtitles
src/lib/shared/utils.ts            text normalization for LLM output / TTS input, splitByPunctuation
src/lib/pages/EnginePage.svelte    THE ENGINE LOOP: think (LLM, optional prepass) → speak (TTS, Discord, subtitles)
src/lib/pages/prompt/              prompt sections + templates (persisted in localStorage)
src/lib/pages/services/<name>/     <Name>Page.svelte (UI) + <name>Service.ts (API client, stores)
src/lib/pages/services/ServicePage.svelte   shared Configuration/Logs tab wrapper
src/lib/pages/services/docker/dockerService.ts   container status/start/stop, SSE logs, shared `serviceError` store
src/lib/components/                Sidebar, cards, EngineControls, ErrorBanner, Icon, Spinner
src/app.css                        design tokens (@theme, "Autumn Night") + component classes
```

## Conventions

- Svelte 5 runes (`$state`, `$derived`, `$props`) for component and global state. Older `svelte/store` `writable`s are still used in the service clients (`loading`, `serviceError`, model lists). Follow the existing pattern in the file you're editing rather than converting.
- Service clients call **relative** `/api/<name>/...` URLs only. Never hard-code hosts or ports in the frontend.
- Report service errors through the shared `serviceError` store (from `dockerService.ts`), which `ErrorBanner` displays.
- Styling: use the theme tokens and utility classes defined in `src/app.css` (e.g. `bg-bg-surface`, `text-text-disabled`, `tab-button`) instead of raw Tailwind colors.
- Prettier: tabs, single quotes, no trailing commas, width 100, Tailwind class sorting. Run `deno task format` before committing.

## Cross-repo contracts

Each backend's HTTP/WS API is consumed by exactly one client file: `src/lib/pages/services/<name>/<name>Service.ts`. When an API changes in a sibling repo, update that client in the same piece of work, and read the sibling's `CLAUDE.md` and `README.md` first.

To add a new service, touch all of the following:

1. a new sibling repo
2. a service entry in `docker-compose.yml` (and in `depends_on` of `luna-engine`)
3. a `location /api/<name>/` block in `nginx.conf`
4. a `PAGES` entry in `constants.ts` whose `serviceId` matches the container name
5. a `services/<name>/` page and client

Every backend exposes `GET /health` → `{ "status": "OK", "timestamp": ... }`.

## Gotchas

- `kokoro-tts` and `sesame-tts` are third-party images with no build context. `sesame-tts` only runs with `--profile experimental`. Both load `../stt-service/.env`, which is a known oddity, so leave it unless asked.
- compose fails if any referenced `.env` file or `../chat-service/youtube_secret.json` is missing.
- docker-service only streams logs for containers on the `luna-engine_default` network. That network name comes from this directory's name, so don't rename the folder.
- Every service repo has a `.env.example`. When you add or rename an env var in a service, update its `.env.example` and README in the same change.
- `src-tauri/icons/icon.png` is a blank placeholder. Tauri 1.x codegen panics on Linux if it's missing, so replace it, never delete it.
- TTS files saved with "Save TTS" land in `./output/tts` (git-ignored).

## Working rules

- Default branch is `development`. Work on feature branches and don't push without being asked.
- Never read or print `.env` files or `youtube_secret.json`. They hold API keys and tokens (enforced in `.claude/settings.json`).
- Prefer small, verifiable changes. There are no tests to catch regressions.
