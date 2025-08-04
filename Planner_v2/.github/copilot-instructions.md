# Copilot Instructions for SMS Event Planner

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This is a sophisticated SMS-based event planning application that manages complex conversational workflows entirely through text messages.

## Key Architecture Principles

1. **Everyone is a Planner by Default**: All users are planners unless they have an active guest state from receiving availability/RSVP requests
2. **Per-Message Guest State Cleanup**: Guest states are cleaned up after each response message, returning users to planner mode immediately
3. **Handler Pattern**: Each workflow stage has a focused 50-100 line handler in `app/handlers/`
4. **Service Layer Separation**: Business logic is separated into services in `app/services/`
5. **Exact Message Formatting**: Follow the exact emoji and formatting patterns from CONTEXT.md screenshots

## Code Style Guidelines

- Keep handlers focused and under 100 lines
- Use the HandlerResult dataclass for consistent responses
- Follow the database model relationships defined in CONTEXT.md
- Implement proper error handling and logging
- Use the exact message templates from the visual flows

## Key Components

- **SMSRouter**: Main routing logic with "everyone is a planner by default" pattern
- **Workflow Handlers**: Stage-specific message handling (guests, dates, venues, etc.)
- **Service Layer**: Business logic for events, guests, availability, venues, AI processing
- **Database Models**: SQLAlchemy models with proper relationships and methods

When making changes, preserve the user experience described in the visual flows while maintaining clean, modular code architecture.
