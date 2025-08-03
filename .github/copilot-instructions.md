<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Event Planner App - Copilot Instructions

This is a sophisticated SMS-based event planning application built with Flask and modern Python practices.

## Architecture Overview

- **Flask Application**: Web framework with Blueprint-based route organization
- **SQLAlchemy ORM**: Database abstraction with modern model design
- **Twilio Integration**: SMS communication and webhook handling
- **OpenAI Integration**: AI-powered natural language processing
- **Service Layer**: Clean separation of business logic from routes
- **Utility Modules**: Reusable helper functions for common tasks

## Key Design Patterns

1. **Application Factory Pattern**: Used in `app/__init__.py` for flexible app creation
2. **Service Layer Pattern**: Business logic separated into service classes
3. **Blueprint Organization**: Routes organized by functionality
4. **Model Inheritance**: Base model with common fields and methods
5. **Error Handling**: Comprehensive logging and graceful error responses

## Code Style Guidelines

- Use type hints for function parameters and return values
- Follow PEP 8 naming conventions
- Include docstrings for all public methods
- Use logging for debugging and error tracking
- Handle exceptions gracefully with user-friendly messages
- Prefer composition over inheritance where possible

## Key Components

### Models (`app/models/`)
- Base model with common functionality
- Relationship management with proper cascading
- JSON serialization support
- Audit fields (created_at, updated_at)

### Services (`app/services/`)
- Event management logic
- Guest management and invitation handling
- Business rules and workflow management
- Database operations abstraction

### Utils (`app/utils/`)
- Phone number normalization and validation
- SMS communication helpers
- AI/NLP processing functions
- Scheduling and overlap detection

### Routes (`app/routes/`)
- SMS webhook handling
- Dashboard and API endpoints
- Request validation and response formatting

## SMS Workflow States

The application manages complex conversation flows through the `GuestState` model:
- `awaiting_availability`: Guest needs to provide availability
- `awaiting_rsvp`: Guest needs to confirm attendance
- `awaiting_confirmation`: Final confirmation for finalized events

## AI Integration Guidelines

- Use AI for natural language parsing but validate results
- Provide fallback options when AI parsing fails
- Cache expensive AI operations when possible
- Include confidence levels in AI responses

## Testing Considerations

- Mock external services (Twilio, OpenAI) in tests
- Test SMS message parsing and response logic
- Validate phone number handling edge cases
- Test workflow state transitions

## Security Notes

- Validate all user input, especially phone numbers
- Sanitize messages before AI processing
- Use environment variables for sensitive configuration
- Implement rate limiting for SMS endpoints (future enhancement)

## Common Patterns

When adding new features:
1. Create or update models as needed
2. Implement business logic in service classes
3. Add route handlers with proper error handling
4. Include utility functions for reusable logic
5. Update tests and documentation

## Environment Variables Required

- `TWILIO_SID`: Twilio Account SID
- `TWILIO_AUTH`: Twilio Auth Token  
- `TWILIO_NUMBER`: Twilio phone number
- `OPENAI_API_KEY`: OpenAI API key
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Flask secret key
