'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Mic, FileAudio, Shield, Zap } from 'lucide-react'

export default function Home() {
  const router = useRouter()

  const features = [
    {
      icon: <Mic className="w-6 h-6" />,
      title: 'Real-time Transcription',
      description: 'Live audio streaming with instant captions and low latency',
    },
    {
      icon: <FileAudio className="w-6 h-6" />,
      title: 'Medical Accuracy',
      description: 'Dual-engine ASR with medical vocabulary and entity recognition',
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: 'Australian Compliance',
      description: 'Privacy Act 1988 compliant, AU data residency, full encryption',
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'SOAP Notes',
      description: 'Automated clinical documentation with one-click generation',
    },
  ]

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-500 rounded-lg p-2">
                <Mic className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900">AIscribe</h1>
            </div>
            <button
              onClick={() => router.push('/login')}
              className="px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              Sign In
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
            Medical AI Transcription
          </h2>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Secure, compliant, and accurate transcription for Australian medical clinics.
            Real-time streaming with automated SOAP note generation.
          </p>
          <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
            <div className="rounded-md shadow">
              <button
                onClick={() => router.push('/transcribe')}
                className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 md:py-4 md:text-lg md:px-10"
              >
                Start Transcribing
              </button>
            </div>
            <div className="mt-3 rounded-md shadow sm:mt-0 sm:ml-3">
              <button
                onClick={() => router.push('/demo')}
                className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-primary-600 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10"
              >
                View Demo
              </button>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="mt-20">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow"
              >
                <div className="flex items-center justify-center w-12 h-12 bg-primary-100 text-primary-600 rounded-lg mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 text-sm">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Compliance Banner */}
        <div className="mt-16 bg-gray-800 rounded-lg p-8 text-center">
          <h3 className="text-2xl font-bold text-white mb-4">
            Built for Australian Healthcare
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-gray-300">
            <div>
              <p className="font-semibold text-white">Data Residency</p>
              <p className="text-sm mt-1">All data stored in Australia</p>
            </div>
            <div>
              <p className="font-semibold text-white">Privacy Act 1988</p>
              <p className="text-sm mt-1">Fully compliant with APPs</p>
            </div>
            <div>
              <p className="font-semibold text-white">Encryption</p>
              <p className="text-sm mt-1">AES-256 at rest, TLS 1.3 in transit</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
