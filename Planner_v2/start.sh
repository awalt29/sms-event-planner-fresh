#!/bin/bash
# Startup script for Railway deployment
set -e

echo "Starting SMS Event Planner with Gunicorn..."

# Activate virtual environment if it exists
if [ -d "/opt/venv" ]; then
    source /opt/venv/bin/activate
    echo "Virtual environment activated"
fi

# Run database migrations/setup
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"

# Start Gunicorn
exec gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --log-level info --access-logfile - --error-logfile -
