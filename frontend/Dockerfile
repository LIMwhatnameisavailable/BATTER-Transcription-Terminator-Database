FROM node:20-bookworm-slim AS dependencies

WORKDIR /app/frontend

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable \
    && corepack prepare pnpm@9.15.4 --activate \
    && pnpm install --frozen-lockfile

FROM node:20-bookworm-slim AS builder

WORKDIR /app/frontend

COPY --from=dependencies /app/frontend/node_modules ./node_modules
COPY frontend/ ./

ARG BTED_API_ORIGIN=http://backend:8000
ENV BTED_API_ORIGIN=${BTED_API_ORIGIN} \
    NEXT_TELEMETRY_DISABLED=1

RUN corepack enable \
    && corepack prepare pnpm@9.15.4 --activate \
    && pnpm build

FROM node:20-bookworm-slim AS runtime

WORKDIR /app/frontend

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN useradd --create-home --uid 10001 nextjs

COPY --from=builder --chown=nextjs:nextjs /app/frontend/.next ./.next
COPY --from=builder --chown=nextjs:nextjs /app/frontend/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nextjs /app/frontend/package.json ./package.json

USER nextjs

EXPOSE 3000

CMD ["node", "node_modules/next/dist/bin/next", "start"]
