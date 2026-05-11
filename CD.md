# Continuous Delivery Checklist

Use this as a working checklist for production-only CD. Edit freely and mark items as you decide.

## 1) CD Goals & Guardrails

- [x] Define what "ready for production" means:
  - All automated tests pass, including integration tests (to be created).
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
  - Add `pre-commit` to CI so lint/style checks run consistently.
  - Rationale: improves consistency for future AI-assisted contributions.
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
- [ ] Resolve non-interactive secrets access with current 1Password tier:
  - Basic/personal 1Password tiers may not support service accounts for CI.
  - Choose one path:
    - Keep 1Password as sole secret store and run deploys manually from local machine.
    - Store deploy secrets in GitHub Actions/Environment secrets for full automation.
    - Upgrade 1Password plan to one with service accounts, then use `OP_SERVICE_ACCOUNT_TOKEN` in GitHub Actions.
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

- [ ] Choose non-interactive secrets path for GitHub Actions:
  - Option A: Store deploy secrets in GitHub Environment secrets (fastest path to full automation).
  - Option B: Upgrade 1Password tier and use service-account-based access.
- [ ] Document final decision in Section 7 and remove unused options.

### Step 1 - Harden CI Gates (no deploy changes yet)

- [ ] Update `.github/workflows/tests.yaml` to run `pre-commit` in CI.
- [ ] Keep required checks as: mypy, tests, docs.
- [ ] Add initial integration test suite scaffolding and run it in CI (can start with one high-value integration flow).
- [ ] Confirm CI stays green on `main` after these additions.

### Step 2 - Add Main-Only Docker Build Validation

- [ ] Add/extend workflow so Docker build runs on pushes to `main` only.
- [ ] Keep PR pipeline fast by skipping Docker build on PR events.
- [ ] Ensure Docker build failure blocks deploy stages.

### Step 3 - Create Production Deploy Workflow

- [ ] Add `.github/workflows/deploy.yml` dedicated to production deploys.
- [ ] Trigger workflow on push to `main`.
- [ ] Add workflow concurrency (single in-flight production deploy).
- [ ] Install required tooling in workflow (`uv`, Docker/Kamal dependencies).
- [ ] Authenticate non-interactively using the secrets approach chosen in Step 0.
- [ ] Run `kamal deploy` from CI.

### Step 4 - Add Post-Deploy Verification Gates

- [ ] Add smoke check step(s) after `kamal deploy`:
  - Homepage responds.
  - Login flow endpoint responds.
  - One critical app flow responds.
- [ ] Add worker verification step:
  - Queue lightweight job.
  - Verify job completion.
- [ ] Configure workflow to fail if any check fails.

### Step 5 - Validate Failure Signaling + Manual Recovery

- [ ] Trigger a safe failure in a test branch/copy of workflow to verify email notifications reach your inbox.
- [ ] Confirm failed deploy leaves enough context in GitHub Actions logs for incident handling.
- [ ] Validate manual rollback procedure with `kamal rollback` in a controlled test.

### Step 6 - Go Live and Enforce

- [ ] Enable deploy workflow in production mode for all merges/pushes to `main`.
- [ ] Confirm first live automated deploy succeeds end-to-end.
- [ ] Remove any obsolete manual deploy steps from personal routine.

### Step 7 - Stabilization After Launch (first 2-4 weeks)

- [ ] Track deploy outcomes and fix any flaky checks immediately.
- [ ] Expand integration test coverage incrementally around recent incident-prone areas.
- [ ] Review pipeline duration and optimize only where needed (without removing safety gates).
