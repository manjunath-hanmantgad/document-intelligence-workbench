#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/artifacts"
OUTPUT="$ARTIFACT_DIR/docker_proof_output.txt"

mkdir -p "$ARTIFACT_DIR"

{
  echo "Docker proof capture"
  echo "generated_at_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo
  if ! command -v docker >/dev/null 2>&1; then
    echo "status=skip"
    echo "detail=docker command not found"
    exit 0
  fi

  echo "== docker --version =="
  docker --version
  echo

  echo "== docker compose version =="
  docker compose version
  echo

  echo "== docker compose config =="
  docker compose config
  echo

  echo "== docker compose up (detached) =="
  docker compose up -d
  echo

  echo "== docker compose ps =="
  docker compose ps
  echo

  echo "== api health =="
  curl -sS http://127.0.0.1:8005/health
  echo

  echo "== docker compose down =="
  docker compose down
} | tee "$OUTPUT"

echo "Docker proof artifact written: $OUTPUT"
