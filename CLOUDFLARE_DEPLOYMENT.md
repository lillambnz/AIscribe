# Cloudflare Deployment Guide for AIscribe

Complete guide to deploying AIscribe using Cloudflare services while maintaining Australian data residency compliance.

## Overview: Cloudflare Architecture for AIscribe

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare Edge Network                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   DNS        │  │     CDN      │  │     WAF      │      │
│  │ (Global)     │  │  (Cached)    │  │ (Security)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ SSL/TLS      │  │  DDoS Protect│  │   Access     │      │
│  │ (Auto)       │  │  (Always On) │  │ (Zero Trust) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Cloudflare Tunnel (Secure Connection)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Your Infrastructure (Australia)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Frontend    │  │   Backend    │  │  PostgreSQL  │      │
│  │  (Pages)     │  │ (GCP/Azure)  │  │ (Cloud SQL)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  R2 Storage  │  │  Workers     │                         │
│  │  (Audio)     │  │  (Edge API)  │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Cloudflare Services for AIscribe

### 1. Cloudflare Pages (Frontend Hosting)
**Use for:** Next.js frontend

**Benefits:**
- Free unlimited bandwidth
- Global CDN (static assets only)
- Automatic deployments from Git
- Free SSL/TLS certificates
- Built-in analytics

**Setup:**

```bash
# 1. Install Wrangler CLI
npm install -g wrangler

# 2. Login to Cloudflare
wrangler login

# 3. Build frontend
cd frontend
npm run build

# 4. Deploy to Pages
npx wrangler pages deploy .next --project-name=aiscribe

# Or connect to GitHub for auto-deployment
```

**Configuration (wrangler.toml):**
```toml
name = "aiscribe-frontend"
compatibility_date = "2024-01-01"

[env.production]
pages_build_output_dir = ".next"

[[env.production.routes]]
pattern = "aiscribe.com.au/*"
zone_name = "aiscribe.com.au"
```

**Important for Compliance:**
- Frontend static assets can be globally distributed
- API calls still go to Australian backend
- No PHI in frontend code

---

### 2. Cloudflare Tunnel (Secure Backend Connection)
**Use for:** Secure connection to backend without exposing IPs

**Benefits:**
- No open ports on your server
- DDoS protection
- Automatic SSL/TLS
- No VPN needed
- Free for up to 50 users

**Setup:**

```bash
# 1. Install cloudflared on your server
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# 2. Authenticate
cloudflared tunnel login

# 3. Create tunnel
cloudflared tunnel create aiscribe-backend

# 4. Configure tunnel
cat > ~/.cloudflared/config.yml <<EOF
tunnel: aiscribe-backend
credentials-file: /root/.cloudflared/<TUNNEL-ID>.json

ingress:
  # API endpoint
  - hostname: api.aiscribe.com.au
    service: http://localhost:8000

  # WebSocket endpoint
  - hostname: ws.aiscribe.com.au
    service: http://localhost:8000
    originRequest:
      noTLSVerify: false

  # Catch-all
  - service: http_status:404
EOF

# 5. Route DNS
cloudflared tunnel route dns aiscribe-backend api.aiscribe.com.au
cloudflared tunnel route dns aiscribe-backend ws.aiscribe.com.au

# 6. Run tunnel
cloudflared tunnel run aiscribe-backend

# 7. Install as service
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

**Docker Integration:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    # ... existing backend config ...

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: aiscribe-cloudflared
    command: tunnel --no-autoupdate run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    restart: unless-stopped
    depends_on:
      - backend
```

---

### 3. Cloudflare R2 (Audio Storage)
**Use for:** S3-compatible audio file storage

**Benefits:**
- No egress fees (unlike AWS S3)
- S3-compatible API
- $0.015/GB/month storage
- Australian data location available
- Automatic encryption

**Setup:**

```bash
# 1. Create R2 bucket via dashboard or CLI
wrangler r2 bucket create aiscribe-audio --jurisdiction=eu  # Use 'eu' for now, 'au' when available

# 2. Get R2 credentials
# Dashboard → R2 → Manage R2 API Tokens
```

**Backend Configuration:**

```python
# backend/.env
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=<r2-access-key>
S3_SECRET_ACCESS_KEY=<r2-secret-key>
S3_BUCKET_NAME=aiscribe-audio
```

**Code (already S3-compatible):**
```python
# Our backend already supports S3-compatible storage!
# Just update .env and it works with R2
```

