# AI Transcription: How it Works + Clinic-Ready MVP Plan

## 1) How AI Transcription Works (Clinician Context)

- **Audio → Features**: mic/telephony is chunked (20–40 ms); convert to log-mel spectrograms.
- **ASR Models**:
  - Streaming models (RNN-T/Conformer/Transducer) for low-latency partials.
  - Batch models (e.g., Whisper) for higher accuracy at higher latency.
  - Medical adaptation via domain tuning, custom vocab (e.g., "metformin", "S1 radiculopathy"), biasing prompts ("This is a GP consult").
- **Post-processing**: punctuation, casing, numbers, speaker diarization (doctor vs patient), medical entity labeling (meds, dose, allergies), optional PHI redaction if calling external APIs.
- **Confidence & correction**: token confidences highlight uncertain phrases; second-engine fallback for low confidence; re-score with a small medical language model.
- **Packaging to clinical artifacts**: structure as SOAP notes, ICD hints, follow-ups; export to PMS/EMR or as drafts for sign-off.

## 2) Non-Negotiables (Compliance & Safety)

- **Data residency**: host in Australia (GCP australia-southeast1 or Azure Australia East).
- **Privacy**: Australian Privacy Act 1988 (APPs), OAIC guidance. Treat as health information.
- **Encryption**: TLS 1.2+ in transit; AES-256 at rest; per-tenant KMS keys.
- **Access**: SSO (Microsoft Entra) + RBAC (Doctor, Nurse, Admin).
- **Audit**: immutable audit_log for every access/export/delete.
- **Retention**: clinic-configurable; short retention for audio (30–90 days); transcripts per policy.
- **Local-only toggle**: on-device inference mode for sensitive consults.

## 3) MVP Scope

- **Platforms**: Web app (Chromium), optional iOS/Android companion.
- **Inputs**: live room mic (WebRTC), phone consults (SIP trunk → media proxy), file upload (wav/mp3/m4a).
- **Engines (dual-path)**:
  - Primary: streaming medical ASR (low latency).
  - Fallback: Whisper (faster-whisper/CT2) for robustness.
- **Features**: real-time captions, 2-speaker labels, medical vocab injection, low-confidence highlights, 1-click SOAP draft, PDF export, secure email; PMS/EMR integration deferred to Phase 2.

## 4) Reference Architecture

```
[Mic/WebRTC/Telephony] → [Edge Gateway (STUN/TURN, WebSocket/gRPC, per-tenant auth)]
 → Engine A: Streaming ASR (medical)
 → Engine B: Whisper fallback (batch or full fallback)
 → Post-Processor (punctuation, diarization, medical NER, confidence stitching)
 → Composer (SOAP/letters/templates)
 → API + Storage (KMS, audit, retention)
 → Frontend (real-time, corrections, sign-off, export).
```

**Why dual engines?** Reduces failure modes: streaming holds latency and stability; Whisper rescues meds/names and accents in batch re-score.

## 5) Stack Options

- **Cloud**: GCP Sydney (Cloud Run/GKE Autopilot) or Azure Australia East.
- **Streaming ASR**: Azure Speech (healthcare bias) or Amazon Transcribe Medical (check residency); self-hosted NVIDIA Riva/Vosk if GPU available.
- **Fallback ASR**: faster-whisper (CTranslate2), medium/large-v2; int8/int4 on CPU or FP16 on T4/L4 GPU.
- **Diarization**: pyannote.audio (2-speaker fast pipeline).
- **Medical NER/Structuring**: lightweight rules + small domain LLM offline, or hosted health NLP with strict data path.
- **Backend**: FastAPI (Python) or NestJS (Node).
- **DB**: Postgres (Cloud SQL/AlloyDB) with pgcrypto for PHI; GCS/Azure Blob for audio.
- **Auth**: Entra ID OIDC, short-lived JWT, PKCE.
- **Frontend**: Next.js + WebRTC; optional Electron desktop helper.

