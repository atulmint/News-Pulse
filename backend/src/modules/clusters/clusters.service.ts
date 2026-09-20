import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../../database/prisma.service.js';

export interface ClusterSummaryDto {
  id: string;
  label: string;
  articleCount: number;
  startTime: Date | string;
  endTime: Date | string;
}

export interface ClusterDetailDto extends ClusterSummaryDto {
  articles: Array<{
    id: string;
    title: string;
    source: string;
    publishedTime: Date | string;
    originalUrl: string;
    summary: string | null;
  }>;
}

@Injectable()
export class ClustersService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(sourceFilter?: string): Promise<{ clusters: ClusterSummaryDto[] }> {
    const sourceCondition = sourceFilter
      ? { articles: { some: { source: { name: { contains: sourceFilter, mode: 'insensitive' as const } } } } }
      : {};

    const clusters = await this.prisma.cluster.findMany({
      where: sourceCondition,
      include: {
        articles: {
          include: { source: true },
          orderBy: { publishedAt: 'asc' },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    const mapped = clusters.map((cluster) => {
      const dates = cluster.articles
        .map((a) => a.publishedAt ?? a.createdAt)
        .sort((a, b) => a.getTime() - b.getTime());

      const startTime = dates.length > 0 ? dates[0] : cluster.createdAt;
      const endTime = dates.length > 0 ? dates[dates.length - 1] : cluster.createdAt;

      return {
        id: cluster.id,
        label: cluster.label,
        articleCount: cluster.articles.length,
        startTime,
        endTime,
      };
    });

    return { clusters: mapped };
  }

  async findOne(id: string): Promise<ClusterDetailDto> {
    const cluster = await this.prisma.cluster.findUnique({
      where: { id },
      include: {
        articles: {
          include: { source: true },
          orderBy: { publishedAt: 'asc' },
        },
      },
    });

    if (!cluster) {
      throw new NotFoundException(`Cluster with ID "${id}" not found.`);
    }

    const sortedArticles = [...cluster.articles].sort((a, b) => {
      const timeA = (a.publishedAt ?? a.createdAt).getTime();
      const timeB = (b.publishedAt ?? b.createdAt).getTime();
      return timeA - timeB;
    });

    const dates = sortedArticles.map((a) => a.publishedAt ?? a.createdAt);
    const startTime = dates.length > 0 ? dates[0] : cluster.createdAt;
    const endTime = dates.length > 0 ? dates[dates.length - 1] : cluster.createdAt;

    return {
      id: cluster.id,
      label: cluster.label,
      articleCount: sortedArticles.length,
      startTime,
      endTime,
      articles: sortedArticles.map((art) => ({
        id: art.id,
        title: art.title,
        source: art.source.name,
        publishedTime: art.publishedAt ?? art.createdAt,
        originalUrl: art.url,
        summary: art.summary,
      })),
    };
  }
}
