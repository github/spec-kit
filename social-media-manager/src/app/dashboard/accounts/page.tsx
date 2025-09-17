'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { 
  Facebook, 
  Twitter, 
  Instagram, 
  Linkedin, 
  Plus, 
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
  ExternalLink,
  Crown
} from 'lucide-react'
import { useSubscription } from '@/hooks/useSubscription'
import UpgradePrompt from '@/components/UpgradePrompt'

interface SocialAccount {
  id: string
  platform: string
  username: string
  avatar_url?: string
  status: 'active' | 'inactive' | 'error'
  created_at: string
}

const platformConfig = {
  facebook: {
    name: 'Facebook',
    icon: Facebook,
    color: 'bg-blue-600',
    textColor: 'text-blue-600'
  },
  twitter: {
    name: 'Twitter',
    icon: Twitter,
    color: 'bg-sky-500',
    textColor: 'text-sky-500'
  },
  instagram: {
    name: 'Instagram',
    icon: Instagram,
    color: 'bg-pink-600',
    textColor: 'text-pink-600'
  },
  linkedin: {
    name: 'LinkedIn',
    icon: Linkedin,
    color: 'bg-blue-700',
    textColor: 'text-blue-700'
  }
}

export default function AccountsPage() {
  const { user } = useUser()
  const { subscription, usage, canCreateAccount, getAccountsRemaining } = useSubscription()
  const [accounts, setAccounts] = useState<SocialAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState<string | null>(null)
  const [showLimitWarning, setShowLimitWarning] = useState(false)

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await fetch('/api/social-accounts')
      if (response.ok) {
        const data = await response.json()
        setAccounts(data)
      }
    } catch (error) {
      console.error('Error fetching accounts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleConnectAccount = async (platform: string) => {
    if (!user) return
    
    if (!canCreateAccount()) {
      setShowLimitWarning(true)
      return
    }
    
    setConnecting(platform)
    
    try {
      // In a real implementation, this would redirect to Ayrshare OAuth flow
      // For demo purposes, we'll simulate adding an account
      const mockAccount = {
        platform,
        platform_user_id: `${platform}_${Date.now()}`,
        username: `@user_${platform}`,
        avatar_url: `https://via.placeholder.com/40?text=${platform[0].toUpperCase()}`,
        access_token: 'mock_token',
        refresh_token: 'mock_refresh',
        expires_at: new Date(Date.now() + 3600000).toISOString() // 1 hour from now
      }

      const response = await fetch('/api/social-accounts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mockAccount),
      })

      if (response.ok) {
        fetchAccounts() // Refresh the list
      } else {
        console.error('Failed to connect account')
      }
    } catch (error) {
      console.error('Error connecting account:', error)
    } finally {
      setConnecting(null)
    }
  }

  const handleDisconnectAccount = async (accountId: string) => {
    if (!confirm('Are you sure you want to disconnect this account?')) {
      return
    }

    try {
      const response = await fetch(`/api/social-accounts?id=${accountId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        setAccounts(accounts.filter(account => account.id !== accountId))
      } else {
        console.error('Failed to disconnect account')
      }
    } catch (error) {
      console.error('Error disconnecting account:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Connected'
      case 'error':
        return 'Error'
      default:
        return 'Inactive'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Connected Accounts
            </h1>
            <p className="text-gray-600">
              Connect your social media accounts to start scheduling and managing your posts.
            </p>
          </div>
          
          {subscription.tier && (
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center min-w-[200px]">
              <div className="text-2xl font-bold text-gray-900">
                {accounts.length} / {subscription.limits.accounts === -1 ? '∞' : subscription.limits.accounts}
              </div>
              <div className="text-sm text-gray-500">
                Accounts Connected
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {getAccountsRemaining()} remaining
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Limit Warning */}
      {showLimitWarning && (
        <div className="mb-8">
          <UpgradePrompt
            title="Account Limit Reached"
            message={`You've reached your limit of ${subscription.limits.accounts} connected accounts. Upgrade your plan to connect more social media accounts.`}
            onDismiss={() => setShowLimitWarning(false)}
          />
        </div>
      )}

      {/* Connected Accounts */}
      {accounts.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Your Connected Accounts</h2>
          </div>
          <div className="p-6">
            <div className="grid gap-4">
              {accounts.map((account) => {
                const config = platformConfig[account.platform as keyof typeof platformConfig]
                const Icon = config?.icon || Facebook

                return (
                  <div
                    key={account.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-4">
                      <div className={`w-10 h-10 ${config?.color} rounded-lg flex items-center justify-center`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {config?.name || account.platform}
                        </h3>
                        <p className="text-sm text-gray-600">{account.username}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(account.status)}
                        <span className="text-sm text-gray-600">
                          {getStatusText(account.status)}
                        </span>
                      </div>
                      <button
                        onClick={() => handleDisconnectAccount(account.id)}
                        className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                        title="Disconnect account"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Available Platforms */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Connect New Account</h2>
          <p className="text-sm text-gray-600 mt-1">
            Choose a platform to connect your account
          </p>
        </div>
        <div className="p-6">
          <div className="grid md:grid-cols-2 gap-4">
            {Object.entries(platformConfig).map(([platform, config]) => {
              const isConnected = accounts.some(account => account.platform === platform)
              const isConnecting = connecting === platform
              const Icon = config.icon

              return (
                <button
                  key={platform}
                  onClick={() => !isConnected && handleConnectAccount(platform)}
                  disabled={isConnected || isConnecting || (!canCreateAccount() && !isConnected)}
                  className={`flex items-center justify-between p-4 border-2 rounded-lg transition-all ${
                    isConnected
                      ? 'border-green-200 bg-green-50 cursor-not-allowed'
                      : !canCreateAccount()
                      ? 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${config.color} rounded-lg flex items-center justify-center`}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-gray-900">{config.name}</h3>
                      <p className="text-sm text-gray-600">
                        {isConnected ? 'Connected' : 'Connect your account'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {isConnecting ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600"></div>
                    ) : isConnected ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <Plus className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <ExternalLink className="w-3 h-3 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-blue-900 mb-2">Need Help?</h3>
            <p className="text-blue-800 text-sm mb-3">
              Having trouble connecting your accounts? Here are some common solutions:
            </p>
            <ul className="text-blue-800 text-sm space-y-1">
              <li>• Make sure you have admin access to the social media account</li>
              <li>• Check that your account isn't already connected to another service</li>
              <li>• Try clearing your browser cache and cookies</li>
              <li>• Contact support if you continue to experience issues</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}