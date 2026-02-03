# =============================================================================
# DocuQuery Frontend Dockerfile - Multi-Stage Build
#
# Stage 1 (deps):    Install node_modules
# Stage 2 (builder): Build the Next.js application
# Stage 3 (runner):  Slim production image with standalone output
#
# Usage:
#   docker build -t docuquery-frontend .
#   docker run -p 3000:3000 docuquery-frontend
# =============================================================================

# --------------- Stage 1: Dependencies ---------------
FROM node:20-alpine AS deps

WORKDIR /app

# Copy dependency files first (Docker layer caching)
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci


# --------------- Stage 2: Builder ---------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy deps from previous stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Build the Next.js app (outputs to .next/)
RUN npm run build


# --------------- Stage 3: Runner ---------------
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output (includes server + minimal node_modules)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Switch to non-root user
USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]