---

### 4. Cloudflare Workers (Edge API - Optional)
**Use for:** Lightweight API operations at the edge

**Example Use Cases:**
- Authentication checks
- Rate limiting
- Request routing
- WebSocket connection management

**Example Worker (Auth Middleware):**

```typescript
// workers/auth-middleware.ts
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Verify JWT at edge before hitting backend
    const authHeader = request.headers.get('Authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return new Response('Unauthorized', { status: 401 });
    }

    const token = authHeader.substring(7);

    // Verify token (using Jose library)
    try {
      const verified = await verifyJWT(token, env.JWT_SECRET);

      // Add user info to headers
      const newRequest = new Request(request);
      newRequest.headers.set('X-User-ID', verified.sub);
      newRequest.headers.set('X-Clinic-ID', verified.clinic_id);

      // Forward to origin (Australian backend)
      return fetch(newRequest);
    } catch (e) {
      return new Response('Invalid token', { status: 401 });
    }
  }
};
```

**Deploy:**
```bash
wrangler deploy workers/auth-middleware.ts
```

---

### 5. Cloudflare WAF (Web Application Firewall)
**Use for:** Security and compliance

**Key Rules for AIscribe:**

```javascript
// Cloudflare Dashboard → Security → WAF

// Rule 1: Geo-blocking (optional)
// Allow only Australia + New Zealand
(ip.geoip.country ne "AU" and ip.geoip.country ne "NZ")

// Rule 2: Rate limiting for API
(http.request.uri.path eq "/v1/auth/login" and rate() > 5)

// Rule 3: Block common attacks
(cf.threat_score > 10)

// Rule 4: Protect API endpoints
(http.request.uri.path contains "/v1/" and not http.request.headers["authorization"][0] contains "Bearer")

// Rule 5: Medical data protection
(http.request.uri.path contains "/v1/encounters" and http.request.method eq "DELETE" and not verified_jwt())
```

**OWASP Rules:** Enable all OWASP Core Ruleset

---

### 6. Cloudflare Access (Zero Trust)
**Use for:** Secure admin access, staging environments

**Setup:**

```bash
# 1. Enable Cloudflare Access
# Dashboard → Zero Trust → Access → Applications

# 2. Create application
Name: AIscribe Admin
Application domain: admin.aiscribe.com.au
Type: Self-hosted

# 3. Add authentication
Identity Providers:
  - Google Workspace
  - Azure AD (Microsoft Entra)
  - One-time PIN

# 4. Access policies
Policy 1: Admin Access
  - Email: admin@yourclinic.com.au
  - Email domain: @yourclinic.com.au

Policy 2: Developer Access
  - Email: dev@yourcompany.com
  - Country: Australia
```

**Protect Staging Environment:**
```yaml
# Protect staging.aiscribe.com.au
# Only accessible via Cloudflare Access
# No VPN needed!
```

---

### 7. Cloudflare DNS
**Use for:** Fast, secure DNS

**Setup:**

```bash
# 1. Add domain to Cloudflare
# Dashboard → Websites → Add a site

# 2. Update nameservers at your registrar to:
# noah.ns.cloudflare.com
# sue.ns.cloudflare.com

# 3. Add DNS records
aiscribe.com.au          A/CNAME  → Cloudflare Pages
api.aiscribe.com.au      CNAME    → Cloudflare Tunnel
ws.aiscribe.com.au       CNAME    → Cloudflare Tunnel
www.aiscribe.com.au      CNAME    → aiscribe.com.au
```

**DNS Configuration:**
```
Type    Name        Content                     Proxy   TTL
A       @           192.0.2.1                   ✅      Auto
CNAME   api         tunnel-id.cfargotunnel.com  ✅      Auto
CNAME   ws          tunnel-id.cfargotunnel.com  ✅      Auto
CNAME   www         aiscribe.com.au             ✅      Auto
TXT     @           v=spf1 include:_spf... ~all -       Auto
```

---

### 8. Cloudflare SSL/TLS
**Use for:** Automatic HTTPS

**Setup:**

```bash
# 1. Enable Full (Strict) SSL/TLS
# Dashboard → SSL/TLS → Overview → Full (strict)

# 2. Enable Always Use HTTPS
# SSL/TLS → Edge Certificates → Always Use HTTPS: On

# 3. Minimum TLS Version: 1.2 (or 1.3)

# 4. Enable HSTS
# SSL/TLS → Edge Certificates → HTTP Strict Transport Security
Max Age: 12 months
Include subdomains: Yes
Preload: Yes

# 5. Enable Authenticated Origin Pulls
# SSL/TLS → Origin Server → Authenticated Origin Pulls: On
```

