# API rate limits

## Approved scope

- Configure SlowAPI in the shared `AppFactory`, using existing `CACHE_DB_URI`.
- Add shared `Settings.API_RATE_LIMIT`, defaulting to `120/minute`.
- Share a fixed-window allowance per client IP across endpoints and workers.
- Add `AppFactory.add_router(..., rate_limit_exempt=True)` and use it only for
  the Open Access API's `ServiceRouter`.
- Return HTTP 429 with `Retry-After` when the allowance is exhausted.
- Keep storage compatible with Valkey using the Redis protocol. Translate the
  existing legacy `keydb://` URI scheme for SlowAPI without changing cachedb.
- Add SlowAPI to root and service dependency manifests; update only the root lockfile.
- No token support, new Python modules, cache-manager changes, or Docker changes.

## Validation

Review the diff, parse edited Python and TOML, check Black/isort formatting,
and validate the root Poetry lockfile. Run tests only when explicitly requested.

Deployment must configure Uvicorn to trust only the relevant proxy addresses
for client IP identification. Use a `redis://` or `rediss://` connection URL
when switching cachedb to Valkey; no server-specific limiter changes are needed.
