# AIscribe Quick Start - See It Working!

This guide will get AIscribe running in under 10 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Terminal/command line access
- A web browser

## Step 1: Start the Services

```bash
# Navigate to project directory
cd /home/user/AIscribe

# Start all services (Postgres, Backend, Frontend)
docker-compose up --build
```

**What you'll see:**
- PostgreSQL starting on port 5432
- Backend API starting on port 8000
- Frontend starting on port 3000

**Wait for:** "Application startup complete" messages

⏱️ First build takes 3-5 minutes. Subsequent starts are faster.

## Step 2: Set Up the Database

Open a **new terminal** (keep the first one running):

```bash
# Navigate to project
cd /home/user/AIscribe

# Run database migrations
docker-compose exec backend alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, Initial migration
INFO  [alembic.runtime.migration] Running upgrade xxxxx -> yyyyy, Add subscriptions
```

## Step 3: Create Sample Data

```bash
# Create sample clinic and users
docker-compose exec backend python /app/../scripts/create-sample-data.py

# Create subscription plans
docker-compose exec backend python /app/../scripts/seed-subscription-plans.py
```

**Expected output:**
```
✅ Created clinic: Sydney General Practice (ID: 1)
✅ Created user: doctor@example.com (Role: doctor)
✅ Created user: nurse@example.com (Role: nurse)
✅ Created user: admin@example.com (Role: admin)

🎉 Sample data created successfully!

Test credentials:
  Doctor: doctor@example.com / password123
  Nurse: nurse@example.com / password123
  Admin: admin@example.com / password123
```

```
✅ Created plan: Solo Practitioner - $149/month
✅ Created plan: Small Clinic - $599/month
✅ Created plan: Medium Practice - $1,499/month
✅ Created plan: Enterprise - $3,999/month
```

## Step 4: Access the Application

Open your browser and navigate to:

### 🌐 Frontend
**http://localhost:3000**

You should see the AIscribe homepage with:
- Hero section
- Feature cards
- Compliance banner

### 📚 API Documentation
**http://localhost:8000/docs**

You should see the interactive Swagger UI with all API endpoints.

### ❤️ Health Check
**http://localhost:8000/health**

Should return: `{"status":"healthy","service":"AIscribe API","version":"0.1.0"}`

## Step 5: Test User Registration & Login

### Option A: Using the API Docs (Easy)

1. Open **http://localhost:8000/docs**
2. Find **POST /v1/auth/register**
3. Click "Try it out"
4. Enter this JSON:

```json
{
  "email": "test@clinic.com.au",
  "password": "testpassword123",
  "full_name": "Dr. Test User",
  "clinic_id": 1
}
```

5. Click "Execute"
6. Copy the `access_token` from the response

### Option B: Using cURL

```bash
# Register a new user
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@clinic.com.au",
    "password": "testpassword123",
    "full_name": "Dr. Test User",
    "clinic_id": 1
  }'

# Response will include an access_token - save it!
```

### Login with existing user

```bash
# Login
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=doctor@example.com&password=password123"

# Save the access_token from response
```

## Step 6: View Subscription Plans

### In Browser:
**http://localhost:3000/pricing**

You should see:
- 4 pricing tiers
- Monthly/Annual toggle
- Feature comparison
- FAQ section

### Via API:

```bash
# Get all plans
curl http://localhost:8000/v1/billing/plans
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "solo",
    "display_name": "Solo Practitioner",
    "price_monthly": 149.0,
    "hours_included": 100,
    "max_users": 1,
    "features": [...]
  },
  ...
]
```

## Step 7: Subscribe to a Plan

```bash
# Replace YOUR_TOKEN with the token from Step 5
TOKEN="your_access_token_here"

# Subscribe to the "Solo" plan (plan_id: 1)
curl -X POST http://localhost:8000/v1/billing/subscribe \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 1,
    "trial_days": 14
  }'
```

**Response:**
```json
{
  "id": 1,
  "clinic_id": 1,
  "plan": {
    "name": "solo",
    "display_name": "Solo Practitioner",
    "price_monthly": 149.0,
    ...
  },
  "status": "trialing",
  "trial_ends_at": "2024-XX-XX",
  ...
}
```

✅ **Success!** Clinic is now subscribed with a 14-day trial!

## Step 8: Create a Transcription Session

```bash
# Create an encounter (consultation session)
curl -X POST http://localhost:8000/v1/encounters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_ref": "PATIENT-001",
    "source": "room"
  }'
```

**Response:**
```json
{
  "id": 1,
  "clinic_id": 1,
  "doctor_id": 1,
  "patient_ref": "PATIENT-001",
  "source": "room",
  "status": "in_progress",
  "ws_url": "/v1/stream?encounter_id=1",
  "auth_token": "eyJ..."
}
```

## Step 9: Test Live Transcription (Frontend)

1. Open **http://localhost:3000/transcribe**
2. You'll see the live transcription interface
3. Click **"Start Recording"**
4. Grant microphone permissions
5. Speak into your microphone
6. You should see:
   - Status changing to "recording"
   - Live partial transcriptions appearing (currently simulated)
   - Confidence scores
7. Click **"Stop & Finalize"**
8. See:
   - Final transcript
   - SOAP notes generated
   - Download PDF button