---

## Complete Deployment Workflow

### Step 1: Setup Cloudflare Account
```bash
# 1. Sign up at cloudflare.com
# 2. Add your domain (aiscribe.com.au)
# 3. Update nameservers
# 4. Enable SSL/TLS
```

### Step 2: Deploy Frontend to Pages
```bash
cd frontend

# Build
npm run build

# Deploy
npx wrangler pages deploy out --project-name=aiscribe --branch=production

# Or connect GitHub for auto-deploy
# Dashboard → Pages → Create a project → Connect to Git
```

### Step 3: Setup Cloudflare Tunnel for Backend
```bash
# On your Australian server (GCP/Azure)
cloudflared tunnel login
cloudflared tunnel create aiscribe
cloudflared tunnel route dns aiscribe api.aiscribe.com.au
cloudflared tunnel run aiscribe
```

### Step 4: Configure R2 for Storage
```bash
# Create bucket
wrangler r2 bucket create aiscribe-audio

# Update backend .env
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=<key>
S3_SECRET_ACCESS_KEY=<secret>
```

### Step 5: Enable Security Features
```bash
# Dashboard → Security
# - Enable WAF
# - Configure rate limiting
# - Enable DDoS protection
# - Set up Access for admin
```

### Step 6: Configure DNS
```bash
# Add all DNS records
# Point api.aiscribe.com.au to tunnel
# Point aiscribe.com.au to Pages
```

---

## Australian Compliance with Cloudflare

### ✅ Data Residency Compliance

**Challenge:** Cloudflare's edge network is global
**Solution:** Strategic service usage

```
Global (OK):
✅ Frontend static assets (Next.js build output)
✅ DNS
✅ SSL/TLS termination
✅ CDN for public content

Australian Only (Required):
✅ Backend API (via Tunnel to AU server)
✅ PostgreSQL database (GCP Sydney/Azure AU East)
✅ Audio files (R2 with AU preference, or AU-based S3)
✅ PHI data (never leaves AU servers)

Edge Processing (Careful):
⚠️ Workers can run at edge (use for non-PHI only)
⚠️ Analytics (use Cloudflare Analytics or self-host)
```

### Configuration for Compliance:

```toml
# wrangler.toml
[env.production]
# For Workers that handle PHI, specify Australian data centers
routes = [
  { pattern = "api.aiscribe.com.au/*", zone_name = "aiscribe.com.au" }
]

# Ensure data stays in Australia
placement = { mode = "smart" }  # Routes to nearest data center
```

**R2 Storage Location:**
```bash
# When Australia becomes available as jurisdiction:
wrangler r2 bucket create aiscribe-audio --jurisdiction=apac

# For now, use AU-based cloud storage:
# - GCP: australia-southeast1
# - Azure: Australia East
```

---

## Cost Estimate (Cloudflare)

### Free Tier (Good for Starting)
- ✅ DNS (unlimited)
- ✅ CDN (unlimited bandwidth)
- ✅ SSL/TLS certificates
- ✅ DDoS protection (unmetered)
- ✅ Cloudflare Pages (500 builds/month)
- ✅ Cloudflare Tunnel (1 tunnel free)
- ✅ WAF (5 rules free)

### Paid Services
- **R2 Storage:**
  - $0.015/GB/month storage
  - $0 egress (FREE!)
  - ~$15/month for 1TB

- **Workers:**
  - $5/month for 10M requests
  - $0.50 per additional 1M requests

- **Cloudflare Access:**
  - $3/user/month
  - Or $7/user/month for advanced features

- **Pro Plan** ($20/month):
  - Advanced WAF
  - Image optimization
  - Better analytics

**Estimated Monthly Cost:**
- Startup (0-100 clinics): $0-50/month
- Growing (100-500 clinics): $50-200/month
- Scale (500+ clinics): $200-1000/month

---

## Environment Variables Update

