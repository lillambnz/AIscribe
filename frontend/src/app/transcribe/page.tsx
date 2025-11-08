'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Mic, StopCircle, FileText, Download, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

export default function TranscribePage() {
  const router = useRouter()
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [partialText, setPartialText] = useState('')
  const [confidence, setConfidence] = useState(0)
  const [encounterId, setEncounterId] = useState<number | null>(null)
  const [soapNotes, setSoapNotes] = useState<any>(null)
  const [status, setStatus] = useState<string>('ready')

  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)

  const startRecording = async () => {
    try {
      setStatus('starting')

      // Create encounter
      const encounter = await api.createEncounter(undefined, 'room')
      setEncounterId(encounter.id)

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Set up WebSocket
      const ws = api.connectWebSocket(encounter.ws_url, encounter.auth_token)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        setStatus('connected')
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)

        if (data.type === 'ready') {
          setStatus('ready to record')
        } else if (data.type === 'partial') {
          setPartialText(data.text)
          setConfidence(data.confidence || 0)
        } else if (data.type === 'stable') {
          setTranscript((prev) => prev + ' ' + data.text)
          setPartialText('')
        } else if (data.type === 'final') {
          setTranscript((prev) => prev + ' ' + data.text)
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.message)
          setStatus('error: ' + data.message)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setStatus('WebSocket error')
      }

      ws.onclose = () => {
        console.log('WebSocket closed')
        setStatus('disconnected')
      }

      // Set up MediaRecorder to send audio chunks
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
      })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
          // Send audio chunk to WebSocket
          event.data.arrayBuffer().then((buffer) => {
            ws.send(buffer)
          })
        }
      }

      // Start recording (send chunks every 100ms)
      mediaRecorder.start(100)
      setIsRecording(true)
      setStatus('recording')
    } catch (error) {
      console.error('Error starting recording:', error)
      setStatus('error: ' + (error as Error).message)
    }
  }

  const stopRecording = async () => {
    try {
      setStatus('stopping')

      // Stop media recorder
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      }

      // Send stop signal to WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'control', action: 'stop' }))
      }

      setIsRecording(false)
      setStatus('processing')

      // Finalize encounter
      if (encounterId) {
        const result = await api.finalizeEncounter(encounterId)
        console.log('Finalization result:', result)

        // Get transcript with SOAP notes
        const transcriptData = await api.getTranscript(encounterId)
        setTranscript(transcriptData.text)
        setSoapNotes(transcriptData.soap_notes)
        setConfidence(transcriptData.confidence_avg)
        setStatus('completed')
      }

      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    } catch (error) {
      console.error('Error stopping recording:', error)
      setStatus('error: ' + (error as Error).message)
    }
  }

  const downloadPDF = async () => {
    if (!encounterId) return

    try {
      const blob = await api.exportPDF(encounterId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `transcript_${encounterId}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading PDF:', error)
    }
  }

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      }
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Live Transcription</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Status Bar */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${
                isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-300'
              }`} />
              <span className="text-sm font-medium text-gray-700">
                Status: {status}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              {!isRecording ? (
                <button
                  onClick={startRecording}
                  className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  <Mic className="w-5 h-5 mr-2" />
                  Start Recording
                </button>
              ) : (
                <button
                  onClick={stopRecording}
                  className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  <StopCircle className="w-5 h-5 mr-2" />
                  Stop & Finalize
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Live Transcript */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Live Transcript
            </h2>
            <div className="h-96 overflow-y-auto border border-gray-200 rounded p-4 bg-gray-50">
              <p className="text-gray-700 whitespace-pre-wrap">
                {transcript}
                {partialText && (
                  <span className="text-gray-400 italic"> {partialText}</span>
                )}
              </p>
              {confidence > 0 && (
                <div className="mt-4 text-sm text-gray-500">
                  Confidence: {(confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>
          </div>

          {/* SOAP Notes */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                SOAP Notes
              </h2>
              {encounterId && status === 'completed' && (
                <button
                  onClick={downloadPDF}
                  className="flex items-center px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  <Download className="w-4 h-4 mr-1" />
                  PDF
                </button>
              )}
            </div>
            <div className="h-96 overflow-y-auto border border-gray-200 rounded p-4 bg-gray-50">
              {soapNotes ? (
                <div className="space-y-4">
                  {soapNotes.S && (
                    <div>
                      <h3 className="font-semibold text-gray-800">Subjective:</h3>
                      <p className="text-gray-600 text-sm mt-1 whitespace-pre-wrap">
                        {soapNotes.S}
                      </p>
                    </div>
                  )}
                  {soapNotes.O && (
                    <div>
                      <h3 className="font-semibold text-gray-800">Objective:</h3>
                      <p className="text-gray-600 text-sm mt-1 whitespace-pre-wrap">
                        {soapNotes.O}
                      </p>
                    </div>
                  )}
                  {soapNotes.A && (
                    <div>
                      <h3 className="font-semibold text-gray-800">Assessment:</h3>
                      <p className="text-gray-600 text-sm mt-1 whitespace-pre-wrap">
                        {soapNotes.A}
                      </p>
                    </div>
                  )}
                  {soapNotes.P && (
                    <div>
                      <h3 className="font-semibold text-gray-800">Plan:</h3>
                      <p className="text-gray-600 text-sm mt-1 whitespace-pre-wrap">
                        {soapNotes.P}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <div className="text-center">
                    <FileText className="w-12 h-12 mx-auto mb-2" />
                    <p>SOAP notes will appear after finalization</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Info Banner */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 mr-3" />
            <div className="text-sm text-blue-800">
              <p className="font-medium">Privacy & Security</p>
              <p className="mt-1">
                This is a secure medical transcription session. All data is encrypted and stored in Australia.
                Audio will be automatically deleted after {90} days per clinic policy.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
