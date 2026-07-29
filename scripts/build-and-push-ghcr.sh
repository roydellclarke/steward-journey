#!/usr/bin/env bash
# Build and push the StewardPath frontend and backend images to GHCR.
#
# Prereqs (one time):
#   1. Create a GitHub Personal Access Token (classic) with `write:packages`.
#   2. Log in:  echo "$GHCR_TOKEN" | docker login ghcr.io -u roydellclarke --password-stdin
#
# Usage:
#   ./scripts/build-and-push-ghcr.sh              # builds+pushes v0.2.0 (+ git sha)
#   VERSION=v0.3.0 ./scripts/build-and-push-ghcr.sh
#   PUSH=false ./scripts/build-and-push-ghcr.sh   # build only, no push (dry run)
set -euo pipefail

# ---- Config (override via env) --------------------------------------------
OWNER="${OWNER:-roydellclarke}"
REGISTRY="ghcr.io/${OWNER}"
VERSION="${VERSION:-v0.3.0}"                 # semver tag; never :latest (rollback safety)
SITE_URL="${SITE_URL:-https://stewardpathfinder.com}"
API_URL="${API_URL:-https://api.stewardpathfinder.com}"
PUSH="${PUSH:-true}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GIT_SHA="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo nogit)"

FRONTEND_IMG="${REGISTRY}/stewardpath-frontend"
BACKEND_IMG="${REGISTRY}/stewardpath-backend"

echo "Registry : ${REGISTRY}"
echo "Version  : ${VERSION}  (+ sha ${GIT_SHA})"
echo "Site URL : ${SITE_URL}"
echo "API URL  : ${API_URL}"
echo "Push     : ${PUSH}"
echo

# ---- Backend ---------------------------------------------------------------
echo ">> Building backend"
docker build \
  -t "${BACKEND_IMG}:${VERSION}" \
  -t "${BACKEND_IMG}:${VERSION}-${GIT_SHA}" \
  "${ROOT}/backend"

# ---- Frontend (NEXT_PUBLIC_* are compiled in at build time) ----------------
echo ">> Building frontend"
docker build \
  --build-arg "NEXT_PUBLIC_SITE_URL=${SITE_URL}" \
  --build-arg "NEXT_PUBLIC_API_BASE_URL=${API_URL}" \
  -t "${FRONTEND_IMG}:${VERSION}" \
  -t "${FRONTEND_IMG}:${VERSION}-${GIT_SHA}" \
  "${ROOT}/frontend"

if [ "${PUSH}" = "true" ]; then
  echo ">> Pushing images"
  docker push "${BACKEND_IMG}:${VERSION}"
  docker push "${BACKEND_IMG}:${VERSION}-${GIT_SHA}"
  docker push "${FRONTEND_IMG}:${VERSION}"
  docker push "${FRONTEND_IMG}:${VERSION}-${GIT_SHA}"
  echo
  echo "Pushed:"
  echo "  ${BACKEND_IMG}:${VERSION}"
  echo "  ${FRONTEND_IMG}:${VERSION}"
else
  echo ">> PUSH=false, built locally only. Images:"
  echo "  ${BACKEND_IMG}:${VERSION}"
  echo "  ${FRONTEND_IMG}:${VERSION}"
fi
