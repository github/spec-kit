'use client'

import Link from 'next/link'
import { Crown, ArrowRight, X } from 'lucide-react'
import { useState } from 'react'

interface UpgradePromptProps {
  title: string
  message: string
  feature?: string
  onDismiss?: () => void
  dismissible?: boolean
}

export default function UpgradePrompt({ 
  title, 
  message, 
  feature,
  onDismiss,
  dismissible = true 
}: UpgradePromptProps) {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed) return null

  const handleDismiss = () => {
    setDismissed(true)
    onDismiss?.()
  }

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6 relative">
      {dismissible && (
        <button
          onClick={handleDismiss}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X className="w-4 h-4" />
        </button>
      )}
      
      <div className="flex items-start space-x-4">
        <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <Crown className="w-6 h-6 text-white" />
        </div>
        
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {title}
          </h3>
          <p className="text-gray-700 mb-4">
            {message}
          </p>
          
          <div className="flex items-center space-x-4">
            <Link
              href="/dashboard/subscription"
              className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-colors"
            >
              Upgrade Now
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
            
            <Link
              href="/dashboard/subscription"
              className="text-blue-600 hover:text-blue-700 font-medium text-sm"
            >
              View Plans
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}