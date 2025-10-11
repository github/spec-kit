# Database Setup Guide

## Prerequisites

1. **Install PostgreSQL**
   - Download from: https://www.postgresql.org/download/windows/
   - Or use Docker: `docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres`

2. **Create Database**
   ```sql
   -- Connect to PostgreSQL as superuser
   CREATE DATABASE printing_services;
   CREATE USER printing_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE printing_services TO printing_user;
   ```

## Environment Setup

1. **Copy environment file**
   ```bash
   cd backend
   copy .env.example .env
   ```

2. **Update .env file**
   ```env
   DATABASE_URL="postgresql://printing_user:your_password@localhost:5432/printing_services"
   JWT_SECRET="your-super-secret-jwt-key-here-make-it-long-and-random"
   ```

## Database Migration & Seeding

1. **Generate Prisma Client**
   ```bash
   npm run prisma:generate
   ```

2. **Run Database Migrations**
   ```bash
   npm run prisma:migrate
   ```

3. **Seed Database with Sample Data**
   ```bash
   npm run prisma:seed
   ```

4. **Open Prisma Studio (Optional)**
   ```bash
   npm run prisma:studio
   ```

## Test Database Connection

1. **Start the backend server**
   ```bash
   npm run dev
   ```

2. **Check health endpoint**
   - Open: http://localhost:5000/health
   - Should show: "Database: Connected"

## Sample Users Created by Seed

- **Admin**: admin@printmarket.ca (password: admin123)
- **Customer**: customer@example.com (password: customer123)  
- **Broker**: broker@printshop.ca (password: broker123)

## Troubleshooting

### Connection Issues
- Ensure PostgreSQL is running
- Check DATABASE_URL format
- Verify user permissions

### Migration Issues
- Delete `prisma/migrations` folder and run `prisma migrate dev --name init`
- Check database exists and user has permissions

### Seed Issues
- Ensure migrations are applied first
- Check for unique constraint violations
- Clear database: `prisma migrate reset`
