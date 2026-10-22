# Infrastructure

Deployment and CI helpers.

## `nginx/default.conf`

Reverse proxy that fronts the Django API, Django admin, static/media, and the Next.js app on a
single port. Put TLS in front (e.g. a managed load balancer or a `certbot` sidecar) for
production.

## Production checklist

- [ ] `DEBUG=False`, strong `DJANGO_SECRET_KEY`, explicit `ALLOWED_HOSTS`
- [ ] Managed PostgreSQL with point-in-time recovery (PITR) enabled
- [ ] Managed Redis (broker + cache)
- [ ] S3 bucket with versioning + lifecycle; private objects only
- [ ] Run Celery workers and beat separately from web workers
- [ ] `python manage.py collectstatic` during image build
- [ ] Enable security headers (HSTS, CSP, X-Frame-Options)
- [ ] Centralised logging + error tracking (e.g. Sentry)
- [ ] Scheduled backup job (`audit` app) + periodic restore test
- [ ] HTTPS everywhere; short-lived signed URLs for file downloads
