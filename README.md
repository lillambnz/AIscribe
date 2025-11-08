# AIscribe - Medical AI Transcription Platform

A secure, compliant AI transcription platform designed for Australian medical clinics, featuring dual-engine ASR, real-time streaming, and automated SOAP note generation.

## Features

- **Real-time Transcription**: Live audio streaming with WebRTC
- **Dual-Engine ASR**: Streaming model for low latency + Whisper for accuracy
- **Medical Vocabulary**: Custom medical terminology and entity recognition
- **Speaker Diarization**: Automatic doctor/patient identification
- **SOAP Note Generation**: Automated clinical documentation
- **Australian Compliance**: Privacy Act 1988 compliant, AU data residency
- **Secure & Audited**: Full encryption, audit logging, tenant isolation

## Architecture

### Backend (FastAPI)
- Real-time WebSocket streaming
- Dual ASR engine orchestration (streaming + Whisper)
- Medical NER and entity extraction
- SOAP note composition
- Audit logging and compliance

### Frontend (Next.js)
- WebRTC audio capture
- Real-time transcription display
- Confidence highlighting
- SOAP note editor
- Export and patient management

### Database (PostgreSQL)
- Multi-tenant with row-level security
- Encrypted PHI storage
- Configurable retention policies
- Audit trail

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **ASR**: faster-whisper (CTranslate2), Azure Speech SDK (optional)
- **NLP**: spaCy (medical models), pyannote.audio (diarization)
- **Frontend**: Next.js 14, TypeScript, TailwindCSS
- **Database**: PostgreSQL 15+
- **Storage**: S3-compatible (MinIO/GCS/Azure Blob)
- **Auth**: JWT + OAuth2/OIDC (Microsoft Entra ready)
- **Deployment**: Docker, Docker Compose, Kubernetes-ready

## Project Structure

```
AIscribe/
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Config, security, dependencies
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic (ASR, NER, SOAP)
│   │   └── schemas/       # Pydantic schemas
│   ├── alembic/           # Database migrations
│   └── requirements.txt
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/           # App router
│   │   ├── components/    # React components
│   │   └── lib/           # Utilities
│   └── package.json
├── docker/                # Docker configurations
├── docs/                  # Documentation
└── scripts/               # Deployment and utility scripts
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (recommended)

### Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repo-url>
   cd AIscribe
   ```

2. **Backend**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt

   # Setup database
   cp .env.example .env
   # Edit .env with your database credentials
   alembic upgrade head

   # Run development server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Frontend**:
   ```bash
   cd frontend
   npm install
   cp .env.local.example .env.local
   # Edit .env.local with API URL
   npm run dev
   ```

4. **Access**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:3000

### Docker Deployment

```bash
docker-compose up -d
```

## Configuration

### Environment Variables

#### Backend (.env)
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/aiscribe
SECRET_KEY=your-secret-key
AZURE_SPEECH_KEY=optional-for-streaming-asr
AZURE_SPEECH_REGION=australiaeast
STORAGE_BACKEND=local  # or s3, azure, gcs
STORAGE_PATH=/var/aiscribe/audio
ENCRYPTION_KEY=your-kms-key
AU_DATA_RESIDENCY=true
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_AUTH_PROVIDER=local  # or entra, oauth2
```

## Security & Compliance

- **Data Residency**: All data stored in Australia (configurable)
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Authentication**: JWT with optional SSO (Microsoft Entra)
- **Authorization**: Role-based access control (Doctor, Nurse, Admin)
- **Audit Logging**: Immutable audit trail for all operations
- **PHI Protection**: Automatic redaction options, configurable retention
- **Local Mode**: On-device inference option for sensitive consults

## API Documentation

Full API documentation available at `/docs` when running the backend.

### Key Endpoints

- `POST /v1/encounters` - Create new transcription session
- `WS /v1/stream` - WebSocket for real-time audio streaming
- `POST /v1/encounters/{id}/finalize` - Process and generate SOAP notes
- `GET /v1/encounters/{id}/transcript` - Retrieve transcript
- `POST /v1/exports/pdf` - Export to PDF

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Deployment

### Production Checklist

- [ ] Configure Australian cloud region (GCP Sydney or Azure Australia East)
- [ ] Set up production PostgreSQL with encryption
- [ ] Configure object storage (GCS/Azure Blob)
- [ ] Enable TLS certificates
- [ ] Set up SSO (Microsoft Entra)
- [ ] Configure KMS keys for tenant isolation
- [ ] Enable audit logging
- [ ] Set retention policies
- [ ] Configure backup strategy
- [ ] Review security settings
- [ ] Load test with clinic workflow

### Kubernetes Deployment

See `docs/kubernetes-deployment.md` for Kubernetes manifests and deployment guide.

## License

Proprietary - All rights reserved

## Support

For issues and questions, please contact the development team.
