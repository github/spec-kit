import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting database seed...');

  const hashedPassword = bcrypt.hashSync('password', 12);

  // Create sample users
  await prisma.user.createMany({
    data: [
      {
        email: 'admin@printmarket.ca',
        password: hashedPassword,
        role: 'ADMIN',
        isEmailVerified: true,
        isVerified: true,
      },
      {
        email: 'customer@example.com',
        password: hashedPassword,
        role: 'CUSTOMER',
        isEmailVerified: true,
        isVerified: true,
      },
      {
        email: 'broker@printshop.ca',
        password: hashedPassword,
        role: 'BROKER',
        companyName: 'QuickPrint Inc.',
        isEmailVerified: true,
        isVerified: true,
      },
    ],
  });

  console.log('✅ Database seeded with 3 users!');
  console.log('📧 Admin: admin@printmarket.ca (password: password)');
  console.log('👤 Customer: customer@example.com (password: password)');
  console.log('🏢 Broker: broker@printshop.ca (password: password)');
}

main()
  .catch((e) => {
    console.error('❌ Error seeding database:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
