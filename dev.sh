#! /usr/bin/env bash
(cd src && uv run python -m uvicorn app:app --reload --port 5000 --log-level debug --lifespan on --ws-ping-timeout 5)