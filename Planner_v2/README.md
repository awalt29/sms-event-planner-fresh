# SMS Event Planner - Rebuilt with Clean Architecture

A sophisticated SMS-based event planning application that manages complex conversational workflows entirely through text messages. The system handles dual user roles (planners and guests) with seamless state transitions, natural language processing, AI-powered venue suggestions, and intelligent coordination workflows.

## Architecture Overview

This rebuild implements a clean, modular architecture with:

- **Everyone is a Planner by Default**: Simplified role management with temporary guest state overrides
- **Handler Pattern**: Focused 50-100 line handlers for each workflow stage
- **Service Layer**: Business logic separation for maintainability
- **Per-Message Guest State Cleanup**: Immediate return to planner mode after guest responses

## Project Structure

```
app/
├── models/          # SQLAlchemy database models
├── services/        # Business logic services
├── handlers/        # Workflow stage handlers
├── routes/          # Flask route handlers
└── utils/           # Utility functions

config/              # Configuration files
migrations/          # Database migrations
tests/              # Test suite
```

## Key Features

- Natural language date parsing
- AI-powered venue suggestions with Google Maps integration
- Real-time availability coordination
- Intelligent time overlap calculation
- Contact management with previous guest selection
- RSVP tracking with automatic notifications

## Setup Instructions

1. Create virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables (see `.env.example`)
5. Initialize database: `flask db upgrade`
6. Run the application: `flask run`

## Environment Variables

```
FLASK_APP=app
FLASK_ENV=development
DATABASE_URL=sqlite:///planner.db
TWILIO_SID=your_twilio_sid
TWILIO_AUTH=your_twilio_auth_token
TWILIO_NUMBER=your_twilio_phone_number
OPENAI_API_KEY=your_openai_api_key
```

## Testing

Run tests with: `pytest tests/`

## Documentation

See `CONTEXT.md` for complete architecture documentation and visual workflows.
