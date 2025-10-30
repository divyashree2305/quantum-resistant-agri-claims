#!/bin/bash

echo "⚠️  WARNING: This will delete ALL Docker containers, volumes, and data!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo "📦 Stopping containers..."
docker-compose down -v

echo "🗑️  Removing volumes..."
docker volume prune -f

echo "🔨 Rebuilding from scratch..."
docker-compose up -d --build

echo "⏳ Waiting for services to start..."
sleep 30

echo "🗄️  Initializing database..."
docker-compose exec insurance-backend python -c "from models.database import init_db; init_db()"

echo "✅ Reset complete!"
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - PostgreSQL: localhost:54320"
echo "  - Redis: localhost:63790"
echo ""
echo "Database initialized. You can now start using the system!"

