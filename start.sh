#!/usr/bin/env bash
set -euo pipefail

# ─── SignalFlow AI — Start Script ───
# Builds and starts all services via Docker Compose.
# Usage: ./start.sh [--build] [--detach] [--no-celery] [--fresh]

BUILD=false
DETACH=false
NO_CELERY=false
FRESH=false

for arg in "$@"; do
  case "$arg" in
    --build)     BUILD=true ;;
    --detach|-d) DETACH=true ;;
    --no-celery) NO_CELERY=true ;;
    --fresh)     FRESH=true ;;
    --help|-h)
      echo "Usage: ./start.sh [--build] [--detach|-d] [--no-celery] [--fresh]"
      echo "  --build      Force rebuild of Docker images"
      echo "  --detach|-d  Run in background"
      echo "  --no-celery  Skip Celery worker (signals won't auto-generate)"
      echo "  --fresh      Wipe volumes and start clean (fixes Redis RDB errors)"
      exit 0
      ;;
  esac
done

echo "🚀 SignalFlow AI — Starting..."

# Check prerequisites
if ! command -v docker &>/dev/null; then
  echo "❌ Docker is not installed. Please install Docker first."
  exit 1
fi

if ! docker info &>/dev/null 2>&1; then
  echo "❌ Docker daemon is not running. Please start Docker."
  exit 1
fi

# Check .env file
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your API keys, then re-run this script."
    exit 1
  else
    echo "❌ No .env or .env.example found."
    exit 1
  fi
fi

# Build services
COMPOSE_ARGS=""
if [ "$DETACH" = true ]; then
  COMPOSE_ARGS="-d"
fi

SERVICES="db redis backend frontend"
if [ "$NO_CELERY" = false ]; then
  SERVICES="$SERVICES celery"
fi

if [ "$FRESH" = true ]; then
  echo "🧹 Wiping volumes for a clean start..."
  docker compose down -v --remove-orphans 2>/dev/null || true
fi

if [ "$BUILD" = true ]; then
  echo "🔨 Building Docker images..."
  docker compose build
fi

echo "📦 Starting services: $SERVICES"
if ! docker compose up $COMPOSE_ARGS $SERVICES; then
  # Detect the common Redis RDB incompatibility failure and give a helpful hint
  if docker compose logs redis 2>/dev/null | grep -q "Can't handle RDB format"; then
    echo ""
    echo "❌ Redis failed: incompatible RDB dump file from a previous run."
    echo "   Fix: ./start.sh --fresh (wipes volumes and starts clean)"
  fi
  exit 1
fi

if [ "$DETACH" = true ]; then
  echo ""
  echo "✅ SignalFlow AI is starting in the background!"
  echo ""
  echo "   🌐 Frontend:  http://localhost:3000"
  echo "   🔌 Backend:   http://localhost:8000"
  echo "   📚 API Docs:  http://localhost:8000/docs"
  echo "   ❤️  Health:    http://localhost:8000/health"
  echo ""
  echo "   Logs:  docker compose logs -f"
  echo "   Stop:  docker compose down"
  echo ""
  # Wait for backend to become healthy, then run migrations
  echo "⏳ Waiting for services to be ready..."
  READY=false
  for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health &>/dev/null; then
      READY=true
      echo "✅ Backend is ready!"
      break
    fi
    sleep 2
  done

  if [ "$READY" = true ]; then
    echo "🗄️  Running database migrations..."
    if docker compose exec -T backend alembic upgrade head; then
      echo "✅ Migrations applied."
    else
      echo "⚠️  Migrations failed — check: docker compose logs backend"
    fi
  else
    echo "⚠️  Backend did not become healthy in time — check: docker compose logs backend"
  fi
fi
