# Multi-stage Dockerfile for Next.js standalone build
FROM node:20-alpine AS base

# Step 1: Install dependencies
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Step 2: Build application
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# next.config.ts rewrites are resolved at build time and baked into the
# standalone server (ARCHITECTURE.md §7, TD-09), so the proxy target must be
# supplied as build arguments. docker-compose.yml sets them for the stack.
ARG BACKEND_ORIGIN=http://backend:8000
ARG ADMIN_URL_PATH=admin
ARG DJANGO_STATIC_PREFIX=static
ENV BACKEND_ORIGIN=${BACKEND_ORIGIN} \
    ADMIN_URL_PATH=${ADMIN_URL_PATH} \
    DJANGO_STATIC_PREFIX=${DJANGO_STATIC_PREFIX}

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Step 3: Production runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
