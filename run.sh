#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Edit .env with your MySQL credentials, then run this script again."
  exit 0
fi
alembic upgrade head
python -m scripts.seed_data
uvicorn app.main:app --reload
