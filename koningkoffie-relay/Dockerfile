FROM node:22-bookworm-slim AS builder

ARG RELAY_COMMIT=860983f6d41fc73670910efc177a079f6e4715ee

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN git init \
    && git remote add origin https://github.com/richardosseweijer/Relay-AV-Room-Control-.git \
    && git fetch --depth 1 origin "${RELAY_COMMIT}" \
    && git checkout --detach FETCH_HEAD \
    && rm -rf .git

RUN npm ci --include=dev \
    && npm run build \
    && npm cache clean --force

FROM node:22-bookworm-slim

LABEL org.opencontainers.image.source="https://github.com/cschriel/Meuk-voor-Umbrel" \
      org.opencontainers.image.title="Relay AV Room Control for Umbrel" \
      org.opencontainers.image.licenses="MIT"

ENV NODE_ENV=production \
    PORT=8081

WORKDIR /app
COPY --from=builder --chown=1000:1000 /app /app

USER 1000:1000
EXPOSE 8081

CMD ["npm", "start"]
