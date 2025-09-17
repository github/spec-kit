'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { loadStripe } from '@stripe/stripe-js'
import { CheckCircle, Crown, Star, Zap, ExternalLink } from 'lucide-react'
import { SUBSCRIPTION_TIERS } from '@/lib/stripe'

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!)

interface UserSubscription {
  tier: 'basic' | 'pro' | 'enterprise' | null
  status: 'active' | 'canceled' | 'past_due' | 'incomplete' | null
  current_period_end?: string
}

export default function SubscriptionPage() {
  const { user } = useUser()
  const [loading, setLoading] = useState(false)
  const [subscription, setSubscription] = useState<UserSubscription>({ tier: null, status: null })

  useEffect(() => {
    // In a real app, fetch user subscription from your API
    // For now, we'll use mock data
    setSubscription({
      tier: 'basic',
      status: 'active',
      current_period_end: '2024-02-15T00:00:00Z'
    })
  }, [])

  const handleSubscribe = async (priceId: string) => {
    if (!user) return

    setLoading(true)
    
    try {
      const response = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ priceId }),
      })

      const { sessionId } = await response.json()
      const stripe = await stripePromise

      if (stripe) {
        const { error } = await stripe.redirectToCheckout({ sessionId })
        if (error) {
          console.error('Stripe redirect error:', error)
        }
      }
    } catch (error) {
      console.error('Error creating checkout session:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleManageSubscription = async () => {
    setLoading(true)
    
    try {
      const response = await fetch('/api/create-portal-session', {
        method: 'POST',
      })

      const { url } = await response.json()
      window.location.href = url
    } catch (error) {
      console.error('Error creating portal session:', error)
    } finally {
      setLoading(false)
    }
  }

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'BASIC':
        return <Star className="w-6 h-6" />
      case 'PRO':
        return <Crown className="w-6 h-6" />
      case 'ENTERPRISE':
        return <Zap className="w-6 h-6" />
      default:
        return <Star className="w-6 h-6" />
    }
  }

  const isCurrentTier = (tier: string) => {
    return subscription.tier === tier.toLowerCase()
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Choose Your Plan
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Unlock the full potential of your social media management with our flexible pricing plans.
        </p>
      </div>

      {/* Current Subscription Status */}
      {subscription.tier && subscription.status === 'active' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <div>
                <h3 className="text-lg font-semibold text-green-900">
                  Active Subscription - {subscription.tier.charAt(0).toUpperCase() + subscription.tier.slice(1)}
                </h3>
                <p className="text-green-700">
                  Your subscription renews on {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
            <button
              onClick={handleManageSubscription}
              disabled={loading}
              className="inline-flex items-center px-4 py-2 bg-white border border-green-300 text-green-700 rounded-lg hover:bg-green-50 disabled:opacity-50"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Manage Subscription
            </button>
          </div>
        </div>
      )}

      {/* Pricing Cards */}
      <div className="grid md:grid-cols-3 gap-8">
        {Object.entries(SUBSCRIPTION_TIERS).map(([key, tier]) => (
          <div
            key={key}
            className={`relative bg-white rounded-lg border-2 p-8 ${
              key === 'PRO' 
                ? 'border-blue-500 shadow-lg scale-105' 
                : isCurrentTier(key)
                ? 'border-green-500'
                : 'border-gray-200'
            }`}
          >
            {key === 'PRO' && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                Most Popular
              </div>
            )}

            {isCurrentTier(key) && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-green-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                Current Plan
              </div>
            )}

            <div className="text-center mb-8">
              <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${
                key === 'PRO' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
              }`}>
                {getTierIcon(key)}
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h3>
              <div className="text-4xl font-bold text-gray-900 mb-1">
                ${(tier.price / 100).toFixed(2)}
                <span className="text-lg font-normal text-gray-500">/month</span>
              </div>
            </div>

            <ul className="space-y-4 mb-8">
              {tier.features.map((feature, index) => (
                <li key={index} className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleSubscribe(tier.priceId)}
              disabled={loading || isCurrentTier(key)}
              className={`w-full py-3 px-4 rounded-lg font-semibold transition-colors ${
                isCurrentTier(key)
                  ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                  : key === 'PRO'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-900 text-white hover:bg-gray-800'
              } disabled:opacity-50`}
            >
              {loading ? 'Processing...' : isCurrentTier(key) ? 'Current Plan' : `Choose ${tier.name}`}
            </button>
          </div>
        ))}
      </div>

      {/* FAQ Section */}
      <div className="mt-16">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
          Frequently Asked Questions
        </h2>
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Can I change my plan anytime?
            </h3>
            <p className="text-gray-600">
              Yes, you can upgrade or downgrade your plan at any time. Changes will be prorated and reflected in your next billing cycle.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              What happens if I cancel?
            </h3>
            <p className="text-gray-600">
              You can cancel your subscription anytime. You'll continue to have access to your plan features until the end of your current billing period.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Do you offer refunds?
            </h3>
            <p className="text-gray-600">
              We offer a 30-day money-back guarantee for all new subscriptions. Contact our support team for assistance.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Is my data secure?
            </h3>
            <p className="text-gray-600">
              Absolutely. We use industry-standard encryption and security measures to protect your data and social media accounts.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}