## 6) Minimum Data Model

```sql
- clinics(id, name, data_residency, retention_days, kms_key_id)
- users(id, clinic_id, role, email, sso_sub, mfa_enabled)
- encounters(id, clinic_id, patient_ref, started_at, doctor_id, source {room|phone|upload})
- audio_blobs(id, encounter_id, uri, duration_s, deleted_at)
- transcripts(id, encounter_id, engine, text, confidence_avg, version, created_at)
- entities(id, transcript_id, type {med,dose,allergy}, value, start, end)
- audit_log(id, actor_id, action, resource_type, resource_id, ts, ip_hash)
```

## 7) API Sketches

```
POST /v1/encounters → { encounter_id, ws_url, auth_token }
WS  /v1/stream?encounter_id=… (Bearer)
  client→server: PCM/opus frames (20ms)
  server→client: { partial_text, stable_text, confidences[], speaker, t }
POST /v1/encounters/{id}/finalize → batch re-score, diarization, NER, SOAP
GET  /v1/encounters/{id}/transcript → { text, soap, entities[], confidence_avg }
POST /v1/exports/pdf { encounter_id, template }
DELETE /v1/audio/{id} → hard delete (policy-gated), audited.
```

## 8) Accuracy & Latency Tactics

- Prompt biasing/context hints (GP consult, common terms).
- Custom vocabulary (drug names, local hospitals, clinician surnames).
- Noise control: VAD, RNNoise; recommend headset profiles for telephony.
- Stability rules: suppress partials <200 ms; stabilize when 2–3 tokens agree.
- Confidence-driven UX: underline <0.85 confidence; TAB to cycle fixes.
- Per-clinic adaptation: rolling token stats & accepted corrections (no raw audio).

## 9) Security Model

- **Zero-trust ingress**: WAF; mTLS edge ↔ engines; Secret Manager only.
- **Egress control**: if any US API is used, perform PHI redaction and tag audit with "data-leaves-AU".
- **Tenant isolation**: Postgres RLS, per-tenant KMS keys, bucket segmentation.
- **Hard toggles**: Local-only, No-audio-retention, No-cloud-NER (visible in UI).

## 10) Clinic Workflow

1. New consult → pick patient → Start.
2. Live captions with low-confidence chips.
3. Stop & Finalize → batch clean-up (fallback, diarization, NER).
4. Draft SOAP appears; doctor edits 15–60s → Sign.
5. Export/Attach PDF; purge audio per policy.

## 11) QA & Reliability

- Dual-engine consensus: if A vs B disagree on medications, show "verify" chip.
- Golden set: de-identified clinic clips for regression tests each deploy.
- Metrics: WER overall & meds, avg confidence, time-to-first-token, crash-free sessions.
- Offline mode: ship mobile with on-device small/medium Whisper; sync when online.
- DR: rolling backups; incident response runbooks; breach notification workflow.

## 12) Phase 2 (Post-MVP)

- PMS/EMR connectors: Best Practice, Genie/Surgical Partners, Helix, Zedmed, Medirecords, FHIR/HL7 bridge.
- Template library: specialist letters, WorkCover forms, pathology referrals.
- Hardware kits: validated USB speaker-mic + laptop presets.
- Multilingual capture: Urdu/Hindi/Pashto with English output.

## 13) Quick Start Checklist

- Pick cloud & AU region.
- Deploy Edge Gateway (WebRTC, JWT).
- Stand up Streaming ASR + faster-whisper fallback behind gRPC.
- Implement /encounters, /stream, /finalize.
- Add post-processing (punctuation, diarization, med NER).
- Build real-time UI with confidence highlights & SOAP preview.
- Wire retention jobs + "delete audio now" button.
- Add SSO (Entra) and audit logging.
- Pilot with 2–3 doctors; collect correction telemetry only.
- Lock templates; publish v1 SOP.
