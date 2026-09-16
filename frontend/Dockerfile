FROM oven/bun:1 AS build

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

ARG NUXT_PUBLIC_API_BASE=https://api.henrycoder.com/api
ARG NUXT_PUBLIC_ALEPHIUM_NODE_URL=https://node.testnet.alephium.org

RUN bun run generate

FROM nginx:stable-alpine-slim

EXPOSE 3000

COPY --from=build /app/.output/public /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]
