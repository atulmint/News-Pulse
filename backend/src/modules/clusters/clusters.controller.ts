import { Controller, Get, Param, Query } from '@nestjs/common';
import { ClustersService, ClusterSummaryDto, ClusterDetailDto } from './clusters.service.js';

@Controller('clusters')
export class ClustersController {
  constructor(private readonly clustersService: ClustersService) {}

  @Get()
  async findAll(@Query('source') source?: string): Promise<{ clusters: ClusterSummaryDto[] }> {
    return this.clustersService.findAll(source);
  }

  @Get(':id')
  async findOne(@Param('id') id: string): Promise<ClusterDetailDto> {
    return this.clustersService.findOne(id);
  }
}
