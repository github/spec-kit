'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Calendar, 
  Image as ImageIcon, 
  Facebook, 
  Twitter, 
  Instagram, 
  Linkedin,
  X,
  Save,
  Send,
  Crown
} from 'lucide-react'
import { useSubscription } from '@/hooks/useSubscription'
import UpgradePrompt from '@/components/UpgradePrompt'
import FeatureGate from '@/components/FeatureGate'

interface SocialAccount {
  id: string
  platform: string
  username: string
  status: 'active' | 'inactive' | 'error'
}

const platformConfig = {
  facebook: { name: 'Facebook', icon: Facebook, color: 'text-blue-600' },
  twitter: { name: 'Twitter', icon: Twitter, color: 'text-sky-500' },
  instagram: { name: 'Instagram', icon: Instagram, color: 'text-pink-600' },
  linkedin: { name: 'LinkedIn', icon: Linkedin, color: 'text-blue-700' },
}

export default function NewPostPage() {
  const router = useRouter()
  const { 
    subscription, 
    usage, 
    canCreatePost, 
    canSchedulePost, 
    getPostsRemaining,
    getScheduledPostsRemaining 
  } = useSubscription()
  const [accounts, setAccounts] = useState<SocialAccount[]>([])
  const [loading, setLoading] = useState(false)
  const [showPostLimitWarning, setShowPostLimitWarning] = useState(false)
  const [showScheduleLimitWarning, setShowScheduleLimitWarning] = useState(false)
  const [formData, setFormData] = useState({
    content: '',
    platforms: [] as string[],
    scheduled_at: '',
    media_urls: [] as string[],
  })

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await fetch('/api/social-accounts')
      if (response.ok) {
        const data = await response.json()
        setAccounts(data.filter((account: SocialAccount) => account.status === 'active'))
      }
    } catch (error) {
      console.error('Error fetching accounts:', error)
    }
  }

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, content: e.target.value }))
  }

  const handlePlatformToggle = (platform: string) => {
    setFormData(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }))
  }

  const handleScheduleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, scheduled_at: e.target.value }))
  }

  const handleSubmit = async (isDraft = false) => {
    if (!formData.content.trim()) {
      alert('Please enter post content')
      return
    }

    if (formData.platforms.length === 0) {
      alert('Please select at least one platform')
      return
    }

    // Check limits
    if (!canCreatePost()) {
      setShowPostLimitWarning(true)
      return
    }

    if (formData.scheduled_at && !canSchedulePost()) {
      setShowScheduleLimitWarning(true)
      return
    }

    setLoading(true)

    try {
      const postData = {
        ...formData,
        scheduled_at: formData.scheduled_at || null,
      }

      const response = await fetch('/api/posts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(postData),
      })

      if (response.ok) {
        router.push('/dashboard/posts')
      } else {
        console.error('Failed to create post')
        alert('Failed to create post. Please try again.')
      }
    } catch (error) {
      console.error('Error creating post:', error)
      alert('An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getCharacterCount = () => {
    return formData.content.length
  }

  const getCharacterLimit = () => {
    if (formData.platforms.includes('twitter')) return 280
    if (formData.platforms.includes('instagram')) return 2200
    return 63206 // Facebook/LinkedIn limit
  }

  const isOverLimit = () => {
    return getCharacterCount() > getCharacterLimit()
  }

  // Get minimum datetime (current time + 5 minutes)
  const getMinDateTime = () => {
    const now = new Date()
    now.setMinutes(now.getMinutes() + 5)
    return now.toISOString().slice(0, 16)
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Create New Post</h1>
            <p className="text-gray-600">
              Create and schedule your social media post across multiple platforms.
            </p>
          </div>
          
          {subscription.tier && (
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-lg border border-gray-200 p-3 text-center">
                <div className="text-lg font-bold text-gray-900">
                  {usage.postsThisMonth} / {subscription.limits.postsPerMonth === -1 ? '∞' : subscription.limits.postsPerMonth}
                </div>
                <div className="text-xs text-gray-500">Posts this month</div>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-3 text-center">
                <div className="text-lg font-bold text-gray-900">
                  {usage.scheduledPosts} / {subscription.limits.scheduledPosts === -1 ? '∞' : subscription.limits.scheduledPosts}
                </div>
                <div className="text-xs text-gray-500">Scheduled posts</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Limit Warnings */}
      {showPostLimitWarning && (
        <div className="mb-8">
          <UpgradePrompt
            title="Monthly Post Limit Reached"
            message={`You've reached your limit of ${subscription.limits.postsPerMonth} posts this month. Upgrade your plan to create more posts.`}
            onDismiss={() => setShowPostLimitWarning(false)}
          />
        </div>
      )}

      {showScheduleLimitWarning && (
        <div className="mb-8">
          <UpgradePrompt
            title="Scheduled Post Limit Reached"
            message={`You've reached your limit of ${subscription.limits.scheduledPosts} scheduled posts. Upgrade your plan to schedule more posts.`}
            onDismiss={() => setShowScheduleLimitWarning(false)}
          />
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Post Content */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Post Content</h2>
            </div>
            <div className="p-6">
              <textarea
                value={formData.content}
                onChange={handleContentChange}
                placeholder="What's on your mind?"
                className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <div className="flex justify-between items-center mt-2">
                <button className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700">
                  <ImageIcon className="w-4 h-4 mr-1" />
                  Add Media
                </button>
                <div className={`text-sm ${isOverLimit() ? 'text-red-500' : 'text-gray-500'}`}>
                  {getCharacterCount()}/{getCharacterLimit()}
                </div>
              </div>
            </div>
          </div>

          {/* Platform Selection */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Select Platforms</h2>
            </div>
            <div className="p-6">
              {accounts.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">No connected accounts found.</p>
                  <button
                    onClick={() => router.push('/dashboard/accounts')}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Connect your social media accounts →
                  </button>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 gap-4">
                  {accounts.map((account) => {
                    const config = platformConfig[account.platform as keyof typeof platformConfig]
                    const Icon = config?.icon || Facebook
                    const isSelected = formData.platforms.includes(account.platform)

                    return (
                      <button
                        key={account.id}
                        onClick={() => handlePlatformToggle(account.platform)}
                        className={`flex items-center p-4 border-2 rounded-lg transition-all ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className={`w-8 h-8 flex items-center justify-center mr-3 ${config?.color}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="text-left">
                          <div className="font-medium text-gray-900">{config?.name}</div>
                          <div className="text-sm text-gray-500">{account.username}</div>
                        </div>
                        {isSelected && (
                          <div className="ml-auto">
                            <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                              <div className="w-2 h-2 bg-white rounded-full"></div>
                            </div>
                          </div>
                        )}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Scheduling */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Schedule Post</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="schedule"
                    value="now"
                    checked={!formData.scheduled_at}
                    onChange={() => setFormData(prev => ({ ...prev, scheduled_at: '' }))}
                    className="mr-2"
                  />
                  <span className="font-medium">Post now</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="schedule"
                    value="later"
                    checked={!!formData.scheduled_at}
                    onChange={() => setFormData(prev => ({ ...prev, scheduled_at: getMinDateTime() }))}
                    className="mr-2"
                  />
                  <span className="font-medium">Schedule for later</span>
                </label>
                {formData.scheduled_at && (
                  <div className="ml-6">
                    <input
                      type="datetime-local"
                      value={formData.scheduled_at}
                      onChange={handleScheduleChange}
                      min={getMinDateTime()}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Preview */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Preview</h2>
            </div>
            <div className="p-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <div className="w-8 h-8 bg-gray-300 rounded-full mr-2"></div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">Your Account</div>
                    <div className="text-xs text-gray-500">Just now</div>
                  </div>
                </div>
                <div className="text-gray-900">
                  {formData.content || 'Your post content will appear here...'}
                </div>
                {formData.platforms.length > 0 && (
                  <div className="flex space-x-2 mt-3">
                    {formData.platforms.map((platform) => {
                      const config = platformConfig[platform as keyof typeof platformConfig]
                      const Icon = config?.icon || Facebook
                      return (
                        <div key={platform} className={`w-5 h-5 ${config?.color}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6">
              <div className="space-y-3">
                <button
                  onClick={() => handleSubmit(false)}
                  disabled={loading || !formData.content.trim() || formData.platforms.length === 0 || isOverLimit()}
                  className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : formData.scheduled_at ? (
                    <Calendar className="w-4 h-4 mr-2" />
                  ) : (
                    <Send className="w-4 h-4 mr-2" />
                  )}
                  {formData.scheduled_at ? 'Schedule Post' : 'Post Now'}
                </button>
                
                <button
                  onClick={() => handleSubmit(true)}
                  disabled={loading || !formData.content.trim()}
                  className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save as Draft
                </button>

                <button
                  onClick={() => router.push('/dashboard/posts')}
                  className="w-full flex items-center justify-center px-4 py-2 text-gray-600 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <X className="w-4 h-4 mr-2" />
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}