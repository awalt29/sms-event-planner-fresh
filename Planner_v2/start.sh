#!/bin/bash
# Startup script for Railway deployment
set -e

echo "Starting SMS Event Planner with Gunicorn..."
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Files in current directory:"
ls -la

# Activate virtual environment if it exists
if [ -d "/opt/venv" ]; then
    source /opt/venv/bin/activate
    echo "Virtual environment activated"
    echo "Python path: $(which python)"
fi

# Check if wsgi.py exists
if [ -f "wsgi.py" ]; then
    echo "Found wsgi.py file"
else
    echo "ERROR: wsgi.py file not found in $(pwd)"
    exit 1
fi

# Run database migrations/setup
echo "Initializing database..."
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --log-level info --access-logfile - --error-logfile -
