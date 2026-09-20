import { Global, Module } from '@nestjs/common';
import { PrismaService } from './prisma.service.js';

/**
 * DatabaseModule is marked @Global so PrismaService is available
 * across the application without re-importing.
 */
@Global()
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class DatabaseModule {}
