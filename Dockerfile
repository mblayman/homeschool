FROM node:23 AS nodejs

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm install --loglevel verbose

COPY frontend frontend/
COPY templates templates/

RUN npm --prefix frontend run build

FROM python:3.13-slim AS python_deps

COPY --from=ghcr.io/astral-sh/uv:0.4.7 /uv /bin/uv

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/cache/debconf/* /var/log/apt/* /var/log/dpkg.log

COPY pyproject.toml uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MALLOC_ARENA_MAX=2 \
    VIRTUAL_ENV=/app/.venv \
    PATH=/app/.venv/bin:$PATH

# weasyprint deps: libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/cache/debconf/* /var/log/apt/* /var/log/dpkg.log

WORKDIR /app

RUN addgroup --gid 222 --system app \
    && adduser --uid 222 --system --group app

# Clean up annoying font errors of `Fontconfig error: No writable cache directories`
RUN chown -R app:app /usr/local/share/fonts /var/cache/fontconfig \
    && su app -s /bin/sh -c "fc-cache --really-force"

RUN mkdir -p /app && chown app:app /app

COPY --from=python_deps /app/.venv /app/.venv

COPY --chown=app:app . /app/

COPY --from=nodejs /app/static/site.css static/

# Some configuration is needed to make Django happy, but these values have no
# impact to collectstatic so we can use dummy values.
RUN \
    AWS_ACCESS_KEY_ID=a-secret-to-everybody \
    AWS_SECRET_ACCESS_KEY=a-secret-to-everybody \
    DJSTRIPE_WEBHOOK_SECRET=whsec_asecrettoeverybody \
    DJSTRIPE_WEBHOOK_VALIDATION='' \
    HASHID_FIELD_SALT=a-secret-to-everybody \
    SECRET_KEY=a-secret-to-everybody \
    SENTRY_ENABLED=off \
    SENTRY_DSN=dsn_example \
    STRIPE_LIVE_MODE=off \
    STRIPE_LIVE_SECRET_KEY=sk_live_a-secret-to-everybody \
    STRIPE_TEST_SECRET_KEY=sk_test_a-secret-to-everybody \
    STRIPE_TEST_PUBLISHABLE_KEY=pk_test_a-secret-to-everybody \
    python manage.py collectstatic --noinput

RUN sphinx-build -M html "docs" "docs/_build" -W -b dirhtml \
    && python -m whitenoise.compress docs/_build/html

USER app

ENTRYPOINT ["/app/bin/docker-entrypoint"]
EXPOSE 8000
CMD ["/app/bin/server"]
