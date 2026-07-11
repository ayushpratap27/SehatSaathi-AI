# SehatSaathi-AI — Production Deployment Checklist

## Security

- [ ] Change `SECRET_KEY` to a cryptographically strong random value (`openssl rand -hex 32`)
- [ ] Set `GEMINI_API_KEY` from environment (never commit to source)
- [ ] Use PostgreSQL (`postgresql+asyncpg://`) instead of SQLite in production
- [ ] Use a dedicated Redis instance with password authentication
- [ ] Configure HTTPS via Nginx + Let's Encrypt (Certbot)
- [ ] Review `ALLOWED_ORIGINS` — restrict to your frontend domain only
- [ ] Enable rate limiting (add `slowapi` middleware to `/auth/login` and `/rag/chat`)
- [ ] Rotate all secrets (DB passwords, API keys) if they were ever committed
- [ ] Run `alembic upgrade head` on first deployment (not `init_db()`)
- [ ] Ensure `DEBUG=false` and `ENV=production`

## Database

- [ ] Create a dedicated PostgreSQL user with minimal permissions
- [ ] Enable automated daily backups (pgdump + S3/GCS)
- [ ] Test backup restoration procedure
- [ ] Enable WAL archiving for point-in-time recovery
- [ ] Add database connection pooling (pgBouncer) for high traffic

## Performance

- [ ] Configure Redis with `maxmemory` policy (`allkeys-lru`)
- [ ] Enable Nginx gzip compression (already in `nginx.conf`)
- [ ] Set `--workers 4` (or `(2 * CPUs) + 1`) in the uvicorn CMD
- [ ] Add CDN for static frontend assets
- [ ] Enable HTTP/2 in Nginx
- [ ] Monitor slow database queries with `pg_stat_statements`

## Deployment

- [ ] Use multi-stage Docker builds (already configured)
- [ ] Pin all Docker image versions (e.g., `postgres:16.2-alpine` not `16-alpine`)
- [ ] Store Docker images in a private registry (ECR, GCR, GHCR)
- [ ] Use Kubernetes or ECS for container orchestration in production
- [ ] Configure rolling deployments (zero-downtime)
- [ ] Set resource limits (`mem_limit`, `cpus`) in docker-compose.prod.yml
- [ ] Configure log aggregation (Loki, CloudWatch, or ELK)

## Monitoring

- [ ] Set up uptime monitoring for `/health` and `/ready`
- [ ] Configure alerts for high error rates (Grafana + Prometheus, or Datadog)
- [ ] Monitor Gemini API latency and error rates
- [ ] Track database connection pool saturation
- [ ] Set up Sentry (or equivalent) for exception tracking

## Scaling

- [ ] Frontend is stateless — safe to run multiple replicas behind a load balancer
- [ ] Backend sessions are JWT-based (stateless) — safe to horizontally scale
- [ ] FAISS indexes are file-based — shared NFS or object storage needed for multi-instance
- [ ] Consider migrating FAISS to Qdrant/Weaviate for production vector search

## Legal / Compliance

- [ ] Add Privacy Policy page to frontend
- [ ] Add Terms of Service page
- [ ] Implement data deletion (GDPR right-to-erasure) endpoint
- [ ] Ensure medical disclaimer is prominent on all AI-generated pages
- [ ] Review HIPAA/DISHA compliance requirements if handling real patient data
- [ ] Implement audit log retention policy (PII purging after N days)

## Post-deployment Verification

- [ ] `GET /health` returns 200
- [ ] `GET /ready` returns 200 with `database: ok`
- [ ] Frontend loads correctly at `https://your-domain.com`
- [ ] Register a test user and complete the full upload → analysis → chat flow
- [ ] Verify JWT refresh works (wait for access token to expire, confirm auto-refresh)
- [ ] Confirm uploads are stored in the correct directory / object storage
- [ ] Verify Redis caching is active (`redis-cli monitor`)
