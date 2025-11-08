/**
 * API client for AIscribe backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export interface Encounter {
  id: number
  clinic_id: number
  doctor_id: number
  patient_ref?: string
  source: string
  status: string
  started_at: string
  ended_at?: string
  ws_url: string
  auth_token: string
}

export interface Transcript {
  id: number
  encounter_id: number
  engine: string
  text: string
  confidence_avg: number
  segments?: any[]
  soap_notes?: any
  entities?: any[]
  created_at: string
}

class APIClient {
  private token: string | null = null

  constructor() {
    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
  }

  private async request(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<any> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Authentication
  async login(email: string, password: string): Promise<{ access_token: string }> {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await fetch(`${API_URL}/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error('Login failed')
    }

    const data = await response.json()
    this.setToken(data.access_token)
    return data
  }

  async register(
    email: string,
    password: string,
    fullName: string,
    clinicId: number
  ): Promise<{ access_token: string }> {
    const data = await this.request('/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        clinic_id: clinicId,
      }),
    })
    this.setToken(data.access_token)
    return data
  }

  async getCurrentUser(): Promise<any> {
    return this.request('/v1/auth/me')
  }

  // Encounters
  async createEncounter(patientRef?: string, source: string = 'room'): Promise<Encounter> {
    return this.request('/v1/encounters', {
      method: 'POST',
      body: JSON.stringify({
        patient_ref: patientRef,
        source,
      }),
    })
  }

  async getEncounter(encounterId: number): Promise<Encounter> {
    return this.request(`/v1/encounters/${encounterId}`)
  }

  async finalizeEncounter(
    encounterId: number,
    options: {
      run_diarization?: boolean
      run_ner?: boolean
      generate_soap?: boolean
    } = {}
  ): Promise<any> {
    return this.request(`/v1/encounters/${encounterId}/finalize`, {
      method: 'POST',
      body: JSON.stringify({
        run_diarization: options.run_diarization ?? true,
        run_ner: options.run_ner ?? true,
        generate_soap: options.generate_soap ?? true,
      }),
    })
  }

  async getTranscript(encounterId: number): Promise<Transcript> {
    return this.request(`/v1/encounters/${encounterId}/transcript`)
  }

  // WebSocket connection
  connectWebSocket(wsUrl: string, token: string): WebSocket {
    const fullUrl = `${WS_URL}${wsUrl}&token=${token}`
    return new WebSocket(fullUrl)
  }

  // Exports
  async exportPDF(encounterId: number): Promise<Blob> {
    const response = await fetch(`${API_URL}/v1/exports/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify({
        encounter_id: encounterId,
        template: 'soap',
      }),
    })

    if (!response.ok) {
      throw new Error('Export failed')
    }

    return response.blob()
  }

  async exportText(encounterId: number): Promise<Blob> {
    const response = await fetch(`${API_URL}/v1/exports/text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify({
        encounter_id: encounterId,
      }),
    })

    if (!response.ok) {
      throw new Error('Export failed')
    }

    return response.blob()
  }
}

export const api = new APIClient()
