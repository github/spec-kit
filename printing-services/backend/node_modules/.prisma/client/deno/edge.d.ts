class PrismaClient {
  constructor() {
    throw new Error(
      '@prisma/client/deno/edge did not initialize yet. Please run "prisma generate" and try to import it again.',
    )
  }
}

export { PrismaClient }
