'use client'

import { ReactNode } from 'react'
import { SubscriptionTier } from '@/lib/stripe'
import { hasFeatureAccess, getUpgradeMessage, FeatureAccess } from '@/lib/permissions'
import UpgradePrompt from './UpgradePrompt'

interface FeatureGateProps {
  feature: keyof FeatureAccess
  userTier: SubscriptionTier | null
  children: ReactNode
  fallback?: ReactNode
  showUpgradePrompt?: boolean
}

export default function FeatureGate({
  feature,
  userTier,
  children,
  fallback,
  showUpgradePrompt = true
}: FeatureGateProps) {
  const hasAccess = hasFeatureAccess(feature, userTier)

  if (hasAccess) {
    return <>{children}</>
  }

  if (fallback) {
    return <>{fallback}</>
  }

  if (showUpgradePrompt) {
    return (
      <UpgradePrompt
        title="Premium Feature"
        message={getUpgradeMessage(feature)}
        feature={feature}
        dismissible={false}
      />
    )
  }

  return null
}

// Wrapper component for disabled state
interface DisabledFeatureProps {
  feature: keyof FeatureAccess
  userTier: SubscriptionTier | null
  children: ReactNode
  className?: string
}

export function DisabledFeature({
  feature,
  userTier,
  children,
  className = ''
}: DisabledFeatureProps) {
  const hasAccess = hasFeatureAccess(feature, userTier)

  return (
    <div className={`${!hasAccess ? 'opacity-50 pointer-events-none' : ''} ${className}`}>
      {children}
      {!hasAccess && (
        <div className="absolute inset-0 bg-gray-50 bg-opacity-75 flex items-center justify-center rounded-lg">
          <div className="text-center">
            <div className="text-sm font-medium text-gray-600 mb-1">Premium Feature</div>
            <div className="text-xs text-gray-500">Upgrade to unlock</div>
          </div>
        </div>
      )}
    </div>
  )
}