```bash
# backend/.env
# Frontend URL (Cloudflare Pages)
CORS_ORIGINS=["https://aiscribe.com.au", "https://www.aiscribe.com.au"]

# R2 Storage
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=<r2-access-key>
S3_SECRET_ACCESS_KEY=<r2-secret-key>
S3_BUCKET_NAME=aiscribe-audio
S3_REGION=auto

# Cloudflare specific
CLOUDFLARE_ACCOUNT_ID=<account-id>
CLOUDFLARE_API_TOKEN=<token>
```

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://api.aiscribe.com.au
NEXT_PUBLIC_WS_URL=wss://ws.aiscribe.com.au
```

---

## Security Best Practices

### 1. Enable Bot Protection
```bash
# Dashboard → Security → Bots
# Block automated traffic to /v1/auth/login
```

### 2. Configure Page Rules
```bash
# Cache static assets
Cache Level: Standard
Edge Cache TTL: 1 month
Pattern: *.js, *.css, *.png, *.jpg

# Don't cache API
Cache Level: Bypass
Pattern: api.aiscribe.com.au/*
```

### 3. Enable Rate Limiting
```javascript
// Free: 10,000 requests/month
// Pattern: /v1/auth/login
// Rate: 5 requests per minute per IP
```

### 4. Enable DNSSEC
```bash
# Dashboard → DNS → Settings → DNSSEC: Enabled
```

---

## Monitoring & Analytics

### Cloudflare Analytics (Built-in)
```bash
# Dashboard → Analytics
# - Requests
# - Bandwidth
# - Threats blocked
# - Performance insights
```

### Custom Logging (Workers)
```typescript
// Send logs to your backend
export default {
  async fetch(request: Request): Promise<Response> {
    const start = Date.now();
    const response = await fetch(request);
    const duration = Date.now() - start;

    // Log to your backend
    await fetch('https://api.aiscribe.com.au/internal/logs', {
      method: 'POST',
      body: JSON.stringify({
        path: new URL(request.url).pathname,
        duration,
        status: response.status,
      })
    });

    return response;
  }
};
```

---

## Migration Checklist

- [ ] Sign up for Cloudflare
- [ ] Add domain to Cloudflare
- [ ] Update nameservers
- [ ] Deploy frontend to Pages
- [ ] Install cloudflared on server
- [ ] Create Cloudflare Tunnel
- [ ] Configure DNS records
- [ ] Enable SSL/TLS (Full Strict)
- [ ] Set up R2 bucket
- [ ] Update environment variables
- [ ] Configure WAF rules
- [ ] Enable rate limiting
- [ ] Set up Access for admin
- [ ] Test end-to-end
- [ ] Monitor for 24 hours
- [ ] Update DNS TTL to production values

---

## Troubleshooting

### Issue: "Tunnel not connecting"
```bash
# Check cloudflared service
sudo systemctl status cloudflared

# View logs
sudo journalctl -u cloudflared -f

# Test tunnel
cloudflared tunnel info aiscribe
```

### Issue: "502 Bad Gateway"
```bash
# Check backend is running
curl http://localhost:8000/health

# Check tunnel config
cat ~/.cloudflared/config.yml

# Restart tunnel
sudo systemctl restart cloudflared
```

### Issue: "R2 Access Denied"
```bash
# Verify credentials
wrangler r2 bucket list

# Check CORS settings
# Dashboard → R2 → aiscribe-audio → Settings → CORS
```

---

## Alternative: Cloudflare for SaaS

If you want to offer white-label AIscribe to other clinics:

```bash
# Each clinic gets their own subdomain
# clinic1.aiscribe.com.au
# clinic2.aiscribe.com.au

# Or custom domains
# transcription.drsmith.com.au

# Cloudflare for SaaS handles:
# - Custom SSL certificates
# - DNS management
# - Automatic provisioning
```

Cost: $2/custom hostname/month

---

## Summary: Why Cloudflare?

**Pros:**
✅ Free SSL/TLS and CDN
✅ Excellent DDoS protection
✅ No egress fees (R2)
✅ Simple deployment (Pages, Tunnel)
✅ Great performance
✅ Built-in security (WAF, Access)
✅ Cost-effective at scale

**Cons:**
⚠️ R2 doesn't have Australian jurisdiction yet (use AU cloud storage for PHI)
⚠️ Workers run at edge (careful with PHI)
⚠️ Some features require paid plans

**Recommendation:**
Use Cloudflare for:
- Frontend hosting (Pages)
- CDN and security (free tier)
- Tunnel to backend (free)
- Non-PHI storage (R2)

Keep in Australia:
- Backend API (via Tunnel)
- PostgreSQL database
- Audio files (until R2 AU available)
- PHI data

This gives you best of both worlds: global performance + Australian compliance!
