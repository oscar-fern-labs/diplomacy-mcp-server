#!/usr/bin/env bash
set -e
export PORT=8080
export HOST=0.0.0.0
exec uvicorn app.main:app --host "" --port ""
