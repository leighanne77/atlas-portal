.PHONY: sync-types sync-types-check test backend frontend docker-local docker-push

# --- Docker image config (override on the command line, e.g. make docker-push TAG=slice7.2) ---
AR_REGION ?= us-west1
AR_PROJECT ?= demo-project-id-12345
AR_REPO ?= atlas-portal
IMAGE_NAME ?= backend
TAG ?= $(shell git rev-parse --short HEAD)
IMAGE_URI = $(AR_REGION)-docker.pkg.dev/$(AR_PROJECT)/$(AR_REPO)/$(IMAGE_NAME):$(TAG)

# Regenerate frontend TypeScript types from Pydantic models.
# Needs frontend/node_modules/.bin/json2ts on PATH — make sure you've run
# `npm ci` in frontend/ first.
sync-types:
	.venv/bin/python scripts/sync_types.py

# CI check: regenerate and fail if the committed file differs. Catches
# forgotten regenerations before they reach main.
sync-types-check: sync-types
	@git diff --exit-code frontend/src/api/generated_types.ts || \
		(echo "ERROR: generated_types.ts is out of sync. Run 'make sync-types' and commit." && exit 1)

test:
	.venv/bin/python -m pytest tests/ -q

# Kill any stale uvicorn process holding port 8000, then start fresh.
# Addresses the Day 4 smoke-session friction.
backend:
	-pkill -f 'uvicorn.*app.main' 2>/dev/null || true
	unset ANTHROPIC_API_KEY && .venv/bin/uvicorn app.main:app --reload

# Kill any stale Vite dev server, then start fresh.
frontend:
	-pkill -f 'vite' 2>/dev/null || true
	cd frontend && npm run dev

# Local arm64 build for Apple Silicon dev iteration. Loads into the
# local Docker daemon so `docker run atlas-portal:dev` works immediately.
# Single-platform — multi-arch images can't be --load'ed, only --push'ed.
docker-local:
	docker buildx build --platform linux/arm64 -t atlas-portal:dev --load .

# Multi-arch prod build (amd64 + arm64) pushed to Artifact Registry.
# Override TAG to use a non-hash tag, e.g. `make docker-push TAG=slice7.2`.
# After push, deploy with: gcloud run services update atlas-portal \
#   --region=$(AR_REGION) --project=$(AR_PROJECT) --image=$(IMAGE_URI)
docker-push:
	@echo "Pushing $(IMAGE_URI)"
	docker buildx build --platform linux/amd64,linux/arm64 -t $(IMAGE_URI) --push .
