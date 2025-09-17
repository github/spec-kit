'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { SubscriptionTier } from '@/lib/stripe'
import { getUserLimits, getFeatureAccess, UserLimits, FeatureAccess } from '@/lib/permissions'

interface SubscriptionData {
  tier: SubscriptionTier | null
  status: 'active' | 'canceled' | 'past_due' | 'incomplete' | null
  current_period_end?: string
  limits: UserLimits
  features: FeatureAccess
}

interface UsageData {
  accountsConnected: number
  postsThisMonth: number
  scheduledPosts: number
}

export function useSubscription() {
  const { user, isLoaded } = useUser()
  const [subscription, setSubscription] = useState<SubscriptionData>({
    tier: null,
    status: null,
    limits: getUserLimits(null),
    features: getFeatureAccess(null)
  })
  const [usage, setUsage] = useState<UsageData>({
    accountsConnected: 0,
    postsThisMonth: 0,
    scheduledPosts: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isLoaded && user) {
      fetchSubscriptionData()
      fetchUsageData()
    }
  }, [isLoaded, user])

  const fetchSubscriptionData = async () => {
    try {
      const response = await fetch('/api/user')
      if (response.ok) {
        const userData = await response.json()
        const tier = userData.subscription_tier as SubscriptionTier | null
        
        setSubscription({
          tier,
          status: userData.subscription_status,
          current_period_end: userData.subscriptions?.[0]?.current_period_end,
          limits: getUserLimits(tier),
          features: getFeatureAccess(tier)
        })
      }
    } catch (error) {
      console.error('Error fetching subscription:', error)
    }
  }

  const fetchUsageData = async () => {
    try {
      // Fetch accounts
      const accountsResponse = await fetch('/api/social-accounts')
      const accounts = accountsResponse.ok ? await accountsResponse.json() : []

      // Fetch posts for current month
      const now = new Date()
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
      const postsResponse = await fetch('/api/posts')
      const posts = postsResponse.ok ? await postsResponse.json() : []
      
      const postsThisMonth = posts.filter((post: any) => 
        new Date(post.created_at) >= startOfMonth
      ).length

      const scheduledPosts = posts.filter((post: any) => 
        post.status === 'scheduled'
      ).length

      setUsage({
        accountsConnected: accounts.length,
        postsThisMonth,
        scheduledPosts
      })
    } catch (error) {
      console.error('Error fetching usage data:', error)
    } finally {
      setLoading(false)
    }
  }

  const canCreateAccount = () => {
    return subscription.limits.accounts === -1 || 
           usage.accountsConnected < subscription.limits.accounts
  }

  const canCreatePost = () => {
    return subscription.limits.postsPerMonth === -1 || 
           usage.postsThisMonth < subscription.limits.postsPerMonth
  }

  const canSchedulePost = () => {
    return subscription.limits.scheduledPosts === -1 || 
           usage.scheduledPosts < subscription.limits.scheduledPosts
  }

  const hasFeature = (feature: keyof FeatureAccess) => {
    return subscription.features[feature]
  }

  const getAccountsRemaining = () => {
    if (subscription.limits.accounts === -1) return 'Unlimited'
    return Math.max(0, subscription.limits.accounts - usage.accountsConnected)
  }

  const getPostsRemaining = () => {
    if (subscription.limits.postsPerMonth === -1) return 'Unlimited'
    return Math.max(0, subscription.limits.postsPerMonth - usage.postsThisMonth)
  }

  const getScheduledPostsRemaining = () => {
    if (subscription.limits.scheduledPosts === -1) return 'Unlimited'
    return Math.max(0, subscription.limits.scheduledPosts - usage.scheduledPosts)
  }

  const refresh = async () => {
    setLoading(true)
    await Promise.all([fetchSubscriptionData(), fetchUsageData()])
  }

  return {
    subscription,
    usage,
    loading,
    canCreateAccount,
    canCreatePost,
    canSchedulePost,
    hasFeature,
    getAccountsRemaining,
    getPostsRemaining,
    getScheduledPostsRemaining,
    refresh
  }
}