**Note:** The WebSocket streaming currently shows simulated transcription. For real transcription with Whisper, audio processing happens on finalization.

## Step 10: Finalize and Generate SOAP Notes

```bash
# Finalize the encounter (generates SOAP notes)
curl -X POST http://localhost:8000/v1/encounters/1/finalize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "run_diarization": true,
    "run_ner": true,
    "generate_soap": true
  }'
```

**Response:**
```json
{
  "status": "completed",
  "encounter_id": 1,
  "transcript_id": 1,
  "entities_found": 5,
  "soap_generated": true
}
```

## Step 11: View Transcript with SOAP Notes

```bash
# Get the transcript
curl http://localhost:8000/v1/encounters/1/transcript \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "id": 1,
  "encounter_id": 1,
  "engine": "streaming_simulation",
  "text": "Final transcript from X audio chunks",
  "confidence_avg": 0.85,
  "soap_notes": {
    "S": "Subjective: Patient reports...",
    "O": "Objective: Examination shows...",
    "A": "Assessment: Likely diagnosis...",
    "P": "Plan: Prescribe medication..."
  },
  "entities": [
    {
      "type": "med",
      "value": "metformin",
      "confidence": 0.8
    }
  ]
}
```

## Step 12: Check Usage & Billing

```bash
# Check current usage
curl http://localhost:8000/v1/billing/usage \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "allowed": true,
  "status": "trialing",
  "plan_name": "solo",
  "hours_used": 0.02,
  "hours_limit": 100,
  "hours_remaining": 99.98,
  "overage_hours": 0,
  "overage_charge": 0,
  "trial_ends_at": "2024-XX-XX"
}
```

## Step 13: Export to PDF

```bash
# Export transcript as PDF
curl -X POST http://localhost:8000/v1/exports/pdf \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "encounter_id": 1,
    "template": "soap"
  }' \
  --output transcript.pdf

# Open the PDF
open transcript.pdf  # macOS
# or
xdg-open transcript.pdf  # Linux
```

## Step 14: View Audit Logs (Database)

```bash
# Connect to database
docker-compose exec postgres psql -U aiscribe -d aiscribe

# View audit logs
SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;

# View subscriptions
SELECT * FROM subscriptions;

# View usage records
SELECT * FROM usage_records;

# Exit
\q
```

## Quick Verification Checklist

✅ Services running:
- [ ] PostgreSQL (port 5432)
- [ ] Backend API (port 8000)
- [ ] Frontend (port 3000)

✅ Data created:
- [ ] Clinic created
- [ ] Sample users created
- [ ] Subscription plans created

✅ Features tested:
- [ ] User registration/login
- [ ] Subscription created
- [ ] Encounter created
- [ ] Transcript generated
- [ ] SOAP notes created
- [ ] PDF export works
- [ ] Usage tracked

## Common Issues & Solutions

### Issue: "Port already in use"

```bash
# Kill processes on ports
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5432 | xargs kill -9  # Postgres

# Or use different ports in docker-compose.yml
```

### Issue: "Database connection refused"

```bash
# Wait for Postgres to fully start
docker-compose logs postgres

# Look for: "database system is ready to accept connections"
```

### Issue: "Module not found"

```bash
# Rebuild containers
docker-compose down
docker-compose up --build
```

### Issue: "Alembic migrations fail"

```bash
# Reset database
docker-compose down -v  # WARNING: Deletes all data
docker-compose up -d postgres
sleep 5
docker-compose exec backend alembic upgrade head
```

### Issue: "Frontend shows blank page"

```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up --build frontend
```

## Next Steps - Real Transcription

To enable real Whisper transcription:

1. **Set Whisper model** in `.env`:
   ```
   WHISPER_MODEL=medium
   WHISPER_DEVICE=cpu
   ```

2. **Upload an audio file** via API:
   ```bash
   curl -X POST http://localhost:8000/v1/upload \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@consultation.mp3" \
     -F "encounter_id=1"
   ```

3. **Finalize** to run Whisper on the audio

## Next Steps - Stripe Integration

To enable real payment processing:

1. **Sign up for Stripe**: https://stripe.com
2. **Get API keys** from Stripe Dashboard
3. **Add to `.env`**:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   ```
4. **Restart backend**
5. Subscriptions will now actually charge cards!

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Just backend
docker-compose logs -f backend

# Just frontend
docker-compose logs -f frontend
```

### API Metrics

Visit: **http://localhost:8000/docs** to see all available endpoints

## Stopping the Application

```bash
# Stop services (keeps data)
docker-compose down

# Stop and delete all data
docker-compose down -v

# Stop just one service
docker-compose stop backend
```

## You're All Set! 🎉

You now have a fully functional medical AI transcription platform with:
- ✅ Real-time transcription framework
- ✅ User authentication
- ✅ Subscription management
- ✅ Usage tracking and billing
- ✅ SOAP note generation
- ✅ Medical entity extraction
- ✅ PDF export
- ✅ Audit logging
- ✅ Multi-tenant support

**Test workflow:**
1. Register → Login → Subscribe → Create Encounter → Record Audio → Finalize → Get SOAP Notes → Export PDF → Check Usage

**Production deployment:** See DEPLOYMENT.md for cloud deployment guide.

**Questions?** Check the full documentation in README.md and SPECIFICATION.md
