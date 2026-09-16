# Coolify deployment

This Compose file is for a **Docker Compose Application** in Coolify, with
**Raw Compose Deployment disabled**. Coolify will create its private network
and generate the Traefik routing labels.

1. Point the `A`/`AAAA` records for `henrycoder.com` and `api.henrycoder.com`
   to the Coolify server. Add matching records for `www.henrycoder.com` if used.
2. Stop the old host Nginx/Certbot site so Coolify can bind ports 80 and 443.
3. Deploy this repository as a Docker Compose Application using
   `docker-compose.yml`.
4. In the generated service domain fields, set:
   - `frontend`: `https://henrycoder.com:3000`
   - `backend`: `https://api.henrycoder.com:8000`
   The backend domain has no path prefix. Python keeps its `/api` routes.
   Compose explicitly exposes frontend port `3000` and backend port `8000`;
   these match their Dockerfiles, listeners, and health checks. The ports in
   the domain fields select internal container ports; public HTTPS uses `443`.
5. Leave Coolify's default Traefik proxy configuration and generated labels in
   place. Do not enable Raw Compose Deployment and do not publish host ports.
6. In **Configuration > Environment Variables**, enter the values marked as
   required by Coolify: `API_KEY`, `LLM_MODEL`, and `SMART_LLM_MODEL`. The
   Compose defaults create editable values for `API_URL`, `AGENT_MODEL`,
   `NODE_URL`, `LOG_LEVEL`, `NUXT_PUBLIC_API_BASE`, and
   `NUXT_PUBLIC_ALEPHIUM_NODE_URL`.

Set the frontend build variable `NUXT_PUBLIC_API_BASE` to
`https://api.henrycoder.com/api`, replacing any existing `/api` override.
The backend's comma-separated `CORS_ORIGINS` defaults to
`https://henrycoder.com,https://www.henrycoder.com` and allows the browser's
JSON POST preflight requests. Rebuild and redeploy both services after these
changes. Check `https://api.henrycoder.com/api/health` for HTTP 200.

The backend returns
newline-delimited streaming responses, and Traefik forwards recognized streams
without response buffering. `X-Accel-Buffering` is harmless but is only
interpreted by Nginx; no Traefik proxy change is required.

`langgraph-prebuilt` is pinned because the currently unpinned newest release
imports a runtime symbol unavailable in the version range required by this
application's LangChain release.

## Environment variables

The local `frontend/.env` file is excluded from the frontend image. Compose
interpolation creates matching Coolify-managed fields instead.
The frontend is generated as static files, so `NUXT_PUBLIC_API_BASE` and
`NUXT_PUBLIC_ALEPHIUM_NODE_URL` are baked into the frontend image at build
time. Rebuild the frontend after changing either value.

- `${VARIABLE:-default}` means use `default` until a value is set in Coolify.
- `${VARIABLE:?}` means the value is required and Coolify prevents deployment
  while it is empty.

`OPENROUTER_API_KEY` remains intentionally absent from Compose: the backend
only reads `API_KEY`, so passing the unused alias would expose an unnecessary
secret to the container.

For local Docker Compose, copy `.env.example` to a root `.env` and fill the
three required values. Docker Compose reads its project-level `.env`; it does
not automatically merge the per-service `.env` files.

For an explicit end-to-end check after deployment, open the application and
start a long chat/translation. Browser DevTools should show a `200` streamed
response from `https://api.henrycoder.com/api/chat/stream` and incremental NDJSON chunks before the
request completes.
