# Remote Ralph LSP Architecture

## Overview

Target topology:

```
Browser (Monaco editor)
        ↓ WebSocket (JSON-RPC)
Backend proxy (Node.js)
        ↓ stdio/TCP bridge
Java Ralph language server
```

The browser never talks directly to the JVM process. A Node.js proxy terminates WebSocket connections, forwards framed LSP traffic to the Java server, and handles lifecycle, auth, and logging. Deployment options:

* **On-demand JVM per client** – proxy spawns a fresh `java -jar ralph-lsp.jar` process for each WebSocket session, piping stdin/stdout. Good isolation, higher resource cost.
* **Shared JVM over TCP** – Ralph server exposes a TCP socket (new mode) and proxy multiplexes multiple WebSocket clients to it. Requires implementing deterministic multiplexing in the proxy; useful when JVM startup cost must be amortised.

The following sections outline the implementation plans for each layer and an accompanying `docker-compose` setup.

---

## Frontend connector (browser)

### Stack

| Concern              | Choice                                      |
|----------------------|----------------------------------------------|
| Bundler/dev server   | Vite (TypeScript template)                   |
| Editor               | `monaco-editor` (ESM build)                  |
| LSP client           | `monaco-languageclient` + `vscode-ws-jsonrpc`|
| State management     | Lightweight in-module store (Zustand optional) |
| Transport            | WebSocket (wss://) to proxy                  |

### Client modules

1. **`src/lsp/connection.ts`**
   * Wraps websocket connection, performs JSON-RPC framing using `createWebSocketConnection` from `vscode-ws-jsonrpc`.
   * Exposes lifecycle hooks (open/close/error/reconnect).
   * Injects optional auth header token via query string or `Sec-WebSocket-Protocol`.

2. **`src/lsp/client.ts`**
   * Creates `MonacoLanguageClient` instance.
   * Calls `client.start()` and wires disposal when socket closes.
   * Implements reconnection with exponential backoff; replays `didOpen` documents after reconnect.

3. **`src/editor/MonacoRalphEditor.tsx`**
   * React/Vue/Svelte wrapper (choose framework) mounting `monaco-editor`.
   * Registers language basics (if syntax provided) and delegates LSP capabilities to client.
   * Keeps open document state: `model.onDidChangeContent` triggers `didChange` through the language client (handled automatically once registered).

4. **`src/config.ts`**
   * Reads `VITE_LSP_PROXY_URL`, `VITE_LSP_AUTH_TOKEN`, `VITE_LOG_LEVEL`.
   * Provides defaults for local dev (`ws://localhost:3000`).

### Initialization flow

1. App bootstraps Monaco, loads Ralph syntax (optional from existing VS Code TM grammar converted to Monarch).
2. Fetch configuration (optional secure endpoint) before connecting.
3. Create WebSocket connection to proxy.
4. Once open, instantiate language client with `createLanguageClient` helper and call `start()`.
5. On close, display toast & retry (unless manual disconnect).

### Diagnostics & UX extras

* Surface diagnostics via `monaco.languages.registerCodeActionProvider` or rely on LSP diagnostics pushing into Monaco automatically through `monaco-languageclient`.
* Show connection status indicator with last error message.
* Support multiple workspaces by requesting workspace folders via custom API (proxy may restrict); start with single root from configuration.
* Provide upload/import of local files via browser FS Access or remote repo fetch.

### Packaging & deployment

* `npm run build` produces static assets served by CDN / static bucket.
* For local dev against dockerised backend, run `npm run dev -- --host` and set proxy URL to `ws://localhost:3000`.
* Consider embedding auth token via cookie; ensure WebSocket uses TLS in production.

---

## Backend proxy (Node.js)

### Responsibilities

* Accept WebSocket connections, validate auth, negotiate JSON-RPC.
* Spawn / connect to Ralph LSP server.
* Stream data bidirectionally, handle backpressure, close sessions cleanly.
* Collect per-session logs & metrics.

### Process model options

1. **Spawn-per-session (default)**
   * Each connection triggers `child_process.spawn(JAVA_CMD, JAVA_ARGS)` with stdio pipes.
   * Proxy forwards WS messages to stdin and stdout back to WS.
   * On disconnect/error, kill the child.
   * Isolation simplifies workspace management and avoids multiplexing.

2. **Shared server mode (optional)**
   * Proxy connects to long-lived TCP server (see Docker compose plan).
   * Requires session routing if multiple clients share same server – typically by running one proxy per user or by enforcing single client.

### Suggested project structure

```
proxy/
  package.json
  tsconfig.json
  src/
    index.ts               // entrypoint, creates HTTP(S)+WS server
    session.ts             // manages java child process lifecycle
    logging.ts             // pino/winston configuration
    auth.ts                // token/cookie validation
    config.ts              // env var parsing via zod/envalid
    metrics.ts             // Prometheus counters (optional)
```

### Key implementation points

* Use Node 18+ (ESM or TypeScript compiled to CJS).
* Use `ws` for WebSocket server; optionally wrap with `http` or `https` server for TLS termination (or front with reverse proxy).
* Forward binary `Buffer` chunks verbatim; no JSON parsing in proxy.
* Watch child stdout/stderr for diagnostics; prefix logs with session ID.
* Implement heartbeat/ping to detect dead connections and terminate child processes.
* Configurable limits:
  * `MAX_SESSIONS`, `MAX_BUFFER_BYTES`, `IDLE_TIMEOUT_SEC`.
* Security hooks:
  * Expect `Authorization: Bearer <token>` header or query string `token`.
  * Validate token locally or via external auth service before spawning server.
* Observability:
  * Expose `/healthz` (proxy ready if accepting connections).
  * Expose `/metrics` (Prometheus) for active sessions, spawn failures, etc.

### Environment variables

| Variable                | Description                                                      | Default            |
|-------------------------|------------------------------------------------------------------|--------------------|
| `PORT`                  | WebSocket listener port                                          | `3000`             |
| `JAVA_CMD`              | Java binary                                                       | `java`             |
| `JAVA_ARGS`             | Arguments for Ralph LSP (e.g. `-jar /opt/ralph/ralph-lsp.jar`)    | none               |
| `LSP_SERVER_HOST`       | (Shared mode) hostname of TCP LSP server                          | `localhost`        |
| `LSP_SERVER_PORT`       | (Shared mode) TCP port                                            | `7000`             |
| `AUTH_TOKEN`            | Static bearer token (development)                                | empty (disabled)   |
| `IDLE_TIMEOUT_SEC`      | Seconds before killing idle session                              | `900`              |
| `LOG_LEVEL`             | `info`, `debug`, etc.                                             | `info`             |

### Dependencies

* `ws`, `yargs`/`commander` for CLI, `pino` for logging, `envalid` for config, `uuid` for session IDs, `prom-client` optional.

---

## Docker Compose deployment

### Purpose

* Provide reproducible local/preview environment with one Ralph LSP JVM instance and one proxy instance.
* Support both spawn-per-session (proxy launches its own `java`) and shared TCP mode. Compose focuses on **shared TCP mode** to avoid Java inside proxy container.

### Preparatory work

1. Extend `Main.scala` to support TCP mode (if `RALPH_LSP_TCP_BIND` set). Sketch:
   * Parse env var `RALPH_LSP_TCP_BIND` (e.g. `0.0.0.0:7000`).
   * If present, create `ServerSocket`, call `accept()`, pass streams into existing `start(in, out)`.
   * Allow loop to accept one client at a time or wrap in while loop for sequential sessions.
2. Produce runnable fat jar via `sbt assembly` (or reuse existing `target/scala-2.13/ralph-lsp.jar`).

### File layout

```
infra/
  docker-compose.yml
  proxy/Dockerfile
  ralph-lsp/Dockerfile
```

### `ralph-lsp` service

* Dockerfile (OpenJDK 21 slim):
  ```dockerfile
  FROM eclipse-temurin:21-jre
  WORKDIR /opt/ralph
  COPY target/scala-2.13/ralph-lsp.jar /opt/ralph/
  ENV RALPH_LSP_TCP_BIND=0.0.0.0:7000
  EXPOSE 7000
  CMD ["java","-jar","/opt/ralph/ralph-lsp.jar"]
  ```
* Optional volume mount for logs: `./logs:/var/log/ralph` (if server supports `RALPH_LSP_LOG_HOME`).
* Healthcheck: TCP on port 7000 or custom HTTP when added.

### `proxy` service

* Dockerfile (Node 20 alpine):
  ```dockerfile
  FROM node:20-alpine
  WORKDIR /app
  COPY proxy/package*.json ./
  RUN npm ci --omit=dev
  COPY proxy/dist ./dist
  ENV PORT=3000 \
      LSP_SERVER_HOST=ralph-lsp \
      LSP_SERVER_PORT=7000
  EXPOSE 3000
  CMD ["node","dist/index.js"]
  ```
* Mount additional config via env or secrets for auth tokens.
* Optionally run `npm run build` during image build if using TypeScript.

### Example `docker-compose.yml`

```yaml
tservices:
  ralph-lsp:
    build:
      context: ../
      dockerfile: infra/ralph-lsp/Dockerfile
    environment:
      RALPH_LSP_TCP_BIND: "0.0.0.0:7000"
      RALPH_LSP_LOG_HOME: /var/log/ralph
    volumes:
      - ./logs:/var/log/ralph
    expose:
      - "7000"

  proxy:
    build:
      context: ../
      dockerfile: infra/proxy/Dockerfile
    depends_on:
      - ralph-lsp
    environment:
      PORT: "3000"
      LSP_SERVER_HOST: "ralph-lsp"
      LSP_SERVER_PORT: "7000"
      AUTH_TOKEN: "dev-token"
    ports:
      - "3000:3000"
```

(Ensure the `services:` key spelling is correct when authoring.)

### Running locally

1. Build assets:
   * `sbt assembly` → produces `target/scala-2.13/ralph-lsp.jar`
   * `(cd proxy && npm install && npm run build)`
2. `docker compose -f infra/docker-compose.yml up --build`
3. Frontend dev server connects to `ws://localhost:3000`.

### Production considerations

* Use TLS termination (nginx/Traefik) in front of proxy. Terminate TLS at reverse proxy and forward to Node via localhost network.
* Scale `proxy` horizontally with sticky sessions (each session binds to backend process). For shared JVM, run one `ralph-lsp` per proxy and scale pairs.
* Externalise logs via stdout or mount to persistent storage.
* Add observability (Grafana/Prometheus scraping proxy metrics endpoint).

---

## Next steps checklist

* [ ] Implement TCP mode in `Main.scala` + configuration plumbing.
* [ ] Scaffold `proxy/` TypeScript project with the described modules.
* [ ] Scaffold `frontend/` Vite project for Monaco connector.
* [ ] Add `infra/` Dockerfiles and `docker-compose.yml` skeleton.
* [ ] Provide CI jobs to build images and run container smoke tests.

This document can be migrated to the target repository as the blueprint for implementation.