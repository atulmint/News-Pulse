import { Module } from '@nestjs/common';
import { ClustersController } from './clusters.controller.js';
import { ClustersService } from './clusters.service.js';

@Module({
  controllers: [ClustersController],
  providers: [ClustersService],
})
export class ClustersModule {}
