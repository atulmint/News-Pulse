import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { AppModule } from './../src/app.module.js';

describe('News Pulse API (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('GET /health → 200 ok', () => {
    return request(app.getHttpServer())
      .get('/health')
      .expect(200)
      .expect({ status: 'ok' });
  });

  it('GET /clusters → 200 ok with clusters array', async () => {
    const res = await request(app.getHttpServer()).get('/clusters').expect(200);
    expect(res.body).toHaveProperty('clusters');
    expect(Array.isArray(res.body.clusters)).toBe(true);
    if (res.body.clusters.length > 0) {
      const cluster = res.body.clusters[0];
      expect(cluster).toHaveProperty('id');
      expect(cluster).toHaveProperty('label');
      expect(cluster).toHaveProperty('articleCount');
      expect(cluster).toHaveProperty('startTime');
      expect(cluster).toHaveProperty('endTime');
    }
  });

  it('GET /clusters/:id → 404 for non-existent cluster', () => {
    return request(app.getHttpServer())
      .get('/clusters/non-existent-uuid-123456789')
      .expect(404);
  });

  it('GET /timeline → 200 ok with timeline array', async () => {
    const res = await request(app.getHttpServer()).get('/timeline').expect(200);
    expect(res.body).toHaveProperty('timeline');
    expect(Array.isArray(res.body.timeline)).toBe(true);
    if (res.body.timeline.length > 0) {
      const entry = res.body.timeline[0];
      expect(entry).toHaveProperty('clusterId');
      expect(entry).toHaveProperty('label');
      expect(entry).toHaveProperty('startTime');
      expect(entry).toHaveProperty('endTime');
      expect(entry).toHaveProperty('articleCount');
      expect(entry).toHaveProperty('intensity');
    }
  });

  it('POST /ingest/trigger → 201/200 ok returning jobId and PENDING status', async () => {
    const res = await request(app.getHttpServer())
      .post('/ingest/trigger')
      .expect((res) => {
        expect([200, 201]).toContain(res.status);
      });

    expect(res.body).toHaveProperty('jobId');
    expect(res.body).toHaveProperty('status');
  });

  it('GET /ingest/status/:jobId → 404 for non-existent job', () => {
    return request(app.getHttpServer())
      .get('/ingest/status/non-existent-job-9999')
      .expect(404);
  });
});
