#!/bin/bash
# Setup script for AIscribe development environment

set -e

echo "🚀 Setting up AIscribe..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env files from examples
echo "📝 Creating environment files..."

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env"
else
    echo "⏭️  backend/.env already exists"
fi

if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.local.example frontend/.env.local
    echo "✅ Created frontend/.env.local"
else
    echo "⏭️  frontend/.env.local already exists"
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Run database migrations
echo "📊 Running database migrations..."
docker-compose run --rm backend alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Start all services: docker-compose up"
echo "  2. Access the API: http://localhost:8000/docs"
echo "  3. Access the frontend: http://localhost:3000"
echo ""
echo "🔧 Development commands:"
echo "  - Backend logs: docker-compose logs -f backend"
echo "  - Frontend logs: docker-compose logs -f frontend"
echo "  - Database shell: docker-compose exec postgres psql -U aiscribe -d aiscribe"
echo "  - Create migration: docker-compose run --rm backend alembic revision --autogenerate -m 'description'"
echo ""
