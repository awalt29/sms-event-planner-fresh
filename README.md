# Event Planner App

A sophisticated SMS-based event planning application that helps users organize events through natural language conversations.

## Features

- **SMS-driven interface** using Twilio for seamless communication
- **AI-powered parsing** with OpenAI GPT for natural language understanding
- **Multi-user system** supporting Planners and Guests
- **Smart scheduling** with availability collection and overlap detection
- **Contact management** for saving and reusing contacts
- **Location intelligence** with venue suggestions
- **State management** for complex conversation flows
- **Calendar integration** capabilities

## Architecture

This application follows modern Python best practices with:

- **Clean separation of concerns**: Models, Services, Routes, and Utilities
- **Database abstraction**: SQLAlchemy ORM with migrations
- **Configuration management**: Environment-based settings
- **Error handling**: Comprehensive logging and error boundaries
- **Modular design**: Blueprint-based route organization
- **Testing**: Unit and integration test structure

## Project Structure

```
event_planner/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models/              # Database models
│   ├── services/            # Business logic layer
│   ├── routes/              # API endpoints
│   ├── utils/               # Helper utilities
│   └── config.py            # Configuration settings
├── migrations/              # Database migrations
├── tests/                   # Test suite
├── requirements.txt         # Dependencies
├── .env                     # Environment variables
└── run.py                   # Application entry point
```

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Initialize database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. Run the application:
```bash
python run.py
```

## Environment Variables

- `FLASK_APP`: Application entry point
- `FLASK_ENV`: Environment (development/production)
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Flask secret key
- `TWILIO_SID`: Twilio Account SID
- `TWILIO_AUTH`: Twilio Auth Token
- `TWILIO_NUMBER`: Twilio phone number
- `OPENAI_API_KEY`: OpenAI API key
- `BASE_URL`: Application base URL for webhooks

## Usage

The application communicates via SMS messages. Planners can:

1. Create new events by texting event details
2. Add guests and collect their availability
3. Receive AI-powered suggestions for venues and activities
4. Manage event logistics through natural conversation
5. Generate calendar invitations and finalize plans

## License

MIT License
# Deployment trigger Sun Aug  3 12:36:12 EDT 2025
