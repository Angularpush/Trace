FROM node:20-alpine AS build

WORKDIR /app

# Install npm dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build production bundle
COPY frontend/ .
RUN npm run build

# Production Nginx reverse proxy image
FROM nginx:alpine

# Copy compiled static assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Nginx proxy configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
