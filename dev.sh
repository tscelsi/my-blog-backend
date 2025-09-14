#! /usr/bin/env bash
uv run uvicorn app:app \
  --app-dir src \
  --reload \
  --port 5000 \
  --log-level debug \
  --lifespan on \
  --ws-ping-timeout 5 \
  --env-file .env