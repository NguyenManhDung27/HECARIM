# Multi-stage build for the backend
FROM node:18-alpine AS backend-builder

WORKDIR /app/backend
COPY back-end/package*.json ./
RUN npm ci

COPY back-end ./
RUN npm run build

# Backend production image
FROM node:18-alpine AS backend

WORKDIR /app/backend
ENV NODE_ENV=production

COPY --from=backend-builder /app/backend/package*.json ./
RUN npm ci --only=production

COPY --from=backend-builder /app/backend/dist ./dist
COPY back-end/.env.example ./.env

EXPOSE 5000
CMD ["node", "dist/server.js"]

# Frontend build stage
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY front-end/package*.json ./
RUN npm ci

COPY front-end ./
RUN npm run build

# Nginx stage for serving frontend
FROM nginx:alpine AS frontend

COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80