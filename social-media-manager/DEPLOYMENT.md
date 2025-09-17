# Deployment Guide

This guide covers deploying the Social Media Manager application to production.

## Pre-deployment Checklist

### 1. Environment Variables
Ensure all required environment variables are configured:

```bash
# Production URLs
NEXT_PUBLIC_APP_URL=https://your-domain.com

# Clerk (Production)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...

# Stripe (Production)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Supabase (Production)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# Ayrshare (Production)
AYRSHARE_API_KEY=...
AYRSHARE_DOMAIN=...
```

### 2. Database Setup

1. **Create Production Database**:
   - Create a new Supabase project for production
   - Note the database URL and keys

2. **Run Migrations**:
   ```sql
   -- Execute the contents of supabase/migrations/001_initial_schema.sql
   -- in your Supabase SQL Editor
   ```

3. **Configure RLS Policies**:
   - Ensure all Row Level Security policies are active
   - Test with a sample user account

### 3. Third-Party Service Configuration

#### Stripe Setup
1. **Create Products**:
   ```bash
   # Create subscription products in Stripe Dashboard
   # Update price IDs in src/lib/stripe.ts
   ```

2. **Configure Webhooks**:
   - Endpoint: `https://your-domain.com/api/webhooks/stripe`
   - Events: `customer.subscription.*`, `invoice.payment_*`

#### Clerk Setup
1. **Production Instance**:
   - Create production Clerk application
   - Configure allowed origins: `https://your-domain.com`

2. **Webhooks**:
   - Endpoint: `https://your-domain.com/api/webhooks/clerk`
   - Events: `user.created`, `user.updated`, `user.deleted`

#### Ayrshare Setup
1. **Domain Configuration**:
   - Add production domain to Ayrshare
   - Update OAuth redirect URLs

## Deployment Options

### Option 1: Vercel (Recommended)

1. **Connect Repository**:
   ```bash
   # Push code to GitHub/GitLab/Bitbucket
   # Connect repository in Vercel dashboard
   ```

2. **Configure Environment Variables**:
   - Add all production environment variables
   - Use Vercel's environment variable interface

3. **Deploy**:
   ```bash
   # Automatic deployment on git push
   # Or manual deployment from Vercel dashboard
   ```

4. **Custom Domain**:
   - Add your custom domain in Vercel
   - Configure DNS records

### Option 2: Docker Deployment

1. **Create Dockerfile**:
   ```dockerfile
   FROM node:18-alpine AS deps
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production

   FROM node:18-alpine AS builder
   WORKDIR /app
   COPY . .
   COPY --from=deps /app/node_modules ./node_modules
   RUN npm run build

   FROM node:18-alpine AS runner
   WORKDIR /app
   ENV NODE_ENV production
   
   RUN addgroup -g 1001 -S nodejs
   RUN adduser -S nextjs -u 1001

   COPY --from=builder /app/public ./public
   COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
   COPY --from=builder /app/node_modules ./node_modules
   COPY --from=builder /app/package.json ./package.json

   USER nextjs
   EXPOSE 3000
   ENV PORT 3000

   CMD ["npm", "start"]
   ```

2. **Build and Deploy**:
   ```bash
   docker build -t social-media-manager .
   docker run -p 3000:3000 social-media-manager
   ```

### Option 3: Traditional VPS

1. **Server Setup**:
   ```bash
   # Install Node.js 18+
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs

   # Install PM2 for process management
   npm install -g pm2
   ```

2. **Application Deployment**:
   ```bash
   # Clone repository
   git clone <your-repo-url>
   cd social-media-manager

   # Install dependencies
   npm ci --only=production

   # Build application
   npm run build

   # Start with PM2
   pm2 start npm --name "social-media-manager" -- start
   pm2 startup
   pm2 save
   ```

3. **Reverse Proxy (Nginx)**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

## Post-Deployment Steps

### 1. Health Checks
```bash
# Test application endpoints
curl https://your-domain.com/api/health

# Test authentication
curl https://your-domain.com/api/user

# Test webhooks
# Use webhook testing tools for Stripe and Clerk
```

### 2. Monitoring Setup

1. **Application Monitoring**:
   - Set up error tracking (Sentry, Bugsnag)
   - Configure performance monitoring
   - Set up uptime monitoring

2. **Database Monitoring**:
   - Monitor Supabase metrics
   - Set up alerts for high usage
   - Configure backup schedules

### 3. SSL Certificate
```bash
# For VPS deployment with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 4. Security Headers
Add security headers to your deployment:

```javascript
// next.config.js
const nextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ]
  },
}
```

## Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**:
   - Check variable names and values
   - Restart application after changes
   - Verify deployment platform configuration

2. **Database Connection Errors**:
   - Verify Supabase URLs and keys
   - Check network connectivity
   - Review RLS policies

3. **Webhook Failures**:
   - Verify webhook URLs are accessible
   - Check webhook signatures
   - Review webhook event logs

4. **Authentication Issues**:
   - Verify Clerk configuration
   - Check redirect URLs
   - Review CORS settings

### Debugging Commands

```bash
# Check application logs
pm2 logs social-media-manager

# Test database connection
psql "postgresql://[username]:[password]@[host]:[port]/[database]"

# Verify environment variables
printenv | grep NEXT_PUBLIC

# Test webhook endpoints
curl -X POST https://your-domain.com/api/webhooks/stripe \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## Performance Optimization

### 1. Caching Strategy
- Enable Redis for session storage
- Implement API response caching
- Use CDN for static assets

### 2. Database Optimization
- Add database indexes for frequently queried fields
- Enable connection pooling
- Monitor query performance

### 3. Application Optimization
- Enable Next.js image optimization
- Implement code splitting
- Use service workers for offline capability

## Backup and Recovery

### 1. Database Backups
```bash
# Automated Supabase backups are enabled by default
# Additional manual backup
pg_dump "postgresql://[connection-string]" > backup.sql
```

### 2. Application Backups
- Regular git repository backups
- Environment variable backups (encrypted)
- Configuration file backups

### 3. Recovery Procedures
1. Database restoration from Supabase backups
2. Application redeployment from git
3. Environment variable restoration
4. Third-party service reconfiguration

## Scaling Considerations

### Horizontal Scaling
- Use load balancers for multiple instances
- Implement sticky sessions for authentication
- Consider serverless deployment (Vercel Functions)

### Database Scaling
- Monitor Supabase usage and upgrade plans
- Implement read replicas for heavy read workloads
- Consider database sharding for large datasets

### CDN and Caching
- Use Vercel Edge Network or CloudFlare
- Implement Redis for application caching
- Cache static assets and API responses

## Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] Environment variables secured
- [ ] Database access restricted
- [ ] Webhook signatures verified
- [ ] Rate limiting implemented
- [ ] Security headers configured
- [ ] Regular security updates
- [ ] Access logs monitored

## Maintenance

### Regular Tasks
- Monitor application performance
- Review error logs and fix issues
- Update dependencies regularly
- Backup verification
- Security patch updates

### Monthly Tasks
- Review usage metrics
- Optimize database performance
- Update documentation
- Security audit
- Cost optimization review