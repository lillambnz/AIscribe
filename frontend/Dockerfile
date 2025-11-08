# Multi-stage build for Next.js frontend
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Development command (override in docker-compose for production)
CMD ["npm", "run", "dev"]
