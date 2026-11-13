# Panagerry: built by Home Assistant on the machine it runs on (no pre-built image),
# so no `--platform=$BUILDPLATFORM` (not every Docker builder defines it).
FROM node:22-alpine AS build
WORKDIR /app
COPY app/package*.json ./
RUN npm ci
COPY app/ ./
RUN npm run build && npm prune --omit=dev

FROM node:22-alpine
ARG BUILD_VERSION=dev
ARG BUILD_ARCH=amd64
LABEL io.hass.type="addon" io.hass.name="Panagerry" io.hass.version="$BUILD_VERSION" io.hass.arch="$BUILD_ARCH" \
  org.opencontainers.image.source="https://github.com/gerrypc72/panagerry" org.opencontainers.image.version="$BUILD_VERSION"
WORKDIR /app
ENV NODE_ENV=production PORT=8099
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/server ./server
COPY --from=build /app/package.json ./
CMD ["node", "server/index.js"]
