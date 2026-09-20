import { Controller, Get, Query } from '@nestjs/common';
import { TimelineService, TimelineEntryDto } from './timeline.service.js';

@Controller('timeline')
export class TimelineController {
  constructor(private readonly timelineService: TimelineService) {}

  @Get()
  async getTimeline(@Query('source') source?: string): Promise<{ timeline: TimelineEntryDto[] }> {
    return this.timelineService.getTimeline(source);
  }
}
