# Multi-stage build for Next.js application

# Stage 1: Dependencies
FROM node:18-alpine AS deps

WORKDIR /app

# Copy package files
COPY package*.json ./
# Install dependencies
RUN npm ci --legacy-peer-deps

# Stage 2: Builder
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source files
COPY . .

# Set environment for build
ENV NEXT_TELEMETRY_DISABLED=1

# Build Next.js application
RUN npm run build

# Stage 3: Runner
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/next.config.ts ./

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next

# Copy node_modules (production dependencies only if using standalone)
# For standard mode, copy all node_modules from builder
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "start"]

