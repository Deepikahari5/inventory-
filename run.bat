@echo off
cd /d "%~dp0"
if not exist venv (
  python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
if not exist .env (
  copy .env.example .env
  echo Edit .env with your MySQL credentials, then run this file again.
  pause
  exit /b
)
alembic upgrade head
python -m scripts.seed_data
uvicorn app.main:app --reload
