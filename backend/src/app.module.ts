import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import configuration from './config/configuration.js';
import { DatabaseModule } from './database/database.module.js';
import { ArticlesModule } from './modules/articles/articles.module.js';
import { ClustersModule } from './modules/clusters/clusters.module.js';
import { TimelineModule } from './modules/timeline/timeline.module.js';
import { IngestionModule } from './modules/ingestion/ingestion.module.js';
import { HealthController } from './common/health.controller.js';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true, load: [configuration] }),
    DatabaseModule,
    ArticlesModule,
    ClustersModule,
    TimelineModule,
    IngestionModule,
  ],
  controllers: [HealthController],
})
export class AppModule {}
