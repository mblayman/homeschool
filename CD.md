# Continuous Delivery Checklist

Use this as a working checklist for production-only CD. Edit freely and mark items as you decide.

## 1) CD Goals & Guardrails

- [x] Define what "ready for production" means:
  - All automated tests pass, including the main-only Playwright E2E suite.
  - Production Docker image build completes successfully.
- [x] Decide release frequency and automation target:
  - Release on every merge to `main`.
  - Target a fully automated, hands-off production CD pipeline.
- [x] Decide acceptable deploy window(s) and blackout periods:
  - No deploy window restrictions.
  - No blackout periods.
  - Rationale: `kamal deploy` supports zero-downtime deploys, and migrations will be written to minimize disruption.
- [x] Define ownership for deploys and incident response:
  - Deploys are executed by automation.
  - The production deploy pipeline runs in GitHub Actions.
  - Incident response starts from GitHub Actions failure notifications sent to your inbox.

## 2) Git & Branch Policy

- [x] Make `main` the only production deploy source:
  - `main` is the only production deploy source.
  - Enforce this in the GitHub Actions deploy workflow trigger/config.
- [x] Decide whether pull requests are required for `main`:
  - Pull requests are not required for this solo app.
  - Direct pushes to `main` are allowed when needed.
- [x] Require passing checks before merge:
  - All checks must be passing before merge.
- [x] Decide merge strategy and keep it consistent:
  - Always use `squash` merges.
- [x] Decide release-notes convention:
  - No release notes process.
  - Use `git log` as the source of release history.

## 3) CI Quality Gates (Pre-Deploy)

- [x] Keep and expand required CI checks:
  - Keep existing required checks: type checks, tests, docs build.
  - Use `pre-commit.ci` for lint/style checks (no duplicate pre-commit job in GitHub Actions).
  - Rationale: keeps enforcement consistent without duplicating CI runtime.
- [x] Define E2E gate strategy:
  - Use Node Playwright for browser-based E2E coverage.
  - Run E2E checks on pushes to `main` only.
  - Run E2E against the built Docker image for production-like configuration signal.
  - Use Django admin login (`/office/`) for authenticated E2E sessions (no custom auth bypass endpoint).
- [x] Decide container build policy in CI:
  - Run container builds on `main` only.
  - Do not require container builds on PRs.
  - Rationale: saves CI time; most changes are unlikely to affect Docker build behavior.
- [x] Decide test runtime/flakiness policy:
  - No explicit test runtime budget for now.
  - Flaky tests are not acceptable and will be fixed as they appear.
  - No special CI pipeline handling for flaky tests.
- [x] Define dependency/security scanning policy:
  - Use Dependabot for dependency updates and baseline security handling.
  - Keep Dependabot enabled as part of ongoing CI/CD hygiene.

## 4) Build Artifact Strategy

- [x] Confirm build artifact strategy:
  - All build artifact strategy requirements are handled by Kamal defaults.
  - This includes image build/tag/deploy behavior needed for production CD.

## 5) Production Deploy Workflow

- [x] Create a dedicated deploy workflow in GitHub Actions.
- [x] Trigger deploy on merge to `main`.
- [x] Add workflow concurrency so only one deploy runs at a time.
- [x] Run `kamal deploy` from CI with non-interactive authentication.
- [x] Decide deploy metadata storage approach:
  - Default GitHub Actions logs are sufficient for now.
  - No separate/special deploy metadata storage is required at this time.

## 6) Database Migration Safety

- [x] Decide migration approach:
  - Keep the entrypoint migration approach.
- [x] Define schema/app compatibility policy:
  - No explicit compatibility rules are required.
- [x] Define migration rollback expectations:
  - Rollback is manual when needed.
- [x] Decide handling for migration failure mid-deploy:
  - Treat failures as incidents via email notifications.
  - You will handle incident response directly.
  - No additional runbook documentation is required at this time.

## 7) Secrets & Environment Management

- [x] Inventory required production secrets:
  - Use the existing secret set referenced in `.kamal/secrets` as the production baseline.
  - Continue managing app, AWS, Stripe, and monitoring credentials in 1Password.
- [x] Resolve non-interactive secrets access with current 1Password tier:
  - Decision: store deploy secrets in GitHub Actions repository-level secrets for full automation.
  - Rationale: basic/personal 1Password tier does not provide a practical service-account path for non-interactive CI/CD.
  - Preserve local-machine deploy support with 1Password-based secret retrieval.
  - Accept two sources of truth for runtime access (GitHub Actions + 1Password) and manage synchronization intentionally.
  - Secret resolution behavior: prefer `CI_`-prefixed environment variable values first; fall back to `op read` when those vars are not set.
