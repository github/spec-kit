# Social Media Manager

A comprehensive Next.js application for managing social media presence across multiple platforms with subscription-based access control.

## Features

- **Authentication**: Clerk-powered authentication with social login support
- **Payment Processing**: Stripe integration with multiple subscription tiers
- **Social Media Management**: Connect and manage Facebook, Twitter, Instagram, and LinkedIn accounts
- **Post Scheduling**: Create and schedule posts across multiple platforms
- **Analytics**: Track post performance and engagement metrics
- **Access Control**: Subscription-based feature restrictions and usage limits

## Tech Stack

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Authentication**: Clerk
- **Payments**: Stripe
- **Database**: Supabase (PostgreSQL)
- **Social Media API**: Ayrshare
- **UI Components**: Lucide React icons, Radix UI components

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Supabase account and project
- Clerk account and application
- Stripe account
- Ayrshare account

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd social-media-manager
```

2. Install dependencies:
```bash
npm install
```

3. Copy the environment template:
```bash
cp .env.example .env.local
```

4. Configure your environment variables:

```env
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Ayrshare
AYRSHARE_API_KEY=your_api_key
AYRSHARE_DOMAIN=your_domain

# App Configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Database Setup

1. Run the Supabase migration:
```bash
# In your Supabase dashboard, run the SQL from:
# supabase/migrations/001_initial_schema.sql
```

2. Set up Row Level Security policies as defined in the migration file.

### Stripe Setup

1. Create products and prices in your Stripe dashboard:
   - Basic Plan: $9.99/month (`price_basic_monthly`)
   - Pro Plan: $29.99/month (`price_pro_monthly`)
   - Enterprise Plan: $99.99/month (`price_enterprise_monthly`)

2. Update the price IDs in `src/lib/stripe.ts`

3. Configure webhooks in Stripe dashboard:
   - Endpoint URL: `https://your-domain.com/api/webhooks/stripe`
   - Events: `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`

### Clerk Setup

1. Configure your Clerk application:
   - Add social providers (Google, Apple, etc.)
   - Set up webhook endpoint: `https://your-domain.com/api/webhooks/clerk`
   - Enable events: `user.created`, `user.updated`, `user.deleted`

### Ayrshare Setup

1. Create an Ayrshare account and get your API key
2. Configure your domain in Ayrshare dashboard
3. Set up OAuth applications for each social platform

### Development

Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Authentication pages
│   ├── dashboard/         # Protected dashboard pages
│   ├── api/               # API routes
│   └── globals.css        # Global styles
├── components/            # Reusable UI components
├── hooks/                 # Custom React hooks
├── lib/                   # Utility libraries and configurations
└── types/                 # TypeScript type definitions
```

## Key Features

### Authentication System
- Clerk integration with social login
- Protected routes with middleware
- User profile management
- Webhook synchronization with Supabase

### Subscription Management
- Three-tier subscription model (Basic, Pro, Enterprise)
- Stripe integration for payments
- Usage-based restrictions
- Upgrade prompts and billing portal

### Social Media Integration
- Connect multiple social accounts per platform
- OAuth flow through Ayrshare
- Account status monitoring
- Platform-specific limitations

### Post Management
- Rich text post creation
- Multi-platform publishing
- Scheduled posting
- Draft management
- Character count validation per platform

### Analytics Dashboard
- Post performance metrics
- Platform-wise breakdown
- Engagement tracking
- Historical data visualization

## API Routes

### Authentication
- `POST /api/webhooks/clerk` - Clerk webhook handler

### User Management
- `GET /api/user` - Get current user data
- `PUT /api/user` - Update user profile

### Social Accounts
- `GET /api/social-accounts` - List connected accounts
- `POST /api/social-accounts` - Connect new account
- `DELETE /api/social-accounts` - Disconnect account

### Posts
- `GET /api/posts` - List user posts
- `POST /api/posts` - Create new post
- `PUT /api/posts` - Update existing post
- `DELETE /api/posts` - Delete post

### Payments
- `POST /api/create-checkout-session` - Create Stripe checkout
- `POST /api/create-portal-session` - Create billing portal session
- `POST /api/webhooks/stripe` - Stripe webhook handler

## Deployment

### Vercel Deployment

1. Connect your repository to Vercel
2. Configure environment variables in Vercel dashboard
3. Deploy the application

### Environment Variables for Production

Ensure all environment variables are properly set:
- Update URLs to production domains
- Use production API keys
- Configure webhook endpoints with production URLs

### Database Migration

Run the Supabase migration in your production database:
1. Access your Supabase project dashboard
2. Go to SQL Editor
3. Run the migration script from `supabase/migrations/001_initial_schema.sql`

## Security Considerations

- All API routes are protected with Clerk authentication
- Row Level Security is enabled on all Supabase tables
- Webhook endpoints verify signatures
- Environment variables contain sensitive data
- Rate limiting should be implemented for production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Check the documentation
- Review the code comments
- Open an issue on GitHub

## Roadmap

- [ ] Mobile app development
- [ ] Advanced analytics with charts
- [ ] Bulk post scheduling
- [ ] Team collaboration features
- [ ] API for third-party integrations
- [ ] White-label solutions
- [ ] Advanced content planning tools