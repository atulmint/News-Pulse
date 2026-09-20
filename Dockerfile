FROM node:20-bookworm-slim

# Install Python 3, pip, and required build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    libpq-dev \
    gcc \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy full repository (backend & scraper)
COPY . .

# Install Python scraper dependencies
WORKDIR /app/scraper
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

# Install Node backend dependencies, generate Prisma client, and build NestJS
WORKDIR /app/backend
RUN npm install
RUN npx prisma generate
RUN npm run build

# Set production environment variables
ENV NODE_ENV=production
ENV PYTHON_PATH=python3
ENV PORT=3001

EXPOSE 3001

# Automatically apply pending Prisma migrations before starting NestJS HTTP server
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/main.js"]
