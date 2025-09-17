'use client'

import { useState, useEffect } from 'react'
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Heart, 
  MessageCircle, 
  Share,
  Eye,
  Calendar,
  Facebook,
  Twitter,
  Instagram,
  Linkedin
} from 'lucide-react'

interface AnalyticsData {
  totalPosts: number
  totalReach: number
  totalEngagements: number
  totalClicks: number
  platformBreakdown: {
    platform: string
    posts: number
    reach: number
    engagements: number
  }[]
  recentPosts: {
    id: string
    content: string
    platform: string
    posted_at: string
    metrics: {
      impressions: number
      engagements: number
      clicks: number
      likes: number
      comments: number
      shares: number
    }
  }[]
}

const platformConfig = {
  facebook: { name: 'Facebook', icon: Facebook, color: 'text-blue-600', bgColor: 'bg-blue-50' },
  twitter: { name: 'Twitter', icon: Twitter, color: 'text-sky-500', bgColor: 'bg-sky-50' },
  instagram: { name: 'Instagram', icon: Instagram, color: 'text-pink-600', bgColor: 'bg-pink-50' },
  linkedin: { name: 'LinkedIn', icon: Linkedin, color: 'text-blue-700', bgColor: 'bg-blue-50' },
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('30d')

  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  const fetchAnalytics = async () => {
    try {
      // Mock data - in real app, fetch from API
      const mockData: AnalyticsData = {
        totalPosts: 45,
        totalReach: 15420,
        totalEngagements: 1240,
        totalClicks: 320,
        platformBreakdown: [
          { platform: 'facebook', posts: 15, reach: 6500, engagements: 450 },
          { platform: 'twitter', posts: 12, reach: 3200, engagements: 280 },
          { platform: 'instagram', posts: 10, reach: 4100, engagements: 380 },
          { platform: 'linkedin', posts: 8, reach: 1620, engagements: 130 },
        ],
        recentPosts: [
          {
            id: '1',
            content: 'Just launched our new product feature! 🚀',
            platform: 'twitter',
            posted_at: '2024-01-15T10:00:00Z',
            metrics: { impressions: 1250, engagements: 89, clicks: 23, likes: 67, comments: 12, shares: 10 }
          },
          {
            id: '2',
            content: 'Behind the scenes of our latest project...',
            platform: 'instagram',
            posted_at: '2024-01-14T14:30:00Z',
            metrics: { impressions: 980, engagements: 124, clicks: 15, likes: 98, comments: 18, shares: 8 }
          },
          {
            id: '3',
            content: 'Tips for better social media engagement',
            platform: 'linkedin',
            posted_at: '2024-01-13T09:15:00Z',
            metrics: { impressions: 750, engagements: 45, clicks: 12, likes: 32, comments: 8, shares: 5 }
          }
        ]
      }
      
      setAnalytics(mockData)
    } catch (error) {
      console.error('Error fetching analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Analytics Data</h3>
        <p className="text-gray-600">Start posting to see your analytics here.</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics</h1>
          <p className="text-gray-600">
            Track your social media performance and engagement metrics.
          </p>
        </div>
        
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
        </select>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Posts</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.totalPosts}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Eye className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Reach</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.totalReach.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Heart className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Engagements</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.totalEngagements.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Clicks</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.totalClicks}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8 mb-8">
        {/* Platform Breakdown */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Platform Performance</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {analytics.platformBreakdown.map((platform) => {
                const config = platformConfig[platform.platform as keyof typeof platformConfig]
                const Icon = config?.icon || BarChart3

                return (
                  <div key={platform.platform} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-8 h-8 ${config?.bgColor} rounded-lg flex items-center justify-center`}>
                        <Icon className={`w-4 h-4 ${config?.color}`} />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{config?.name}</h3>
                        <p className="text-sm text-gray-500">{platform.posts} posts</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">{platform.reach.toLocaleString()}</p>
                      <p className="text-sm text-gray-500">{platform.engagements} engagements</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Engagement Rate Chart Placeholder */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Engagement Rate Trend</h2>
          </div>
          <div className="p-6">
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">Chart visualization would go here</p>
                <p className="text-sm text-gray-400 mt-1">Integration with charting library needed</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Post Performance */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Post Performance</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Post
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Platform
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Impressions
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Engagements
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rate
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analytics.recentPosts.map((post) => {
                const config = platformConfig[post.platform as keyof typeof platformConfig]
                const Icon = config?.icon || BarChart3
                const engagementRate = ((post.metrics.engagements / post.metrics.impressions) * 100).toFixed(1)

                return (
                  <tr key={post.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 max-w-xs truncate">
                        {post.content}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <Icon className={`w-4 h-4 ${config?.color}`} />
                        <span className="text-sm text-gray-900">{config?.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(post.posted_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {post.metrics.impressions.toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span className="flex items-center">
                          <Heart className="w-3 h-3 mr-1" />
                          {post.metrics.likes}
                        </span>
                        <span className="flex items-center">
                          <MessageCircle className="w-3 h-3 mr-1" />
                          {post.metrics.comments}
                        </span>
                        <span className="flex items-center">
                          <Share className="w-3 h-3 mr-1" />
                          {post.metrics.shares}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {engagementRate}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}