- [x] Define secret rotation policy:
  - Rotate automation credentials (GitHub or 1Password service-account token) on a schedule and after security events.
  - Rotate underlying production secrets in 1Password as needed.
- [x] Define access model for production secrets:
  - You retain update/admin control of secrets in 1Password.
  - If using CI automation, restrict CI credentials to least privilege/read-only access where possible.

## 8) Post-Deploy Verification

- [x] Add smoke checks after deploy:
  - Keep checks short and focused (homepage, login, critical flow).
- [x] Add a worker health check:
  - Queue a lightweight job and verify completion.
- [x] Define post-deploy pass/fail policy:
  - No threshold model.
  - All defined post-deploy checks must pass.
- [x] Fail deployment pipeline when checks fail.

## Implementation Plan

Use this as the concrete execution sequence. Complete each step in order so production CD is reliable at every stage.

### Step 0 - Resolve CI Secrets Path (blocking decision)

- [x] Choose non-interactive secrets path for GitHub Actions:
  - Store deploy secrets in GitHub Actions repository-level secrets.
- [x] Document final decision in Section 7 and remove unused options.
- [x] Preserve local deploy workflow:
  - Keep `kamal deploy` from dev machine working with 1Password via `op`.
  - Ensure secret resolution prefers `CI_`-prefixed env vars first, then falls back to `op`.

### Step 1 - Harden CI Gates (no deploy changes yet)

- [x] Decide pre-commit enforcement path:
  - Use `pre-commit.ci` as the source of truth for pre-commit checks.
  - Do not duplicate pre-commit checks in `.github/workflows/tests.yaml`.
- [ ] Keep required checks as: mypy, tests, docs.
- [ ] Confirm CI stays green on `main` after this cleanup.

### Step 2 - Add Main-Only Docker Build Validation

- [ ] Add/extend workflow so Docker build runs on pushes to `main` only.
- [ ] Keep PR pipeline fast by skipping Docker build on PR events.
- [ ] Ensure this build path is the same image build process used by Kamal.
- [ ] Ensure Docker build failure blocks downstream deploy stages.

### Step 3 - Add Main-Only Playwright E2E Validation

- [ ] Add Playwright scaffolding under `frontend` (Node Playwright test runner + config).
- [ ] Define initial E2E test set (3-5 critical flows).
- [ ] Run E2E on pushes to `main` only.
- [ ] Run E2E against the exact image artifact produced by Step 2.
- [ ] Use Django admin login flow (`/office/`) for authenticated E2E tests.
- [ ] Seed/upsert a deterministic staff user for E2E before Playwright execution.
- [ ] Upload Playwright artifacts (trace/screenshot/video) on failure.
- [ ] Ensure E2E failure blocks downstream deploy stages.

### Step 4 - Create Production Deploy Workflow

- [ ] Add `.github/workflows/deploy.yml` dedicated to production deploys.
- [ ] Trigger workflow on push to `main`.
- [ ] Add workflow concurrency (single in-flight production deploy).
- [ ] Install required tooling in workflow (`uv`, Docker/Kamal dependencies).
- [ ] Authenticate non-interactively using the secrets approach chosen in Step 0.
- [ ] Gate deploy job on successful main-only Docker + E2E validation.
- [ ] Run `kamal deploy` from CI.

### Step 5 - Add Post-Deploy Verification Gates

- [ ] Add smoke check step(s) after `kamal deploy`:
  - Homepage responds.
  - Login flow endpoint responds.
  - One critical app flow responds.
- [ ] Add worker verification step:
  - Queue lightweight job.
  - Verify job completion.
- [ ] Configure workflow to fail if any check fails.

### Step 6 - Validate Failure Signaling + Manual Recovery

- [ ] Trigger a safe failure in a test branch/copy of workflow to verify email notifications reach your inbox.
- [ ] Confirm failed deploy leaves enough context in GitHub Actions logs for incident handling.
- [ ] Validate manual rollback procedure with `kamal rollback` in a controlled test.

### Step 7 - Go Live and Enforce

- [ ] Enable deploy workflow in production mode for all merges/pushes to `main`.
- [ ] Confirm first live automated deploy succeeds end-to-end.
- [ ] Remove any obsolete manual deploy steps from personal routine.

### Step 8 - Stabilization After Launch (first 2-4 weeks)

- [ ] Track deploy outcomes and fix any flaky checks immediately.
- [ ] Expand Playwright E2E coverage incrementally around recent incident-prone areas.
- [ ] Review pipeline duration and optimize only where needed (without removing safety gates).
