# ============================================================
# SehatSaathi-AI — Frontend Dockerfile (multi-stage)
# ============================================================
FROM node:22-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile

COPY . .
RUN npm run build


FROM nginx:1.27-alpine AS runtime

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx config for SPA routing
COPY nginx-frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s CMD wget -q -O- http://localhost:3000/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
