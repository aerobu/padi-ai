# Security Rotation Checklist — 2026-04-20

## Scope

The file `apps/api/.env` contained development credentials that must be rotated out-of-band before any non-local deployment. Decision: keep git history (repo is private, solo-dev), rotate credentials.

## Credentials to rotate

(Each KEY from `apps/api/.env` is listed below — values are REDACTED — with a checkbox for rotation status.)

### App Settings
- [ ] `APP_NAME` — non-sensitive label; no rotation needed unless branding changes
- [ ] `APP_VERSION` — non-sensitive; no rotation needed
- [ ] `ENVIRONMENT` — non-sensitive flag; no rotation needed
- [ ] `DEBUG` — non-sensitive flag; set to `false` in production

### Database
- [ ] `DATABASE_URL` — rotate Postgres password (update in Postgres, docker-compose, and any deployed env)
- [ ] `DATABASE_POOL_MIN` — non-sensitive tuning value; no rotation needed
- [ ] `DATABASE_POOL_MAX` — non-sensitive tuning value; no rotation needed

### Redis
- [ ] `REDIS_URL` — rotate Redis auth token if AUTH is enabled in production
- [ ] `REDIS_POOL_MIN` — non-sensitive tuning value; no rotation needed
- [ ] `REDIS_POOL_MAX` — non-sensitive tuning value; no rotation needed

### Auth0
- [ ] `AUTH0_SECRET` — regenerate (32-byte random); update in Auth0 dashboard and deployed env
- [ ] `AUTH0_BASE_URL` — non-sensitive URL; update for each environment
- [ ] `AUTH0_ISSUER_BASE_URL` — non-sensitive URL; verify per environment
- [ ] `AUTH0_CLIENT_ID` — rotate/regenerate application client ID in Auth0 dashboard
- [ ] `AUTH0_CLIENT_SECRET` — regenerate in Auth0 dashboard; store in secrets manager
- [ ] `AUTH0_AUDIENCE` — non-sensitive identifier; verify per environment

### LLM Routing (COPPA-compliant)
- [ ] `LLM_ROUTING__TUTOR` — non-sensitive model identifier; no rotation needed
- [ ] `LLM_ROUTING__ASSESSMENT` — non-sensitive model identifier; no rotation needed
- [ ] `LLM_ROUTING__QUESTION_GEN` — non-sensitive model identifier; no rotation needed
- [ ] `LLM_ROUTING__ADMIN` — non-sensitive model identifier; no rotation needed

### Cloud LLM APIs
- [ ] `ANTHROPIC_API_KEY` — regenerate in Anthropic console; store in secrets manager
- [ ] `OPENAI_API_KEY` — regenerate in OpenAI dashboard; store in secrets manager

### AWS
- [ ] `AWS_REGION` — non-sensitive config; no rotation needed
- [ ] `AWS_ACCESS_KEY_ID` — rotate IAM access key in AWS console; use least-privilege role
- [ ] `AWS_SECRET_ACCESS_KEY` — rotate together with AWS_ACCESS_KEY_ID
- [ ] `AWS_S3_BUCKET` — non-sensitive bucket name; no rotation needed

### Stripe (MMP stage)
- [ ] `STRIPE_SECRET_KEY` — rotate in Stripe dashboard (Developers → API keys)
- [ ] `STRIPE_PUBLISHABLE_KEY` — rotate together with STRIPE_SECRET_KEY (publishable keys pair with secret keys)
- [ ] `STRIPE_WEBHOOK_SECRET` — regenerate webhook endpoint signing secret in Stripe dashboard

### API Configuration
- [ ] `API_HOST` — non-sensitive; no rotation needed
- [ ] `API_PORT` — non-sensitive; no rotation needed
- [ ] `CORS_ORIGINS` — non-sensitive; update per environment

### Ollama
- [ ] `OLLAMA_BASE_URL` — non-sensitive URL; update per environment
- [ ] `OLLAMA_DEFAULT_MODEL` — non-sensitive model identifier; no rotation needed
- [ ] `OLLAMA_TUTOR_MODEL` — non-sensitive model identifier; no rotation needed
- [ ] `OLLAMA_ASSESSMENT_MODEL` — non-sensitive model identifier; no rotation needed

### Knowledge Tracing
- [ ] `BKT_GUESS_PROB` — non-sensitive tuning value; no rotation needed
- [ ] `BKT_SLIP_PROB` — non-sensitive tuning value; no rotation needed
- [ ] `BKT_LEARNING_RATE` — non-sensitive tuning value; no rotation needed

### Logging
- [ ] `LOG_LEVEL` — non-sensitive config; no rotation needed
- [ ] `LOG_FORMAT` — non-sensitive config; no rotation needed

## Priority rotation targets (actual secrets)

In order of urgency before any non-local deployment:

1. `AUTH0_CLIENT_SECRET`
2. `AUTH0_SECRET`
3. `ANTHROPIC_API_KEY`
4. `OPENAI_API_KEY`
5. `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
6. `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET`
7. `DATABASE_URL` (Postgres password component)

## After rotation

Once all secrets above are rotated and updated in your secrets manager / deployment environment:

```
git rm SECURITY-ROTATION-2026-04-20.md && git commit -m "security: remove rotation checklist after credential rotation complete"
```
