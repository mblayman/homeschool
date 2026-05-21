# Agent Guide

This repository is a Django app for homeschool planning. Use this file as the
first stop for AI-agent work: it captures the commands, architecture, and safety
rules that are otherwise spread across the repo.

## Stack

- Python 3.13, managed with `uv`.
- Django 6 app configured from `project/settings.py`.
- SQLite is the default local database.
- Node 23 is used for Tailwind CSS and Playwright under `frontend/`.
- Sphinx documentation lives under `docs/`.

## Key Paths

- `project/`: Django project settings, URL routing, ASGI/WSGI entry points, and
  test settings.
- `homeschool/`: first-party Django apps. Each domain app keeps its models,
  views, forms, URLs, admin code, and tests together.
- `templates/`: Django templates shared by the first-party apps.
- `frontend/`: Tailwind source, Node package lockfile, and Playwright e2e tests.
- `static/`: static assets checked into the repo. Generated CSS is ignored at
  `static/site.css`.
- `docs/`: Sphinx documentation.
- `hashid_field/`: vendored package code. Keep changes here minimal and preserve
  upstream style unless the task is explicitly about this package.

## Setup

Use the repo-local examples rather than inventing environment values.

```bash
cp .env.example .env
uv sync
npm --prefix frontend i
make bootstrap
```

`make bootstrap` installs frontend dependencies, runs migrations, creates or
updates the local `matt` superuser, and enables the signup flag. The local login
created by the Makefile is `matt@example.com` with password `correcthorse`.

## Development Commands

- `make local`: run the Django web process, Huey worker, and Tailwind watcher via
  `honcho` and `Procfile`.
- `uv run manage.py migrate`: apply database migrations.
- `uv run manage.py shell`: open a Django shell.
- `npm --prefix frontend run build`: build minified Tailwind CSS into
  `static/site.css`.
- `npm --prefix frontend run watch`: watch Tailwind CSS during local development.
- `uv run pre-commit run --all-files`: run the configured django-upgrade and
  Ruff hooks.
- `make docs`: build Sphinx docs.
- `make build`: build the Docker Compose image.

## Verification Commands

Start with the narrowest check that exercises your change, then widen only as
needed.

- `uv run pytest path/to/test.py -q`: preferred focused Python test command.
- `make fcov`: fast coverage check for the full Django test suite.
- `make coverage`: slower coverage run with migrations enabled.
- `make mypy`: type-check `homeschool`, `project`, and `manage.py`.
- `npm --prefix frontend run build`: verify CSS builds after template or
  Tailwind changes.
- `npm --prefix frontend run e2e:install`: install Chromium for Playwright when
  the browser is missing.
- `bin/e2e-local`: run Playwright against a locally started app.
- `bin/e2e-docker <image-ref>`: run Playwright against a Docker image.

Tests use `project.testing_settings` from `pyproject.toml`. That switches to an
in-memory SQLite database, in-memory file storage, immediate Huey execution, and
locmem email. Pytest disables sockets by default, so do not write tests that
depend on live network access.

## Code Style

- Follow existing Django patterns in the nearest app before introducing a new
  abstraction.
- Keep app boundaries intact: domain logic should usually live in the matching
  `homeschool/<app>/` package.
- Add or update tests beside the app being changed.
- Prefer targeted changes over broad refactors.
- Use Ruff rules from `pyproject.toml`; imports are sorted by Ruff/isort.
- `.pre-commit-config.yaml` runs django-upgrade plus Ruff lint/format hooks.
- Keep mypy-compatible types when touching typed code. Do not silence type
  errors with casts or ignore comments.
- Migrations should be generated intentionally and reviewed. Do not hand-edit a
  migration unless the task specifically requires it.

## Frontend Notes

- Templates are server-rendered Django HTML using Tailwind utility classes.
- Tailwind scans `templates/**/*.html` from `frontend/tailwind.config.js`.
- If you change templates or Tailwind config, rebuild CSS with
  `npm --prefix frontend run build`.
- Keep generated frontend artifacts out of commits: `static/site.css`,
  `frontend/playwright-report/`, and `frontend/test-results/` are ignored.

## Environment And Secrets

- `.env.example` is the source for local placeholder values.
- `.tool-versions` pins local Node, Ruby, and Kamal versions for developers who
  use asdf-compatible tooling.
- `.opencode/` contains local OpenCode plugin dependencies. Do not treat it as
  application source or edit it for app changes.
- Never commit `.env`, database files, media files, generated static files, or
  Playwright output.
- Production-like settings in `project/settings.py` expect real AWS, Stripe,
  Sentry, and email configuration. Use the test settings or `.env.example`
  placeholders for local and automated work.
- The runtime Docker image installs dependencies into `/app/.venv` during build;
  it does not include `uv` at runtime.

## Agent Workflow

1. Read the nearest models, forms, views, URLs, templates, and tests before
   editing a feature.
2. Reproduce or cover behavior with a focused test when changing Python logic.
3. Make the smallest coherent change that satisfies the task.
4. Run focused tests first, then `make fcov` and `make mypy` when the change is
   not trivially local.
5. For user-visible web changes, run the app and verify the affected page or
   flow manually, using Playwright when practical.
6. Report any pre-existing failures separately rather than hiding them in the
   change.
7. Shut down any long-running dev processes you started (for example gunicorn,
   honcho, Tailwind watchers, or Huey workers) after building or testing so
   they do not block later runs.
8. Keep code coverage at 100%; add or update tests for every new or changed
   Python line before finishing.

## Do Not

- Do not add new dependencies unless the task explicitly requires them.
- Do not make external service calls from tests.
- Do not change deployment, billing, email, or storage behavior without a clear
  task and focused verification.
- Do not commit generated artifacts or local state.
- Do not weaken tests, reduce coverage expectations, or bypass type/lint errors.
