import { NextRequest, NextResponse } from 'next/server'
import { headers } from 'next/headers'
import { stripe } from '@/lib/stripe'
import { supabaseAdmin } from '@/lib/supabase'
import Stripe from 'stripe'

export async function POST(req: NextRequest) {
  const body = await req.text()
  const signature = headers().get('stripe-signature')!

  let event: Stripe.Event

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    )
  } catch (err: any) {
    console.error(`Webhook signature verification failed.`, err.message)
    return NextResponse.json(
      { error: 'Webhook signature verification failed' },
      { status: 400 }
    )
  }

  try {
    switch (event.type) {
      case 'customer.subscription.created':
      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription
        
        // Get the user by Stripe customer ID
        const { data: userData, error: userError } = await supabaseAdmin
          .from('users')
          .select('id, clerk_id')
          .eq('stripe_customer_id', subscription.customer as string)
          .single()

        if (userError) {
          console.error('Error finding user:', userError)
          break
        }

        // Determine subscription tier from price ID
        const priceId = subscription.items.data[0]?.price.id
        let tier: 'basic' | 'pro' | 'enterprise' = 'basic'
        
        if (priceId === 'price_pro_monthly') tier = 'pro'
        else if (priceId === 'price_enterprise_monthly') tier = 'enterprise'

        // Update user subscription status
        await supabaseAdmin
          .from('users')
          .update({
            subscription_tier: tier,
            subscription_status: subscription.status as any,
          })
          .eq('id', userData.id)

        // Upsert subscription record
        await supabaseAdmin
          .from('subscriptions')
          .upsert({
            user_id: userData.id,
            stripe_subscription_id: subscription.id,
            stripe_price_id: priceId,
            tier,
            status: subscription.status as any,
            current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
            current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
            cancel_at_period_end: subscription.cancel_at_period_end,
          })

        console.log(`Subscription ${event.type} for user ${userData.clerk_id}`)
        break
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription
        
        // Get the user by Stripe customer ID
        const { data: userData, error: userError } = await supabaseAdmin
          .from('users')
          .select('id, clerk_id')
          .eq('stripe_customer_id', subscription.customer as string)
          .single()

        if (userError) {
          console.error('Error finding user:', userError)
          break
        }

        // Update user subscription status
        await supabaseAdmin
          .from('users')
          .update({
            subscription_tier: null,
            subscription_status: 'canceled',
          })
          .eq('id', userData.id)

        // Update subscription record
        await supabaseAdmin
          .from('subscriptions')
          .update({
            status: 'canceled',
          })
          .eq('stripe_subscription_id', subscription.id)

        console.log(`Subscription deleted for user ${userData.clerk_id}`)
        break
      }

      case 'invoice.payment_succeeded': {
        const invoice = event.data.object as Stripe.Invoice
        console.log(`Payment succeeded for invoice ${invoice.id}`)
        break
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice
        
        if (invoice.subscription) {
          // Get the user by subscription
          const { data: subData, error: subError } = await supabaseAdmin
            .from('subscriptions')
            .select('user_id')
            .eq('stripe_subscription_id', invoice.subscription as string)
            .single()

          if (!subError && subData) {
            await supabaseAdmin
              .from('users')
              .update({
                subscription_status: 'past_due',
              })
              .eq('id', subData.user_id)
          }
        }

        console.log(`Payment failed for invoice ${invoice.id}`)
        break
      }

      default:
        console.log(`Unhandled event type ${event.type}`)
    }
  } catch (error) {
    console.error('Error processing webhook:', error)
    return NextResponse.json(
      { error: 'Webhook processing failed' },
      { status: 500 }
    )
  }

  return NextResponse.json({ received: true })
}