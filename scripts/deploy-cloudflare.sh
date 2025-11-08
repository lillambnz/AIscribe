#!/bin/bash
# Deploy AIscribe to Cloudflare

set -e

echo "🚀 Deploying AIscribe to Cloudflare"
echo "===================================="
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "Installing Wrangler CLI..."
    npm install -g wrangler
fi

# Check if logged in
echo "Checking Cloudflare authentication..."
if ! wrangler whoami &> /dev/null; then
    echo "Please login to Cloudflare:"
    wrangler login
fi

echo "✅ Authenticated with Cloudflare"
echo ""

# Step 1: Deploy Frontend to Pages
echo "📦 Step 1/4: Building and deploying frontend..."
cd frontend

# Build Next.js
echo "Building Next.js application..."
npm run build

# Deploy to Pages
echo "Deploying to Cloudflare Pages..."
npx wrangler pages deploy out \
    --project-name=aiscribe \
    --branch=production \
    --commit-message="Production deployment $(date +%Y-%m-%d)"

cd ..
echo "✅ Frontend deployed to Cloudflare Pages"
echo ""

# Step 2: Create R2 bucket (if not exists)
echo "🗄️  Step 2/4: Setting up R2 storage..."

if wrangler r2 bucket list | grep -q "aiscribe-audio"; then
    echo "R2 bucket 'aiscribe-audio' already exists"
else
    echo "Creating R2 bucket..."
    wrangler r2 bucket create aiscribe-audio
    echo "✅ R2 bucket created"
fi
echo ""

# Step 3: Deploy Workers (optional)
echo "⚡ Step 3/4: Deploying Cloudflare Workers..."

if [ -f "cloudflare/workers/rate-limit.ts" ]; then
    echo "Deploying rate-limit worker..."
    cd cloudflare/workers
    wrangler deploy rate-limit.ts --name aiscribe-rate-limit
    cd ../..
    echo "✅ Rate limit worker deployed"
fi
echo ""

# Step 4: Setup Tunnel (instructions)
echo "🔒 Step 4/4: Cloudflare Tunnel setup"
echo ""
echo "To set up Cloudflare Tunnel for your backend:"
echo ""
echo "1. On your production server (in Australia), run:"
echo "   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb"
echo "   sudo dpkg -i cloudflared.deb"
echo ""
echo "2. Authenticate:"
echo "   cloudflared tunnel login"
echo ""
echo "3. Create tunnel:"
echo "   cloudflared tunnel create aiscribe-backend"
echo ""
echo "4. Copy the tunnel ID and update cloudflare/tunnel-config.yml"
echo ""
echo "5. Route DNS:"
echo "   cloudflared tunnel route dns aiscribe-backend api.aiscribe.com.au"
echo "   cloudflared tunnel route dns aiscribe-backend ws.aiscribe.com.au"
echo ""
echo "6. Run tunnel:"
echo "   cloudflared tunnel run aiscribe-backend"
echo ""
echo "7. Install as service:"
echo "   sudo cloudflared service install"
echo ""

echo "===================================="
echo "🎉 Deployment Complete!"
echo "===================================="
echo ""
echo "Your AIscribe deployment:"
echo ""
echo "  Frontend:   https://aiscribe.com.au (Cloudflare Pages)"
echo "  API:        https://api.aiscribe.com.au (via Tunnel)"
echo "  WebSocket:  wss://ws.aiscribe.com.au (via Tunnel)"
echo "  Storage:    R2 bucket 'aiscribe-audio'"
echo ""
echo "Next steps:"
echo "  1. Configure Cloudflare Tunnel on your server"
echo "  2. Update DNS records in Cloudflare dashboard"
echo "  3. Enable WAF rules for security"
echo "  4. Set up Cloudflare Access for admin"
echo "  5. Configure SSL/TLS to 'Full (strict)'"
echo ""
echo "Documentation: CLOUDFLARE_DEPLOYMENT.md"
echo ""
