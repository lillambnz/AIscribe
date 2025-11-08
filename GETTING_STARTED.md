# Getting Started with AIscribe

This guide will help you set up and run AIscribe for development or production deployment.

## Prerequisites

- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **Python** 3.11+ (for local development)
- **Node.js** 18+ (for local development)
- **PostgreSQL** 15+ (if not using Docker)

## Quick Start with Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AIscribe
   ```

2. **Run the setup script**:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

3. **Start all services**:
   ```bash
   docker-compose up
   ```

4. **Create sample data** (optional):
   ```bash
   docker-compose run --rm backend python ../scripts/create-sample-data.py
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - API: http://localhost:8000

## Manual Setup (Without Docker)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL database**:
   ```bash
   # Create database
   createdb aiscribe

   # Run migrations
   alembic upgrade head
   ```

6. **Run the development server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with API URL
   ```

4. **Run the development server**:
   ```bash
   npm run dev
   ```

## First Steps

### 1. Create a User Account

Using the sample data script:
```bash
docker-compose run --rm backend python ../scripts/create-sample-data.py
```

Or register via API:
```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "yourpassword",
    "full_name": "Dr. Example",
    "clinic_id": 1
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=doctor@example.com&password=yourpassword"
```

Save the returned `access_token` for API requests.

### 3. Create Your First Encounter

```bash
curl -X POST http://localhost:8000/v1/encounters \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_ref": "PATIENT-001",
    "source": "room"
  }'
```

### 4. Use the Frontend

1. Open http://localhost:3000
2. Navigate to the transcription page
3. Click "Start Recording" to begin a live transcription session
4. Grant microphone permissions when prompted
5. Speak into your microphone
6. Click "Stop & Finalize" to generate SOAP notes
7. Export as PDF or text

## Development Workflow

### Backend Development

- **Run tests**:
  ```bash
  cd backend
  pytest
  ```

- **Create database migration**:
  ```bash
  cd backend
  alembic revision --autogenerate -m "description of changes"
  alembic upgrade head
  ```

- **Format code**:
  ```bash
  black app/
  ```

### Frontend Development

- **Run linter**:
  ```bash
  cd frontend
  npm run lint
  ```

- **Build for production**:
  ```bash
  npm run build
  npm start
  ```

## Troubleshooting

### Database Connection Issues

If you see database connection errors:

1. Ensure PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. Check database credentials in `.env`

3. Reset database:
   ```bash
   docker-compose down -v
   docker-compose up -d postgres
   ./scripts/setup.sh
   ```

### Whisper Model Issues

If Whisper fails to load:

1. Check available disk space (models can be 1-3 GB)
2. Verify `WHISPER_MODEL` setting in `.env`
3. For CPU-only environments, use `WHISPER_COMPUTE_TYPE=int8`

### WebSocket Connection Issues

If WebSocket connections fail:

1. Check CORS settings in backend `.env`
2. Ensure `WS_URL` in frontend matches backend host
3. Check browser console for errors
4. Verify authentication token is valid

### Audio Capture Issues

If microphone access fails:

1. Ensure HTTPS is enabled (required for microphone access in production)
2. Grant microphone permissions in browser
3. Check browser compatibility (Chrome/Edge recommended)
4. Test with a different microphone/device

## Configuration

### Audio Retention Policy

Edit `backend/.env`:
```
AUDIO_RETENTION_DAYS=90
TRANSCRIPT_RETENTION_DAYS=2555  # 7 years
```

### ASR Engine Selection

For Whisper-only (no streaming):
```
WHISPER_MODEL=medium  # tiny, base, small, medium, large-v2
WHISPER_DEVICE=cpu    # or cuda for GPU
WHISPER_COMPUTE_TYPE=int8  # int8, float16
```

For Azure Speech SDK (streaming):
```
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=australiaeast
```

### Data Residency

Ensure all services are in Australia:
```
AU_DATA_RESIDENCY=true
# Deploy to: GCP australia-southeast1 or Azure Australia East
```

## Next Steps

- Review [SPECIFICATION.md](SPECIFICATION.md) for detailed architecture
- Read [README.md](README.md) for full feature list
- Check [API documentation](http://localhost:8000/docs) for API reference
- Configure SSO with Microsoft Entra (see backend configuration)
- Set up production deployment with Kubernetes

## Support

For issues and questions:
- Check existing issues on GitHub
- Review the specification document
- Consult the API documentation at `/docs`
