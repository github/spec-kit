import { currentUser } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { Calendar, Users, BarChart3, TrendingUp, Clock, CheckCircle } from 'lucide-react'

export default async function Dashboard() {
  const user = await currentUser()
  
  if (!user) {
    redirect('/sign-in')
  }

  // Mock data - in real app, fetch from Supabase
  const stats = {
    totalPosts: 45,
    scheduledPosts: 12,
    connectedAccounts: 4,
    totalReach: 15420
  }

  const recentPosts = [
    {
      id: '1',
      content: 'Just launched our new product feature! 🚀',
      platforms: ['twitter', 'linkedin'],
      status: 'posted',
      scheduledAt: '2024-01-15T10:00:00Z',
      engagement: 234
    },
    {
      id: '2',
      content: 'Behind the scenes of our latest project...',
      platforms: ['instagram', 'facebook'],
      status: 'scheduled',
      scheduledAt: '2024-01-16T14:30:00Z',
      engagement: 0
    },
    {
      id: '3',
      content: 'Tips for better social media engagement',
      platforms: ['twitter', 'linkedin', 'facebook'],
      status: 'posted',
      scheduledAt: '2024-01-14T09:15:00Z',
      engagement: 567
    }
  ]

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">
          Welcome back, {user.firstName || 'User'}! 👋
        </h1>
        <p className="text-blue-100">
          Here's what's happening with your social media accounts today.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Calendar className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Posts</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalPosts}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Scheduled</p>
              <p className="text-2xl font-bold text-gray-900">{stats.scheduledPosts}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Accounts</p>
              <p className="text-2xl font-bold text-gray-900">{stats.connectedAccounts}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Reach</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalReach.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Posts */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Posts</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {recentPosts.map((post) => (
                <div key={post.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0">
                    {post.status === 'posted' ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <Clock className="w-5 h-5 text-blue-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 mb-1">{post.content}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className="capitalize">{post.platforms.join(', ')}</span>
                      <span>{new Date(post.scheduledAt).toLocaleDateString()}</span>
                      {post.status === 'posted' && (
                        <span className="flex items-center">
                          <BarChart3 className="w-3 h-3 mr-1" />
                          {post.engagement} engagements
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 gap-4">
              <a
                href="/dashboard/posts/new"
                className="flex flex-col items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
              >
                <Calendar className="w-8 h-8 text-blue-600 mb-2" />
                <span className="text-sm font-medium text-blue-900">Create Post</span>
              </a>
              
              <a
                href="/dashboard/accounts"
                className="flex flex-col items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
              >
                <Users className="w-8 h-8 text-green-600 mb-2" />
                <span className="text-sm font-medium text-green-900">Add Account</span>
              </a>
              
              <a
                href="/dashboard/analytics"
                className="flex flex-col items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
              >
                <BarChart3 className="w-8 h-8 text-purple-600 mb-2" />
                <span className="text-sm font-medium text-purple-900">View Analytics</span>
              </a>
              
              <a
                href="/dashboard/subscription"
                className="flex flex-col items-center p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors"
              >
                <TrendingUp className="w-8 h-8 text-orange-600 mb-2" />
                <span className="text-sm font-medium text-orange-900">Upgrade Plan</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}