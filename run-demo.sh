#!/bin/bash
# One-command demo script - sets up and runs AIscribe

set -e

echo "🚀 AIscribe - One-Command Demo"
echo "==============================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

echo "📦 Step 1/5: Starting services..."
echo "   (This may take a few minutes on first run)"
docker-compose up -d --build

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if backend is ready
MAX_RETRIES=30
RETRY_COUNT=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -gt $MAX_RETRIES ]; then
        echo "❌ Backend failed to start. Check logs with: docker-compose logs backend"
        exit 1
    fi
    echo "   Waiting for backend... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✅ Services are running"
echo ""

echo "🗄️  Step 2/5: Setting up database..."
docker-compose exec -T backend alembic upgrade head 2>/dev/null || echo "   Migrations already applied"
echo "✅ Database ready"
echo ""

echo "👥 Step 3/5: Creating sample data..."
docker-compose exec -T backend python /app/../scripts/create-sample-data.py 2>/dev/null || echo "   Sample data already exists"
echo ""

echo "💳 Step 4/5: Creating subscription plans..."
docker-compose exec -T backend python /app/../scripts/seed-subscription-plans.py 2>/dev/null || echo "   Plans already exist"
echo ""

echo "🧪 Step 5/5: Running workflow test..."
echo ""
chmod +x scripts/test-full-workflow.sh
./scripts/test-full-workflow.sh

echo ""
echo "🎉 Demo Complete!"
echo ""
echo "================================"
echo "  🌐 Open in your browser:"
echo "================================"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Pricing:   http://localhost:3000/pricing"
echo ""
echo "================================"
echo "  📝 Test Credentials:"
echo "================================"
echo ""
echo "  Email:     demo@aiscribe.com.au"
echo "  Password:  demo123"
echo ""
echo "  OR"
echo ""
echo "  Email:     doctor@example.com"
echo "  Password:  password123"
echo ""
echo "================================"
echo "  🎬 Next Actions:"
echo "================================"
echo ""
echo "  1. Visit http://localhost:3000 in your browser"
echo "  2. Click 'Start Transcribing'"
echo "  3. Grant microphone access"
echo "  4. Speak and watch live transcription!"
echo ""
echo "  To stop: docker-compose down"
echo "  To view logs: docker-compose logs -f"
echo ""
