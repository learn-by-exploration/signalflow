# ── Stage 1: Dependencies ──
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

# ── Stage 2: Build ──
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

# Build-time environment variables (NEXT_PUBLIC_* are inlined during build)
ARG NEXT_PUBLIC_SHOW_DEMO=false
ARG NEXT_PUBLIC_API_KEY
ARG BACKEND_URL=http://localhost:8000
ARG MKG_URL=http://localhost:8001
ENV NEXT_PUBLIC_SHOW_DEMO=$NEXT_PUBLIC_SHOW_DEMO
ENV NEXT_PUBLIC_API_KEY=$NEXT_PUBLIC_API_KEY
ENV BACKEND_URL=$BACKEND_URL
ENV MKG_URL=$MKG_URL

RUN npm run build

# ── Stage 3: Production ──
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
