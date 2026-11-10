# CLAUDE.md: app (dashboard)

The Luna Engine dashboard and engine loop, plus the Tauri desktop wrapper. It runs as the `luna-engine` container on port 8080. The root `CLAUDE.md` covers the whole system and the cross-service contracts.

## What lives here

- **SvelteKit SPA** (`src/`): Svelte 5 (runes), Tailwind 4 and TypeScript, built with `adapter-static` (with an `index.html` fallback).
- **`nginx.conf`**: serves the built SPA and reverse-proxies `/api/<name>/` → `http://<name>-service:<port>/` inside the compose network.
- **`Dockerfile`**: builds with Deno (`deno install`, `deno task build`), then serves the result with `nginx:alpine`.
- **`src-tauri/`**: optional Tauri **2** desktop wrapper (Rust, `src/main.rs`). It runs `docker compose up` in its current working directory (the repo root), waits for `localhost:8080` on a background thread, then creates the window with `WebviewWindowBuilder` (`tauri.conf.json` defines no windows on purpose, so the webview never loads the URL before the stack is up). On `RunEvent::Exit` it runs `docker compose stop` and kills the `compose up` process. It uses no IPC, so there are no capabilities or plugins.

## Commands (from `app/`)

Deno is the package manager (`deno.lock`). npm also works for the `package.json` scripts.

```bash
deno install
deno task check         # svelte-kit sync + svelte-check (type check)
deno task lint          # prettier --check + eslint
deno task format        # prettier --write
deno task build         # static build → build/

docker compose -f ../docker-compose.yml up -d --build luna-engine   # rebuild the UI container
cd src-tauri && cargo build                # desktop wrapper (needs Rust 1.77.2+, webkit2gtk-4.1)
```

Verify UI changes with `deno task check` and `deno task lint`, then in the running stack at http://localhost:8080.

The `vite dev` proxy in `vite.config.ts` is stale: it sends all of `/api` to `:5000`. Don't rely on `deno task dev` for anything that calls a backend. Use the compose-served UI.

## Code map

```
src/routes/+page.svelte            single page; renders the current page from PAGES
src/lib/shared/constants.ts        PAGES (sidebar entries; serviceId = container name), TTS_ENGINES, platforms
src/lib/shared/shared.svelte.ts    global $state: engineConfig, engineStates, receiveInput, serviceOutput, subtitles
src/lib/shared/utils.ts            text normalization for LLM output / TTS input, splitByPunctuation
src/lib/pages/EnginePage.svelte    THE ENGINE LOOP: think (LLM, optional prepass) → speak (TTS, Discord, subtitles)
src/lib/pages/prompt/              prompt sections + templates (persisted in localStorage)
src/lib/pages/services/<name>/     <Name>Page.svelte (UI) + <name>Service.ts (API client for services/<name>)
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

## Gotchas

- `src-tauri/icons/icon.png` is a blank placeholder. `generate_context!` fails without it, so replace it, never delete it.
- `static/` only contains a `.gitkeep`. Keep the folder, because the Dockerfile copies it.
