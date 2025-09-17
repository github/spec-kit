export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          clerk_id: string
          email: string
          first_name: string | null
          last_name: string | null
          avatar_url: string | null
          subscription_tier: 'basic' | 'pro' | 'enterprise' | null
          subscription_status: 'active' | 'canceled' | 'past_due' | 'incomplete' | null
          stripe_customer_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          clerk_id: string
          email: string
          first_name?: string | null
          last_name?: string | null
          avatar_url?: string | null
          subscription_tier?: 'basic' | 'pro' | 'enterprise' | null
          subscription_status?: 'active' | 'canceled' | 'past_due' | 'incomplete' | null
          stripe_customer_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          clerk_id?: string
          email?: string
          first_name?: string | null
          last_name?: string | null
          avatar_url?: string | null
          subscription_tier?: 'basic' | 'pro' | 'enterprise' | null
          subscription_status?: 'active' | 'canceled' | 'past_due' | 'incomplete' | null
          stripe_customer_id?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      subscriptions: {
        Row: {
          id: string
          user_id: string
          stripe_subscription_id: string
          stripe_price_id: string
          tier: 'basic' | 'pro' | 'enterprise'
          status: 'active' | 'canceled' | 'past_due' | 'incomplete'
          current_period_start: string
          current_period_end: string
          cancel_at_period_end: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          stripe_subscription_id: string
          stripe_price_id: string
          tier: 'basic' | 'pro' | 'enterprise'
          status: 'active' | 'canceled' | 'past_due' | 'incomplete'
          current_period_start: string
          current_period_end: string
          cancel_at_period_end?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          stripe_subscription_id?: string
          stripe_price_id?: string
          tier?: 'basic' | 'pro' | 'enterprise'
          status?: 'active' | 'canceled' | 'past_due' | 'incomplete'
          current_period_start?: string
          current_period_end?: string
          cancel_at_period_end?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      social_accounts: {
        Row: {
          id: string
          user_id: string
          platform: string
          platform_user_id: string
          username: string
          avatar_url: string | null
          access_token: string | null
          refresh_token: string | null
          expires_at: string | null
          status: 'active' | 'inactive' | 'error'
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          platform: string
          platform_user_id: string
          username: string
          avatar_url?: string | null
          access_token?: string | null
          refresh_token?: string | null
          expires_at?: string | null
          status?: 'active' | 'inactive' | 'error'
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          platform?: string
          platform_user_id?: string
          username?: string
          avatar_url?: string | null
          access_token?: string | null
          refresh_token?: string | null
          expires_at?: string | null
          status?: 'active' | 'inactive' | 'error'
          created_at?: string
          updated_at?: string
        }
      }
      posts: {
        Row: {
          id: string
          user_id: string
          content: string
          platforms: string[]
          status: 'draft' | 'scheduled' | 'posted' | 'failed'
          scheduled_at: string | null
          posted_at: string | null
          ayrshare_post_id: string | null
          media_urls: string[] | null
          error_message: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          content: string
          platforms: string[]
          status?: 'draft' | 'scheduled' | 'posted' | 'failed'
          scheduled_at?: string | null
          posted_at?: string | null
          ayrshare_post_id?: string | null
          media_urls?: string[] | null
          error_message?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          content?: string
          platforms?: string[]
          status?: 'draft' | 'scheduled' | 'posted' | 'failed'
          scheduled_at?: string | null
          posted_at?: string | null
          ayrshare_post_id?: string | null
          media_urls?: string[] | null
          error_message?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      post_analytics: {
        Row: {
          id: string
          post_id: string
          platform: string
          impressions: number
          engagements: number
          clicks: number
          shares: number
          likes: number
          comments: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          post_id: string
          platform: string
          impressions?: number
          engagements?: number
          clicks?: number
          shares?: number
          likes?: number
          comments?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          post_id?: string
          platform?: string
          impressions?: number
          engagements?: number
          clicks?: number
          shares?: number
          likes?: number
          comments?: number
          created_at?: string
          updated_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      subscription_tier: 'basic' | 'pro' | 'enterprise'
      subscription_status: 'active' | 'canceled' | 'past_due' | 'incomplete'
      post_status: 'draft' | 'scheduled' | 'posted' | 'failed'
      account_status: 'active' | 'inactive' | 'error'
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}