# Use Node.js LTS version for better stability
FROM node:18-alpine

# Install necessary system dependencies
RUN apk add --no-cache python3 make g++ bash

# Set working directory
WORKDIR /app

# Copy only package.json and package-lock.json first (caches dependencies)
COPY package*.json ./

# Install dependencies with detailed output for debugging
RUN npm install --legacy-peer-deps 2>&1 || (echo "npm install failed" && cat /tmp/*.log && exit 1)

# Copy the rest of the app
COPY . .

# Set environment variables for build
ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV SKIP_PREFLIGHT_CHECK=true
ENV TSC_COMPILE_ON_ERROR=true
ENV GENERATE_SOURCEMAP=false
ENV CI=true
ENV NODE_OPTIONS="--max-old-space-size=2048"

# Build the app with error handling
RUN npm run build 2>&1 || (echo "Build failed - check for TypeScript/React errors" && exit 1)
RUN npm install -g serve

# Expose the port
EXPOSE 3002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3002/ || exit 1

# Start the app using npx serve
CMD ["npx", "serve", "-s", "build", "-l", "3002"]
