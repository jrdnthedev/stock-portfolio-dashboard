# Multi-stage build for Angular application

# Stage 1: Build the Angular application
FROM node:20-alpine AS build

# Set working directory
WORKDIR /workspace

# Copy root workspace package files
COPY package*.json ./

# Copy frontend package files
COPY portfolio-dashboard/package*.json ./portfolio-dashboard/

# Install all dependencies from workspace root
RUN npm ci

# Copy frontend application source
COPY portfolio-dashboard ./portfolio-dashboard/

# Build the application for production
WORKDIR /workspace/portfolio-dashboard
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy custom nginx config (optional)
# COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application from build stage
COPY --from=build /workspace/portfolio-dashboard/dist/portfolio-dashboard/browser /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
