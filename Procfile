web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 bot.main:app
worker: python -m bot.main
release: python migrations/001_initial.py