import { Injectable, NotFoundException, Logger } from '@nestjs/common';
import { JobStatus } from '@prisma/client';
import { spawn } from 'child_process';
import path from 'path';
import { PrismaService } from '../../database/prisma.service.js';

export interface TriggerJobResponseDto {
  jobId: string;
  status: string;
}

export interface JobStatusResponseDto {
  jobId: string;
  status: string;
  startedAt: Date | string | null;
  completedAt: Date | string | null;
  articlesProcessed: number;
  articlesCreated: number;
  error: string | null;
}

@Injectable()
export class IngestionService {
  private readonly logger = new Logger(IngestionService.name);

  constructor(private readonly prisma: PrismaService) {}

  async triggerIngestion(): Promise<TriggerJobResponseDto> {
    const job = await this.prisma.ingestionJob.create({
      data: {
        status: JobStatus.PENDING,
        startedAt: new Date(),
      },
    });

    this.runPythonIngestionProcess(job.id);

    return {
      jobId: job.id,
      status: job.status,
    };
  }

  async getJobStatus(jobId: string): Promise<JobStatusResponseDto> {
    const job = await this.prisma.ingestionJob.findUnique({
      where: { id: jobId },
    });

    if (!job) {
      throw new NotFoundException(`Ingestion job with ID "${jobId}" not found.`);
    }

    return {
      jobId: job.id,
      status: job.status,
      startedAt: job.startedAt,
      completedAt: job.completedAt,
      articlesProcessed: job.articlesFound,
      articlesCreated: job.articlesNew,
      error: job.errorMessage,
    };
  }

  private runPythonIngestionProcess(jobId: string): void {
    const pythonExecutable = process.env.PYTHON_PATH ?? 'python';
    const scraperDir = path.resolve(process.cwd(), '../scraper');

    this.logger.log(`Starting background ingestion process for job ${jobId}...`);

    this.prisma.ingestionJob
      .update({
        where: { id: jobId },
        data: { status: JobStatus.RUNNING },
      })
      .then(() => {
        const child = spawn(pythonExecutable, ['src/main.py'], {
          cwd: scraperDir,
          env: {
            ...process.env,
            PYTHONPATH: scraperDir,
          },
        });

        let stderrBuffer = '';
        let hasHandledCompletion = false;

        const markFailed = async (errorMessage: string) => {
          if (hasHandledCompletion) return;
          hasHandledCompletion = true;
          try {
            await this.prisma.ingestionJob.update({
              where: { id: jobId },
              data: {
                status: JobStatus.FAILED,
                completedAt: new Date(),
                errorMessage: errorMessage.slice(-500),
              },
            });
          } catch (e) {
            this.logger.error(`Failed updating job failure state: ${e}`);
          }
        };

        const markCompleted = async () => {
          if (hasHandledCompletion) return;
          hasHandledCompletion = true;
          try {
            await this.prisma.ingestionJob.update({
              where: { id: jobId },
              data: {
                status: JobStatus.COMPLETED,
                completedAt: new Date(),
              },
            });
          } catch (e) {
            this.logger.error(`Failed updating job completion state: ${e}`);
          }
        };

        child.stderr?.on('data', (chunk) => {
          stderrBuffer += chunk.toString();
        });

        child.on('error', (err) => {
          this.logger.error(`Ingestion process error for job ${jobId}: ${err.message}`);
          markFailed(`Process error: ${err.message}`);
        });

        child.on('close', (code) => {
          if (code === 0) {
            this.logger.log(`Ingestion job ${jobId} completed successfully.`);
            markCompleted();
          } else {
            const errSummary = stderrBuffer.trim() || `Process exited with code ${code}`;
            this.logger.error(`Ingestion job ${jobId} failed: ${errSummary}`);
            markFailed(errSummary);
          }
        });
      })
      .catch((err) => {
        this.logger.error(`Failed to set job status to RUNNING for job ${jobId}: ${err}`);
      });
  }
}
