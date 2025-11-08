'use client'

import { useState } from 'react'
import { Check } from 'lucide-react'

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly')

  const plans = [
    {
      name: 'Solo Practitioner',
      price: { monthly: 149, annual: 1490 },
      hours: 100,
      users: 1,
      features: [
        'Real-time transcription',
        'Basic SOAP notes',
        'PDF export',
        '100 hours/month',
        'Email support',
      ],
      cta: 'Start Free Trial',
      popular: false,
    },
    {
      name: 'Small Clinic',
      price: { monthly: 599, annual: 5990 },
      hours: 500,
      users: 5,
      features: [
        'Everything in Solo, plus:',
        'Advanced SOAP notes',
        'Medical entity extraction',
        'Custom templates',
        '500 hours/month',
        'Up to 5 doctors',
        'Usage analytics',
      ],
      cta: 'Start Free Trial',
      popular: true,
    },
    {
      name: 'Medium Practice',
      price: { monthly: 1499, annual: 14990 },
      hours: 2000,
      users: 15,
      features: [
        'Everything in Small, plus:',
        'Speaker diarization',
        'API access',
        '2,000 hours/month',
        'Up to 15 doctors',
        'Priority support',
        'SSO integration',
      ],
      cta: 'Start Free Trial',
      popular: false,
    },
    {
      name: 'Enterprise',
      price: { monthly: 3999, annual: 39990 },
      hours: 10000,
      users: 999,
      features: [
        'Everything in Medium, plus:',
        'PMS/EMR integration',
        'Unlimited users',
        'Unlimited hours',
        'Dedicated support',
        'Custom integrations',
        'On-premise option',
      ],
      cta: 'Contact Sales',
      popular: false,
    },
  ]

  const getPrice = (plan: typeof plans[0]) => {
    return billingPeriod === 'monthly' ? plan.price.monthly : Math.round(plan.price.annual / 12)
  }

  const getSavings = (plan: typeof plans[0]) => {
    if (billingPeriod === 'monthly') return null
    const monthlyCost = plan.price.monthly * 12
    const savings = monthlyCost - plan.price.annual
    const savingsPercent = Math.round((savings / monthlyCost) * 100)
    return { amount: savings, percent: savingsPercent }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Pricing</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Choose the plan that fits your practice. All prices in AUD.
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                billingPeriod === 'monthly'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod('annual')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                billingPeriod === 'annual'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600'
              }`}
            >
              Annual
              <span className="ml-2 text-xs text-primary-600 font-semibold">
                Save ~17%
              </span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          {plans.map((plan) => {
            const savings = getSavings(plan)
            return (
              <div
                key={plan.name}
                className={`relative bg-white rounded-lg shadow-md p-8 ${
                  plan.popular ? 'ring-2 ring-primary-500' : ''
                }`}
              >
                {plan.popular && (
                  <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                    <span className="bg-primary-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    {plan.name}
                  </h3>
                  <div className="flex items-baseline mb-2">
                    <span className="text-4xl font-bold text-gray-900">
                      ${getPrice(plan)}
                    </span>
                    <span className="text-gray-600 ml-2">/month</span>
                  </div>
                  {billingPeriod === 'annual' && savings && (
                    <p className="text-sm text-green-600 font-medium">
                      Save ${savings.amount} annually
                    </p>
                  )}
                </div>

                <button
                  className={`w-full py-3 px-4 rounded-lg font-medium mb-6 transition-colors ${
                    plan.popular
                      ? 'bg-primary-600 text-white hover:bg-primary-700'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  {plan.cta}
                </button>

                <ul className="space-y-3">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </div>

        {/* Overage Pricing */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-12">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Overage Pricing
          </h3>
          <p className="text-gray-700">
            Need more than your plan includes? Additional hours are just{' '}
            <span className="font-bold">$2 AUD per hour</span>, billed monthly
            in arrears. No surprises.
          </p>
        </div>

        {/* Features Comparison */}
        <div className="bg-white rounded-lg shadow-md p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            All Plans Include
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              'Australian data residency',
              'End-to-end encryption',
              'HIPAA-equivalent security',
              'Audit logging',
              '14-day free trial',
              'No lock-in contracts',
              'Cancel anytime',
              'Data export',
              'Regular updates',
            ].map((feature) => (
              <div key={feature} className="flex items-start">
                <Check className="w-5 h-5 text-primary-600 mr-3 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-12">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Frequently Asked Questions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[
              {
                q: 'What counts as an hour?',
                a: 'One hour is 60 minutes of audio transcription time. A 15-minute consultation counts as 0.25 hours.',
              },
              {
                q: 'Is there a free trial?',
                a: 'Yes! All plans include a 14-day free trial with full access to features.',
              },
              {
                q: 'Can I change plans?',
                a: 'Absolutely. Upgrade or downgrade anytime. Changes take effect at the next billing period.',
              },
              {
                q: 'Where is my data stored?',
                a: 'All data is stored in Australia (Sydney or Melbourne) for compliance with Australian privacy laws.',
              },
              {
                q: 'Do you offer on-premise deployment?',
                a: 'Yes, on-premise deployment is available for Enterprise customers. Contact sales for pricing.',
              },
              {
                q: 'What payment methods do you accept?',
                a: 'We accept all major credit cards and can invoice Enterprise customers monthly.',
              },
            ].map((faq, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 mb-2">{faq.q}</h4>
                <p className="text-gray-600 text-sm">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-16 text-center bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-12 text-white">
          <h3 className="text-3xl font-bold mb-4">
            Ready to Transform Your Practice?
          </h3>
          <p className="text-xl mb-8 text-primary-100">
            Join hundreds of Australian clinics using AIscribe
          </p>
          <button className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors">
            Start Your Free Trial
          </button>
          <p className="mt-4 text-sm text-primary-100">
            No credit card required • 14-day free trial • Cancel anytime
          </p>
        </div>
      </main>
    </div>
  )
}
