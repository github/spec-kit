import { NextRequest, NextResponse } from 'next/server'
import { currentUser } from '@clerk/nextjs/server'
import { supabase } from '@/lib/supabase'
import { ayrshare } from '@/lib/ayrshare'

export async function GET(req: NextRequest) {
  try {
    const user = await currentUser()
    
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { searchParams } = new URL(req.url)
    const status = searchParams.get('status')
    const limit = parseInt(searchParams.get('limit') || '10')
    const offset = parseInt(searchParams.get('offset') || '0')

    // Get user ID from Supabase
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('id')
      .eq('clerk_id', user.id)
      .single()

    if (userError) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    let query = supabase
      .from('posts')
      .select('*')
      .eq('user_id', userData.id)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (status) {
      query = query.eq('status', status)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching posts:', error)
      return NextResponse.json({ error: 'Failed to fetch posts' }, { status: 500 })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Error in GET /api/posts:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(req: NextRequest) {
  try {
    const user = await currentUser()
    
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await req.json()
    const { content, platforms, scheduled_at, media_urls } = body

    // Get user ID from Supabase
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('id')
      .eq('clerk_id', user.id)
      .single()

    if (userError) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Determine post status
    const isScheduled = scheduled_at && new Date(scheduled_at) > new Date()
    const status = isScheduled ? 'scheduled' : 'draft'

    // Create post in database
    const { data: post, error: postError } = await supabase
      .from('posts')
      .insert({
        user_id: userData.id,
        content,
        platforms,
        status,
        scheduled_at: scheduled_at || null,
        media_urls: media_urls || null,
      })
      .select()
      .single()

    if (postError) {
      console.error('Error creating post:', postError)
      return NextResponse.json({ error: 'Failed to create post' }, { status: 500 })
    }

    // If it's a scheduled post, create it in Ayrshare
    if (status === 'scheduled') {
      try {
        const ayrsharePost = await ayrshare.createPost(user.id, {
          post: content,
          platforms,
          scheduleDate: scheduled_at,
          mediaUrls: media_urls,
        })

        // Update post with Ayrshare ID
        await supabase
          .from('posts')
          .update({ ayrshare_post_id: ayrsharePost.id })
          .eq('id', post.id)

        post.ayrshare_post_id = ayrsharePost.id
      } catch (ayrshareError) {
        console.error('Error creating post in Ayrshare:', ayrshareError)
        // Update post status to failed
        await supabase
          .from('posts')
          .update({ 
            status: 'failed',
            error_message: 'Failed to schedule post with Ayrshare'
          })
          .eq('id', post.id)
      }
    }

    return NextResponse.json(post)
  } catch (error) {
    console.error('Error in POST /api/posts:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function PUT(req: NextRequest) {
  try {
    const user = await currentUser()
    
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await req.json()
    const { id, content, platforms, scheduled_at, media_urls } = body

    // Get user ID from Supabase
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('id')
      .eq('clerk_id', user.id)
      .single()

    if (userError) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Get the existing post
    const { data: existingPost, error: fetchError } = await supabase
      .from('posts')
      .select('*')
      .eq('id', id)
      .eq('user_id', userData.id)
      .single()

    if (fetchError) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 })
    }

    // Update post in database
    const { data: updatedPost, error: updateError } = await supabase
      .from('posts')
      .update({
        content,
        platforms,
        scheduled_at: scheduled_at || null,
        media_urls: media_urls || null,
        updated_at: new Date().toISOString(),
      })
      .eq('id', id)
      .eq('user_id', userData.id)
      .select()
      .single()

    if (updateError) {
      console.error('Error updating post:', updateError)
      return NextResponse.json({ error: 'Failed to update post' }, { status: 500 })
    }

    // If post has Ayrshare ID, update it there too
    if (existingPost.ayrshare_post_id) {
      try {
        // Note: Ayrshare doesn't support updating scheduled posts directly
        // You might need to delete and recreate the post
        await ayrshare.deletePost(existingPost.ayrshare_post_id)
        
        if (scheduled_at && new Date(scheduled_at) > new Date()) {
          const newAyrsharePost = await ayrshare.createPost(user.id, {
            post: content,
            platforms,
            scheduleDate: scheduled_at,
            mediaUrls: media_urls,
          })

          await supabase
            .from('posts')
            .update({ ayrshare_post_id: newAyrsharePost.id })
            .eq('id', id)
        }
      } catch (ayrshareError) {
        console.error('Error updating post in Ayrshare:', ayrshareError)
      }
    }

    return NextResponse.json(updatedPost)
  } catch (error) {
    console.error('Error in PUT /api/posts:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const user = await currentUser()
    
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { searchParams } = new URL(req.url)
    const postId = searchParams.get('id')

    if (!postId) {
      return NextResponse.json({ error: 'Post ID is required' }, { status: 400 })
    }

    // Get user ID from Supabase
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('id')
      .eq('clerk_id', user.id)
      .single()

    if (userError) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Get the post to check if it has an Ayrshare ID
    const { data: post, error: fetchError } = await supabase
      .from('posts')
      .select('ayrshare_post_id')
      .eq('id', postId)
      .eq('user_id', userData.id)
      .single()

    if (fetchError) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 })
    }

    // Delete from Ayrshare if it exists
    if (post.ayrshare_post_id) {
      try {
        await ayrshare.deletePost(post.ayrshare_post_id)
      } catch (ayrshareError) {
        console.error('Error deleting post from Ayrshare:', ayrshareError)
      }
    }

    // Delete from database
    const { error } = await supabase
      .from('posts')
      .delete()
      .eq('id', postId)
      .eq('user_id', userData.id)

    if (error) {
      console.error('Error deleting post:', error)
      return NextResponse.json({ error: 'Failed to delete post' }, { status: 500 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error in DELETE /api/posts:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}