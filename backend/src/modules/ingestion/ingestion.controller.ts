import { Controller, Get, Param, Post } from '@nestjs/common';
import { IngestionService, TriggerJobResponseDto, JobStatusResponseDto } from './ingestion.service.js';

@Controller('ingest')
export class IngestionController {
  constructor(private readonly ingestionService: IngestionService) {}

  @Post('trigger')
  async triggerIngestion(): Promise<TriggerJobResponseDto> {
    return this.ingestionService.triggerIngestion();
  }

  @Get('status/:jobId')
  async getJobStatus(@Param('jobId') jobId: string): Promise<JobStatusResponseDto> {
    return this.ingestionService.getJobStatus(jobId);
  }
}
