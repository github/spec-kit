'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { 
  Calendar, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Edit,
  Trash2,
  BarChart3,
  Plus,
  Filter,
  Facebook,
  Twitter,
  Instagram,
  Linkedin
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface Post {
  id: string
  content: string
  platforms: string[]
  status: 'draft' | 'scheduled' | 'posted' | 'failed'
  scheduled_at?: string
  posted_at?: string
  created_at: string
  media_urls?: string[]
}

const platformIcons = {
  facebook: Facebook,
  twitter: Twitter,
  instagram: Instagram,
  linkedin: Linkedin,
}

const statusConfig = {
  draft: { color: 'bg-gray-100 text-gray-800', icon: Clock },
  scheduled: { color: 'bg-blue-100 text-blue-800', icon: Calendar },
  posted: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
  failed: { color: 'bg-red-100 text-red-800', icon: XCircle },
}

export default function PostsPage() {
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [deleting, setDeleting] = useState<string | null>(null)

  useEffect(() => {
    fetchPosts()
  }, [filter])

  const fetchPosts = async () => {
    try {
      const url = filter === 'all' ? '/api/posts' : `/api/posts?status=${filter}`
      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setPosts(data)
      }
    } catch (error) {
      console.error('Error fetching posts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeletePost = async (postId: string) => {
    if (!confirm('Are you sure you want to delete this post?')) {
      return
    }

    setDeleting(postId)
    
    try {
      const response = await fetch(`/api/posts?id=${postId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        setPosts(posts.filter(post => post.id !== postId))
      } else {
        console.error('Failed to delete post')
      }
    } catch (error) {
      console.error('Error deleting post:', error)
    } finally {
      setDeleting(null)
    }
  }

  const filteredPosts = posts.filter(post => 
    filter === 'all' || post.status === filter
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Posts</h1>
          <p className="text-gray-600">
            Manage your social media posts and track their performance.
          </p>
        </div>
        <Link
          href="/dashboard/posts/new"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Post
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="p-6">
          <div className="flex items-center space-x-1">
            <Filter className="w-4 h-4 text-gray-400 mr-2" />
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 text-sm font-medium rounded-full transition-colors ${
                filter === 'all'
                  ? 'bg-blue-100 text-blue-800'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              All Posts
            </button>
            {Object.keys(statusConfig).map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-3 py-1 text-sm font-medium rounded-full transition-colors capitalize ${
                  filter === status
                    ? 'bg-blue-100 text-blue-800'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Posts List */}
      {filteredPosts.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-12 text-center">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {filter === 'all' ? 'No posts yet' : `No ${filter} posts`}
            </h3>
            <p className="text-gray-600 mb-6">
              {filter === 'all' 
                ? 'Get started by creating your first social media post.'
                : `You don't have any ${filter} posts at the moment.`
              }
            </p>
            <Link
              href="/dashboard/posts/new"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Post
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredPosts.map((post) => {
            const StatusIcon = statusConfig[post.status].icon

            return (
              <div
                key={post.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Post Content */}
                    <div className="mb-4">
                      <p className="text-gray-900 text-lg leading-relaxed">
                        {post.content}
                      </p>
                      {post.media_urls && post.media_urls.length > 0 && (
                        <div className="mt-3 flex space-x-2">
                          {post.media_urls.slice(0, 3).map((url, index) => (
                            <img
                              key={index}
                              src={url}
                              alt={`Media ${index + 1}`}
                              className="w-16 h-16 object-cover rounded-lg"
                            />
                          ))}
                          {post.media_urls.length > 3 && (
                            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
                              <span className="text-sm text-gray-600">
                                +{post.media_urls.length - 3}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Post Meta */}
                    <div className="flex items-center space-x-6 text-sm text-gray-600">
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig[post.status].color}`}>
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {post.status.charAt(0).toUpperCase() + post.status.slice(1)}
                        </span>
                      </div>

                      <div className="flex items-center space-x-1">
                        {post.platforms.map((platform) => {
                          const Icon = platformIcons[platform as keyof typeof platformIcons]
                          return Icon ? (
                            <Icon key={platform} className="w-4 h-4 text-gray-400" />
                          ) : (
                            <span key={platform} className="text-xs text-gray-500 capitalize">
                              {platform}
                            </span>
                          )
                        })}
                      </div>

                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {post.status === 'scheduled' && post.scheduled_at ? (
                          <span>Scheduled for {formatDate(new Date(post.scheduled_at))}</span>
                        ) : post.status === 'posted' && post.posted_at ? (
                          <span>Posted on {formatDate(new Date(post.posted_at))}</span>
                        ) : (
                          <span>Created on {formatDate(new Date(post.created_at))}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 ml-4">
                    {post.status === 'posted' && (
                      <button
                        className="p-2 text-gray-400 hover:text-blue-500 transition-colors"
                        title="View Analytics"
                      >
                        <BarChart3 className="w-4 h-4" />
                      </button>
                    )}
                    
                    {(post.status === 'draft' || post.status === 'scheduled') && (
                      <Link
                        href={`/dashboard/posts/${post.id}/edit`}
                        className="p-2 text-gray-400 hover:text-blue-500 transition-colors"
                        title="Edit Post"
                      >
                        <Edit className="w-4 h-4" />
                      </Link>
                    )}

                    <button
                      onClick={() => handleDeletePost(post.id)}
                      disabled={deleting === post.id}
                      className="p-2 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                      title="Delete Post"
                    >
                      {deleting === post.id ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-500"></div>
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}