FROM node:22-alpine AS deps
WORKDIR /app
# Copy the lockfile and install from it so builds are reproducible.
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# NEXT_PUBLIC_* values are inlined at build time, so they must be set here, not at runtime.
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL
RUN npm run build

FROM node:22-alpine AS runner
# Links the published image to the repo on the GHCR package page (final stage).
LABEL org.opencontainers.image.source="https://github.com/roydellclarke/steward-journey"
LABEL org.opencontainers.image.description="StewardPath frontend (Next.js)"
LABEL org.opencontainers.image.licenses="UNLICENSED"
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
