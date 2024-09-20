FROM node:18 AS nodejs

WORKDIR /app

COPY package.json package-lock.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm install --loglevel verbose

COPY frontend frontend/
COPY templates templates/

RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

# weasyprint deps: libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.4.7 /uv /bin/uv
COPY --from=klakegg/hugo:0.101.0 /usr/lib/hugo/hugo /bin/hugo

WORKDIR /app

RUN addgroup --gid 222 --system app \
    && adduser --uid 222 --system --group app

RUN mkdir -p /app && chown app:app /app

COPY --chown=app:app pyproject.toml uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY --chown=app:app . /app/

COPY --from=nodejs /app/static/site.css static/

RUN python manage.py collectstatic --noinput

RUN sphinx-build -M html "docs" "docs/_build" -W -b dirhtml \
    && python -m whitenoise.compress docs/_build/html

RUN hugo \
    && python -m whitenoise.compress blog_out

USER app

EXPOSE 8000

CMD ["gunicorn", "project.wsgi", "--workers=2", "--log-file=-", "--bind=0.0.0.0:8000"]
