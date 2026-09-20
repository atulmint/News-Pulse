import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../database/prisma.service.js';

export interface TimelineEntryDto {
  clusterId: string;
  label: string;
  startTime: Date | string;
  endTime: Date | string;
  articleCount: number;
  intensity: number;
}

@Injectable()
export class TimelineService {
  constructor(private readonly prisma: PrismaService) {}

  async getTimeline(sourceFilter?: string): Promise<{ timeline: TimelineEntryDto[] }> {
    const sourceCondition = sourceFilter
      ? { articles: { some: { source: { name: { contains: sourceFilter, mode: 'insensitive' as const } } } } }
      : {};

    const clusters = await this.prisma.cluster.findMany({
      where: sourceCondition,
      include: {
        articles: {
          orderBy: { publishedAt: 'asc' },
        },
      },
    });

    const entries: TimelineEntryDto[] = clusters.map((cluster) => {
      const dates = cluster.articles
        .map((a) => a.publishedAt ?? a.createdAt)
        .sort((a, b) => a.getTime() - b.getTime());

      const startTime = dates.length > 0 ? dates[0] : cluster.createdAt;
      const endTime = dates.length > 0 ? dates[dates.length - 1] : cluster.createdAt;
      const articleCount = cluster.articles.length;

      return {
        clusterId: cluster.id,
        label: cluster.label,
        startTime,
        endTime,
        articleCount,
        intensity: articleCount,
      };
    });

    entries.sort((a, b) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime());

    return { timeline: entries };
  }
}
