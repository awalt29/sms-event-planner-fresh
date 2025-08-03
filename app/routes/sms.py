from flask import Blueprint, request, current_app
from twilio.twiml.messaging_response import MessagingResponse
from app.models import db, Planner, Event, Contact, Guest, GuestState, Availability
from app.utils.sms import create_twiml_response, send_sms
from app.utils.phone import normalize_phone, format_phone_display
from app.utils.ai import parse_event_input, parse_availability, suggest_venues, is_broad_activity
from app.services.event_service import EventService
from app.services.guest_service import GuestService
from datetime import datetime, date, time
import logging
import json
import traceback

logger = logging.getLogger(__name__)

sms_bp = Blueprint("sms", __name__)


@sms_bp.route("/incoming", methods=["POST"])
def handle_incoming_sms():
    """
    Handle incoming SMS messages from Twilio webhook.
    """
    try:
        # Get message details from Twilio
        from_number = request.form.get('From', '')
        message_body = request.form.get('Body', '').strip()
        to_number = request.form.get('To', '')
        
        logger.info(f"Incoming SMS from {from_number}: {message_body}")
        
        if not from_number or not message_body:
            logger.error("Missing required SMS parameters")
            return create_twiml_response("Sorry, there was an error processing your message.").str
        
        # Normalize phone number
        normalized_phone = normalize_phone(from_number)
        
        # Create TwiML response object
        resp = MessagingResponse()
        
        # NEW APPROACH: Message-driven state management
        # Everyone is a planner by default, guest states are temporary and message-driven
        
        # Check for active guest state first (temporary state from incoming invitations)
        guest_state = GuestState.query.filter_by(phone_number=normalized_phone).first()
        
        if guest_state:
            # User has active guest obligations - handle as guest until resolved
            handle_guest_message(normalized_phone, message_body, resp)
        else:
            # No active guest state - check if user exists as planner or create new planner
            planner = Planner.query.filter_by(phone_number=normalized_phone).first()
            
            if planner:
                # Existing planner - handle as planner
                handle_planner_message(planner, message_body, resp)
            else:
                # New user - create planner account and start onboarding
                handle_new_user(normalized_phone, message_body, resp)
        
        return str(resp)
        
    except Exception as e:
        logger.error(f"Error handling incoming SMS: {e}")
        resp = MessagingResponse()
        resp.message("Sorry, there was an error processing your message. Please try again later.")
        return str(resp)


def create_guest_collection_message(planner: Planner) -> str:
    """Create the initial guest collection message with previous contacts."""
    # Get previous contacts for this planner
    contacts = Contact.query.filter_by(planner_id=planner.id).order_by(Contact.name).all()
    
    message = "Who's coming?\n\n"
    message += "Reply with guest names and phone numbers (e.g. 'John Doe, 123-456-7890') or select previous contacts (e.g. '1,2').\n\n"
    
    if contacts:
        message += "Previous contacts:\n"
        for i, contact in enumerate(contacts, 1):
            message += f"{i}. {contact.name} ({contact.phone_number})\n"
        message += "\n"
    
    message += "Add one guest at a time.\n\n"
    message += "💡 Commands:\n"
    message += "- 'Add guest'\n"
    message += "- 'Remove contact'\n"
    message += "- 'Restart'"

    return message


def handle_planner_message(planner: Planner, message: str, resp: MessagingResponse):
    """
    Handle messages from registered planners.
    """
    try:
        message_lower = message.lower().strip()
        
        # Check if planner name is missing - collect it first
        if not planner.name or planner.name.strip() == '':
            # They're providing their name
            name = message.strip()
            
            # Check if it's a common greeting or command - ask for name again
            common_greetings = ['hey', 'hi', 'hello', 'sup', 'yo', 'howdy', 'hey there', 'hi there']
            commands = ['reset', 'restart', 'start over', 'help', 'status', 'events']
            
            if name.lower() in common_greetings or name.lower() in commands or len(name) < 2 or len(name) > 50:
                resp.message("What's your name? (This will be shown to your guests when they receive invitations)")
                return
            
            # Save the name
            planner.name = name
            planner.save()
            
            # Create a basic event to start the workflow immediately
            event = Event(
                planner_id=planner.id,
                status='planning',
                workflow_stage='collecting_guests'
            )
            event.save()
            
            welcome_text = f"""Great to meet you, {name}! 👋
Let's plan your event!

Who's coming?

Reply with guest names and phone numbers (e.g. 'John Doe, 123-456-7890') or select previous contacts (e.g. '1,2').

Add one guest at a time.

💡 Commands:
- 'Add guest'
- 'Remove contact'
- 'Restart'"""
            
            resp.message(welcome_text)
            return
        
        # Check for reset command (for planners with names)
        if message_lower in ['reset', 'restart', 'start over']:
            try:
                # Delete any active events for this planner
                active_events = Event.query.filter_by(
                    planner_id=planner.id
                ).filter(
                    Event.status.in_(['planning', 'collecting_availability', 'selecting_time'])
                ).all()
                
                deleted_count = 0
                for event in active_events:
                    try:
                        # Delete related records first to avoid foreign key issues
                        # Delete guest states
                        guest_states = GuestState.query.filter_by(event_id=event.id).all()
                        for gs in guest_states:
                            db.session.delete(gs)
                        
                        # Delete availabilities
                        availabilities = Availability.query.filter_by(event_id=event.id).all()
                        for avail in availabilities:
                            db.session.delete(avail)
                        
                        # Delete guests
                        guests = Guest.query.filter_by(event_id=event.id).all()
                        for guest in guests:
                            db.session.delete(guest)
                        
                        # Finally delete the event
                        db.session.delete(event)
                        deleted_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error deleting event {event.id}: {e}")
                        continue
                
                # Commit all deletions
                db.session.commit()
                
                if deleted_count > 0:
                    resp.message(f"🔄 Cleared {deleted_count} active event(s)! Send me a message to start planning a new event.")
                else:
                    resp.message("🔄 No active events to clear. Send me a message to start planning a new event.")
                return
                
            except Exception as e:
                logger.error(f"Error in reset command: {e}")
                db.session.rollback()
                resp.message("🔄 Reset complete! Send me a message to start planning a new event.")
                return
        
        # Check for help command
        if message_lower in ['help', '?', 'commands']:
            help_text = """
🎉 Hangout Planner Commands:

📅 START: Begin planning a hangout
"I want to plan an event"

📊 STATUS: See your active hangouts
"Status" or "Show events"

❓ HELP: Show this menu
            """
            resp.message(help_text)
            return
        
        # Check for status/list events command - but only if no active event workflow
        if (message_lower in ['status', 'events', 'show events', 'list events'] or 
            (message_lower.startswith('status') or message_lower.startswith('show'))):
            events = Event.query.filter_by(planner_id=planner.id).order_by(Event.created_at.desc()).limit(5).all()
            
            if not events:
                resp.message("You don't have any events yet. Send me a message saying 'I want to plan an event' to get started!")
                return
            
            status_text = "📅 Your Recent Hangouts:\n\n"
            for i, event in enumerate(events, 1):
                guest_count = len(event.guests)
                status_text += f"{i}. Hangout #{i}\n"
                status_text += f"   Status: {event.status.title()}\n"
                status_text += f"   Guests: {guest_count}\n"
                if event.start_date:
                    status_text += f"   Date: {event.start_date.strftime('%B %d, %Y')}\n"
                status_text += "\n"
            
            resp.message(status_text)
            return
        
        # Check if there's an active event in progress
        active_event = Event.query.filter_by(
            planner_id=planner.id
        ).filter(
            Event.status.in_(['planning', 'collecting_availability', 'selecting_time'])
        ).filter(
            Event.workflow_stage.in_([
                'collecting_guests', 'removing_contacts', 'collecting_dates', 'awaiting_confirmation', 
                'collecting_availability', 'selecting_time', 'collecting_location', 
                'collecting_activity', 'selecting_venue', 'final_confirmation'
            ])
        ).filter(
            Event.status != 'finalized'  # Exclude finalized events
        ).order_by(Event.created_at.desc()).first()
        
        if active_event:
            # Check if they want to start a new event even with an active one
            if any(phrase in message_lower for phrase in ['plan', 'new event', 'start new', 'create event']) and 'new' in message_lower:
                # They want to start a new event - proceed to create one
                event_service = EventService()
                result = event_service.create_event_from_text(planner.id, message)
                
                if result['success']:
                    event = result['event']
                    response_text = create_guest_collection_message(planner)
                    resp.message(response_text)
                else:
                    resp.message(f"❌ {result['error']}")
            else:
                # Handle message based on current workflow stage
                handle_event_workflow_message(active_event, message, resp)
        else:
            # No active event - check if they want to start planning
            # Common greetings or planning intents
            planning_intents = ['plan', 'organize', 'event', 'party', 'meeting', 'hangout']
            greetings = ['hey', 'hi', 'hello', 'sup', 'yo', 'howdy']
            
            # If it's a greeting or simple planning intent, guide them to start
            if (message_lower in greetings or 
                any(intent in message_lower for intent in planning_intents) or
                len(message.strip()) < 10):  # Short messages are likely greetings or simple requests
                
                # Create a basic event to start the workflow
                event = Event(
                    planner_id=planner.id,
                    status='planning',
                    workflow_stage='collecting_guests'
                )
                event.save()
                
                response_text = "🎉 Ready to plan an event!\n\n" + create_guest_collection_message(planner)
                resp.message(response_text)
                return
            
            # Otherwise try to parse as detailed event information
            # But first check if it's a broad activity description
            broad_check = is_broad_activity(message)
            if broad_check['is_broad']:
                resp.message(f'"{message}" is a bit broad for event planning. Try being more specific like:\n\n"{broad_check["suggestion"]}"\n\nOr send "plan event" to start the step-by-step planner!')
                return
            
            event_service = EventService()
            result = event_service.create_event_from_text(planner.id, message)
            
            if result['success']:
                event = result['event']
                response_text = create_guest_collection_message(planner)
                resp.message(response_text)
            else:
                # If parsing fails, still start the planning process
                resp.message("🎉 Let's plan an event!\n\n" +
                           create_guest_collection_message(planner))
                
                # Create a basic event to start the workflow
                event = Event(
                    planner_id=planner.id,
                    status='planning',
                    workflow_stage='collecting_guests'
                )
                event.save()
        
    except Exception as e:
        logger.error(f"Error handling planner message: {e}")
        resp.message("Sorry, there was an error processing your request. Please try again.")


def handle_event_workflow_message(event: Event, message: str, resp: MessagingResponse):
    """
    Handle messages for an active event based on workflow stage.
    """
    try:
        stage = event.workflow_stage
        message_lower = message.lower().strip()
        
        # Handle reset command
        if message_lower in ['reset', 'start over', 'restart']:
            event.delete()
            resp.message("Event reset! Send me a message to start planning a new event.")
            return
        
        # Handle done command for guest collection
        if message_lower in ['done', 'finished', 'next', 'back'] and stage == 'collecting_guests':
            if len(event.guests) == 0:
                resp.message("You haven't added any guests yet. Please add at least one guest before proceeding.")
                return
            
            # Check if we should return to confirmation menu (came from option 3)
            if event.notes and "[RETURN_TO_CONFIRMATION]" in event.notes:
                # Remove the flag and return to confirmation
                event.notes = event.notes.replace("[RETURN_TO_CONFIRMATION]", "").strip()
                event.workflow_stage = 'awaiting_confirmation'
                event.save()
                
                # Show the confirmation menu again
                guest_list = "\n".join([f"- {guest.name} ({guest.phone_number})" for guest in event.guests])
                
                response_text = "Got it, planning for:\n"
                # Parse the dates from event notes
                if event.notes:
                    dates_match = event.notes.split("Proposed dates: ")
                    if len(dates_match) > 1:
                        dates_text = dates_match[1].split("\n")[0]
                        response_text += f"- {dates_text}\n"
                
                response_text += f"\nGuest list:\n"
                response_text += guest_list
                response_text += "\n\nWould you like to:\n"
                response_text += "1. Request guest availability\n"
                response_text += "2. Change the dates\n" 
                response_text += "3. Add more guests\n\n"
                response_text += "Reply with 1, 2, or 3."
                
                resp.message(response_text)
                return
            # Check if we should return to collecting availability (came from option 2 during availability collection)
            elif event.notes and "[AUTO_SEND_AVAILABILITY]" in event.notes:
                # Remove the flag and return to collecting availability
                event.notes = event.notes.replace("[AUTO_SEND_AVAILABILITY]", "").strip()
                event.workflow_stage = 'collecting_availability'
                event.save()
                
                # Show availability status
                total_guests = Guest.query.filter_by(event_id=event.id).count()
                provided_count = Guest.query.filter_by(event_id=event.id, availability_provided=True).count()
                pending_count = total_guests - provided_count
                
                status_text = f"📊 Availability Status:\n\n"
                status_text += f"✅ Responded: {provided_count}/{total_guests}\n"
                status_text += f"⏳ Pending: {pending_count}\n\n"
                
                if pending_count > 0:
                    # Show who hasn't responded yet
                    pending_guests = [guest for guest in event.guests if not guest.availability_provided]
                    status_text += "Still waiting for:\n"
                    for guest in pending_guests:
                        status_text += f"- {guest.name}\n"
                    status_text += "\nSend 'remind' to send follow-up messages."
                else:
                    status_text += "🎉 Everyone has responded!\n\n"
                    status_text += "Would you like to:\n"
                    status_text += "1. Pick a time\n"
                    status_text += "2. Add more guests"
                
                resp.message(status_text)
                return
            else:
                # Normal flow - move to date collection stage
                event.workflow_stage = 'collecting_dates'
                event.save()
                
                response_text = "What dates are you thinking for your event?\n\n"
                response_text += "You can say things like:\n"
                response_text += "- 'Saturday and Sunday'\n"
                response_text += "- '7/12,7/13,7/14'\n"
                response_text += "- '8/5-8/12'\n"
                response_text += "- 'friday to monday'"

                resp.message(response_text)
                return
        
        if stage == 'collecting_guests':
            # Handle special commands first
            if message_lower in ['remove contact', 'remove contacts', 'delete contact']:
                # Show contacts to remove
                planner = event.planner
                contacts = Contact.query.filter_by(planner_id=planner.id).order_by(Contact.name).all()
                
                if not contacts:
                    resp.message("You don't have any saved contacts to remove.")
                    return
                
                message_text = "Select contacts to remove by replying with their number(s) (e.g. '1,3'):\n\n"
                for i, contact in enumerate(contacts, 1):
                    message_text += f"{i}. {contact.name} ({contact.phone_number})\n"
                message_text += "\nOr reply 'back' to continue adding guests."
                
                # Set a temporary state to handle contact removal
                event.workflow_stage = 'removing_contacts'
                event.save()
                
                resp.message(message_text)
                return
                
            # Check if they're selecting from previous contacts or adding new guests
            elif message.strip().isdigit() or ',' in message.strip():
                # They might be selecting contact numbers like "1,2" or adding new guests
                if message.strip().isdigit() or all(part.strip().isdigit() for part in message.split(',')):
                    # Contact selection (e.g., "1", "2", or "1,2,3")
                    planner = event.planner
                    contacts = Contact.query.filter_by(planner_id=planner.id).order_by(Contact.name).all()
                    
                    if not contacts:
                        resp.message("You don't have any saved contacts yet. Please add guests with their phone numbers (e.g. 'John Doe, 123-456-7890').")
                        return
                    
                    # Parse selected contact numbers
                    try:
                        if ',' in message.strip():
                            selected_numbers = [int(num.strip()) for num in message.split(',')]
                        else:
                            selected_numbers = [int(message.strip())]
                        
                        added_guests = []
                        for num in selected_numbers:
                            if 1 <= num <= len(contacts):
                                contact = contacts[num - 1]
                                
                                # Check if already added to this event
                                existing_guest = Guest.query.filter_by(
                                    event_id=event.id, 
                                    phone_number=contact.phone_number
                                ).first()
                                
                                if not existing_guest:
                                    # Add guest from contact
                                    guest = Guest(
                                        event_id=event.id,
                                        contact_id=contact.id,
                                        name=contact.name,
                                        phone_number=contact.phone_number,
                                        rsvp_status='pending',
                                        availability_provided=False
                                    )
                                    guest.save()
                                    added_guests.append(guest)
                        
                        if added_guests:
                            guest_names = [f"- {guest.name}" for guest in added_guests]
                            response_text = f"Added from contacts: {', '.join([guest.name for guest in added_guests])}\n\n"
                            
                            # Check if we should automatically send availability requests
                            if event.notes and "[AUTO_SEND_AVAILABILITY]" in event.notes:
                                # Send availability requests to newly added guests
                                guest_service = GuestService()
                                for guest in added_guests:
                                    guest_service.send_availability_request(guest)
                                
                                response_text += f"📨 Availability requests sent to {len(added_guests)} new guest(s)!\n\n"
                                response_text += "Add more guests or reply 'back' to continue."
                            elif event.notes and "[RETURN_TO_CONFIRMATION]" in event.notes:
                                response_text += "Add more guests or reply 'back' to continue with event planning."
                            else:
                                response_text += "Add more guests by selecting contacts (e.g. '1,3') or adding new ones.\n\nReply 'done' when finished."
                            
                            resp.message(response_text)
                        else:
                            resp.message("Those contacts are already added or invalid numbers. Try different contact numbers or add new guests.")
                            
                    except ValueError:
                        resp.message("Please use contact numbers (e.g. '1,2') or add new guests with names and phone numbers.")
                        
                else:
                    # Regular guest addition with names and phone numbers
                    guest_service = GuestService()
                    result = guest_service.add_guests_from_text(event.id, message)
                    
                    if result['success']:
                        response_text = f"Added: {result['guests'][0].name} ({result['guests'][0].phone_number})\n\n"
                        
                        # Check if we should automatically send availability requests
                        if event.notes and "[AUTO_SEND_AVAILABILITY]" in event.notes:
                            # Send availability request to newly added guest
                            guest_service = GuestService()
                            for guest in result['guests']:
                                guest_service.send_availability_request(guest)
                            
                            response_text += f"📨 Availability request sent to {result['guests'][0].name}!\n\n"
                            response_text += "Add more guests or reply 'back' to continue."
                        elif event.notes and "[RETURN_TO_CONFIRMATION]" in event.notes:
                            response_text += "Add more guests or reply 'back' to continue with event planning."
                        else:
                            response_text += "Add more guests, or reply 'done' when finished."
                        
                        resp.message(response_text)
                    else:
                        resp.message(f"❌ {result['error']}")
            else:
                # Check if it's a greeting or common word first
                greetings = ['hey', 'hi', 'hello', 'sup', 'yo', 'howdy']
                if message_lower in greetings:
                    # Respond with current status and instructions
                    contacts = Contact.query.filter_by(planner_id=event.planner.id).order_by(Contact.name).all()
                    
                    message_text = "Hi! Let's continue planning your event.\n\n"
                    message_text += "Who's coming?\n\n"
                    message_text += "Reply with guest names and phone numbers (e.g. 'John Doe, 123-456-7890') or select previous contacts (e.g. '1,2').\n\n"
                    
                    if contacts:
                        message_text += "Previous contacts:\n"
                        for i, contact in enumerate(contacts, 1):
                            message_text += f"{i}. {contact.name} ({contact.phone_number})\n"
                        message_text += "\n"
                    
                    message_text += "Add one guest at a time.\n\n"
                    message_text += "💡 Commands:\n"
                    message_text += "- 'Add guest'\n"
                    message_text += "- 'Remove contact'\n"
                    message_text += "- 'Restart'"
                    
                    resp.message(message_text)
                    return
                
                # Regular guest addition with names and phone numbers
                guest_service = GuestService()
                result = guest_service.add_guests_from_text(event.id, message)
                
                if result['success']:
                    response_text = f"Added: {result['guests'][0].name} ({result['guests'][0].phone_number})\n\n"
                    
                    # Check if we should automatically send availability requests
                    if event.notes and "[AUTO_SEND_AVAILABILITY]" in event.notes:
                        # Send availability request to newly added guest
                        for guest in result['guests']:
                            guest_service.send_availability_request(guest)
                        
                        response_text += f"📨 Availability request sent to {result['guests'][0].name}!\n\n"
                        response_text += "Add more guests or reply 'back' to continue."
                    elif event.notes and "[RETURN_TO_CONFIRMATION]" in event.notes:
                        response_text += "Add more guests or reply 'back' to continue with event planning."
                    else:
                        response_text += "Add more guests, or reply 'done' when finished."
                    
                    resp.message(response_text)
                else:
                    resp.message(f"❌ {result['error']}")
                
        elif stage == 'removing_contacts':
            # Handle contact removal
            if message_lower == 'back':
                # Go back to collecting guests
                event.workflow_stage = 'collecting_guests'
                event.save()
                
                response_text = create_guest_collection_message(event.planner)
                resp.message(response_text)
                return
            
            # Parse contact numbers to remove
            if message.strip().isdigit() or ',' in message.strip():
                try:
                    if ',' in message.strip():
                        contact_numbers = [int(num.strip()) for num in message.split(',')]
                    else:
                        contact_numbers = [int(message.strip())]
                    
                    planner = event.planner
                    contacts = Contact.query.filter_by(planner_id=planner.id).order_by(Contact.name).all()
                    
                    removed_contacts = []
                    for num in contact_numbers:
                        if 1 <= num <= len(contacts):
                            contact = contacts[num - 1]
                            removed_contacts.append(contact.name)
                            # Remove the contact
                            db.session.delete(contact)
                    
                    if removed_contacts:
                        db.session.commit()
                        resp.message(f"✅ Removed contacts: {', '.join(removed_contacts)}\n\nReply 'back' to continue adding guests.")
                    else:
                        resp.message("❌ Invalid contact numbers. Please try again or reply 'back' to continue.")
                        
                except ValueError:
                    resp.message("Please use contact numbers (e.g. '1,3') or reply 'back' to continue.")
            else:
                resp.message("Please select contact numbers to remove (e.g. '1,3') or reply 'back' to continue adding guests.")
        elif stage == 'collecting_dates':
            # Parse dates and show confirmation menu
            from app.utils.ai import parse_dates_from_text
            
            parsed_dates = parse_dates_from_text(message)
            if parsed_dates['success']:
                # Save dates to event (you'll need to add date fields)
                event.notes = f"Proposed dates: {parsed_dates['dates_text']}"
                event.workflow_stage = 'awaiting_confirmation'
                event.save()
                
                # Show the confirmation menu like in screenshots
                guest_list = "\n".join([f"- {guest.name} ({guest.phone_number})" for guest in event.guests])
                
                # Format dates as a list
                response_text = "Got it, planning for:\n"
                if 'dates' in parsed_dates and parsed_dates['dates']:
                    for date_obj in parsed_dates['dates']:
                        if isinstance(date_obj, str):
                            # Try to parse the date string
                            try:
                                date_parsed = datetime.strptime(date_obj, '%Y-%m-%d')
                                formatted_date = date_parsed.strftime('%A, %B %-d')
                                response_text += f"- {formatted_date}\n"
                            except:
                                response_text += f"- {date_obj}\n"
                        else:
                            # Assume it's already a date object
                            try:
                                formatted_date = date_obj.strftime('%A, %B %-d')
                                response_text += f"- {formatted_date}\n"
                            except:
                                response_text += f"- {str(date_obj)}\n"
                else:
                    # Fallback to the original dates_text
                    response_text += f"- {parsed_dates['dates_text']}\n"
                
                response_text += f"\nGuest list:\n"
                response_text += guest_list
                response_text += "\n\nWould you like to:\n"
                response_text += "1. Request guest availability\n"
                response_text += "2. Change the dates\n" 
                response_text += "3. Add more guests\n\n"
                response_text += "Reply with 1, 2, or 3."
                
                resp.message(response_text)
            else:
                resp.message("I couldn't understand those dates. Please try again with a clearer format like '8/1-8/4' or 'Saturday and Sunday'.")
                
        elif stage == 'awaiting_confirmation':
            # Handle the 1/2/3 choice
            if message.strip() == '1':
                # Send availability requests
                guest_service = GuestService()
                for guest in event.guests:
                    guest_service.send_availability_request(guest)
                
                event.workflow_stage = 'collecting_availability'
                event.status = 'collecting_availability'
                event.save()
                
                resp.message("Availability requests sent via SMS!")
                
            elif message.strip() == '2':
                # Change dates - go back to date collection
                event.workflow_stage = 'collecting_dates'
                event.save()
                
                response_text = "What dates are you thinking for your event?\n\n"
                response_text += "You can say things like:\n"
                response_text += "- 'Saturday and Sunday'\n"
                response_text += "- '7/12,7/13,7/14'\n" 
                response_text += "- '8/5-8/12'\n"
                response_text += "- 'friday to monday'"
                
                resp.message(response_text)
                
            elif message.strip() == '3':
                # Add more guests - go back to guest collection with a flag to return to confirmation
                event.workflow_stage = 'collecting_guests'
                # Set a flag to indicate we should return to confirmation after adding guests
                event.notes = (event.notes or "") + "\n[RETURN_TO_CONFIRMATION]"
                event.save()
                
                # Show contact selection message
                contacts = Contact.query.filter_by(planner_id=event.planner_id).order_by(Contact.name).all()
                
                message_text = "Add more guests by replying with their contact info (e.g. 'Jane Smith, 555-123-4567') or select previous contacts (e.g. '1,2').\n\n"
                
                if contacts:
                    message_text += "Previous contacts:\n"
                    for i, contact in enumerate(contacts, 1):
                        message_text += f"{i}. {contact.name} ({contact.phone_number})\n"
                
                message_text += "\nReply 'back' when finished adding guests."
                
                resp.message(message_text)
                
            else:
                resp.message("Please reply with 1, 2, or 3 to choose an option.")
        
        elif stage == 'collecting_availability':
            # Handle messages during availability collection phase
            # Use direct database queries for consistent counting
            total_guests = Guest.query.filter_by(event_id=event.id).count()
            provided_count = Guest.query.filter_by(event_id=event.id, availability_provided=True).count()
            pending_count = total_guests - provided_count
            
            if message_lower in ['status', 'summary', 'check']:
                # Show availability status
                status_text = f"📊 Availability Status:\n\n"
                status_text += f"✅ Responded: {provided_count}/{total_guests}\n"
                status_text += f"⏳ Pending: {pending_count}\n\n"
                
                if pending_count > 0:
                    # Show who hasn't responded yet
                    pending_guests = [guest for guest in event.guests if not guest.availability_provided]
                    status_text += "Still waiting for:\n"
                    for guest in pending_guests:
                        status_text += f"- {guest.name}\n"
                    status_text += "\nSend 'remind' to send follow-up messages."
                else:
                    status_text += "🎉 Everyone has responded!\n\n"
                    status_text += "Would you like to:\n"
                    status_text += "1. Pick a time\n"
                    status_text += "2. Add more guests"
                
                resp.message(status_text)
                
            elif message_lower in ['remind', 'reminder', 'follow up']:
                # Send reminders to guests who haven't responded
                guest_service = GuestService()
                pending_guests = [guest for guest in event.guests if not guest.availability_provided]
                
                if pending_guests:
                    for guest in pending_guests:
                        guest_service.send_availability_request(guest)
                    
                    resp.message(f"📨 Sent reminders to {len(pending_guests)} guests!")
                else:
                    resp.message("✅ All guests have already responded!")
                    
            elif message.strip() == '1' and pending_count == 0:
                # Pick a time - calculate overlaps and show top 5 timeslots
                from app.utils.scheduling import calculate_availability_overlaps
                
                overlaps = calculate_availability_overlaps(event.id)
                
                if not overlaps:
                    resp.message("❌ No overlapping availability found. You may need to ask guests for more flexible times.")
                    return
                
                # Filter to show only slots with at least 2 guests (unless only 1 guest total)
                min_guests = 1 if total_guests == 1 else 2
                filtered_overlaps = [overlap for overlap in overlaps if overlap['guest_count'] >= min_guests]
                
                if not filtered_overlaps:
                    resp.message("❌ No timeslots found with at least 2 guests available. You may need to ask for more flexible times.")
                    return
                
                # Show top 5 timeslots
                top_slots = filtered_overlaps[:5]
                
                response_text = "🕒 Best available timeslots:\n\n"
                for i, slot in enumerate(top_slots, 1):
                    # Format the date and time
                    date_obj = slot['date']
                    if isinstance(date_obj, str):
                        date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
                    
                    formatted_date = date_obj.strftime('%A, %B %-d')
                    
                    if slot['all_day']:
                        time_str = "All day"
                    else:
                        start_time = datetime.strptime(slot['start_time'], '%H:%M').strftime('%-I:%M%p').lower()
                        end_time = datetime.strptime(slot['end_time'], '%H:%M').strftime('%-I:%M%p').lower()
                        time_str = f"{start_time}-{end_time}"
                    
                    # Format date as "Sat, 8/2" without leading zeros
                    day_name = date_obj.strftime('%a')
                    formatted_date_short = date_obj.strftime('%-m/%-d')
                    date_display = f"{day_name}, {formatted_date_short}"
                    
                    # Calculate attendance percentage
                    attendance_pct = round((slot['guest_count'] / total_guests) * 100)
                    
                    response_text += f"{i}. {date_display}: {time_str}\n"
                    response_text += f"Attendance: {attendance_pct}%\n"
                    
                    # List available guests
                    guest_names = [name for name in slot['available_guests']]
                    if len(guest_names) <= 3:
                        response_text += f"Available: {', '.join(guest_names)}\n\n"
                    else:
                        response_text += f"Available: {', '.join(guest_names[:2])}, +{len(guest_names)-2} more\n\n"
                
                response_text += "Reply with the number of your preferred(e.g. 1,2,3)"
                
                # Move to time selection stage
                event.workflow_stage = 'selecting_time'
                event.save()
                
                resp.message(response_text)
                
            elif message.strip() == '2':
                # Add more guests - they should get availability requests automatically
                event.workflow_stage = 'collecting_guests'
                # Set a flag to indicate we should send availability requests to new guests
                event.notes = (event.notes or "") + "\n[AUTO_SEND_AVAILABILITY]"
                event.save()
                
                # Show contact selection message
                contacts = Contact.query.filter_by(planner_id=event.planner_id).order_by(Contact.name).all()
                
                message_text = "Add more guests by replying with their contact info (e.g. 'Jane Smith, 555-123-4567') or select previous contacts (e.g. '1,2').\n\n"
                
                if contacts:
                    message_text += "Previous contacts:\n"
                    for i, contact in enumerate(contacts, 1):
                        message_text += f"{i}. {contact.name} ({contact.phone_number})\n"
                
                message_text += "\nNew guests will automatically receive availability requests.\nReply 'back' when finished adding guests."
                
                resp.message(message_text)
                
            else:
                # General help for collecting availability stage
                if pending_count > 0:
                    resp.message("📋 Still collecting availability...\n\n"
                               "Commands:\n"
                               "- 'Status' - Check who has responded\n"
                               "- 'Remind' - Send follow-up messages")
                else:
                    resp.message("🎉 Everyone has responded!\n\n"
                               "Would you like to:\n"
                               "1. Pick a time\n"
                               "2. Add more guests")
        
        elif stage == 'selecting_time':
            # Handle time selection from the overlap results
            if message.strip().isdigit():
                slot_number = int(message.strip())
                if 1 <= slot_number <= 5:
                    # Calculate overlaps again to get the selected slot
                    from app.utils.scheduling import calculate_availability_overlaps
                    
                    overlaps = calculate_availability_overlaps(event.id)
                    total_guests = len(event.guests)
                    min_guests = 1 if total_guests == 1 else 2
                    filtered_overlaps = [overlap for overlap in overlaps if overlap['guest_count'] >= min_guests]
                    
                    if slot_number <= len(filtered_overlaps):
                        selected_slot = filtered_overlaps[slot_number - 1]
                        
                        # Format the selected time
                        date_obj = selected_slot['date']
                        if isinstance(date_obj, str):
                            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
                        
                        formatted_date = date_obj.strftime('%A, %B %-d')
                        
                        if selected_slot['all_day']:
                            time_str = "All day"
                        else:
                            start_time = datetime.strptime(selected_slot['start_time'], '%H:%M').strftime('%-I:%M%p').lower()
                            end_time = datetime.strptime(selected_slot['end_time'], '%H:%M').strftime('%-I:%M%p').lower()
                            time_str = f"{start_time}-{end_time}"
                        
                        # Update event with selected time
                        event.start_date = date_obj
                        if not selected_slot['all_day']:
                            event.start_time = datetime.strptime(selected_slot['start_time'], '%H:%M').time()
                            event.end_time = datetime.strptime(selected_slot['end_time'], '%H:%M').time()
                        
                        # Move to location collection stage instead of finalizing
                        event.workflow_stage = 'collecting_location'
                        event.save()
                        
                        confirmation_msg = f"✅ Perfect! You've selected:\n\n"
                        confirmation_msg += f"📅 {formatted_date}\n"
                        confirmation_msg += f"🕒 {time_str}\n"
                        confirmation_msg += f"👥 {selected_slot['guest_count']}/{total_guests} can attend\n\n"
                        confirmation_msg += "🌍 Where should the hangout be?\n\n"
                        confirmation_msg += "Please specify a location (e.g., 'Williamsburg', 'Manhattan', 'St. Louis', etc.)"
                        
                        resp.message(confirmation_msg)
                    else:
                        resp.message("❌ Invalid selection. Please choose a number from the list.")
                else:
                    resp.message("❌ Invalid selection. Please choose a number from 1-5.")
            else:
                resp.message("Please select a timeslot by replying with its number (1-5).")
        
        elif stage == 'collecting_location':
            # Handle location input
            location = message.strip()
            
            if len(location) < 2:
                resp.message("Please provide a valid location (e.g., 'Williamsburg', 'Manhattan', 'St. Louis').")
                return
            
            # Store location in event notes or add a location field
            event.location = location  # Assuming we'll add this field to the Event model
            event.workflow_stage = 'collecting_activity'
            event.save()
            
            response_text = f"Great! Planning for {location}.\n\n"
            response_text += "🎯 What would you like to do?\n\n"
            response_text += "Please describe the activity (e.g., 'boozy brunch', 'Chinese restaurant', 'coffee and catch up', etc.)"
            
            resp.message(response_text)
        
        elif stage == 'collecting_activity':
            # Handle activity input
            activity = message.strip()
            
            if len(activity) < 3:
                resp.message("Please provide a more detailed activity description (e.g., 'boozy brunch', 'Chinese restaurant').")
                return
            
            # Check for overly broad terms and guide users to be more specific
            activity_lower = activity.lower().strip()
            broad_terms = {
                'chinese food': 'Chinese restaurant',
                'chinese': 'Chinese restaurant',
                'italian food': 'Italian restaurant',
                'italian': 'Italian restaurant',
                'thai food': 'Thai restaurant', 
                'thai': 'Thai restaurant',
                'mexican food': 'Mexican restaurant',
                'mexican': 'Mexican restaurant',
                'japanese food': 'Japanese restaurant or sushi restaurant',
                'japanese': 'Japanese restaurant or sushi restaurant',
                'indian food': 'Indian restaurant',
                'indian': 'Indian restaurant',
                'food': 'specific restaurant type (e.g., "pizza place", "burger joint")',
                'dinner': 'specific restaurant type (e.g., "steakhouse", "seafood restaurant")',
                'lunch': 'specific restaurant type (e.g., "sandwich shop", "salad bar")',
                'drinks': 'specific bar type (e.g., "sports bar", "cocktail lounge")',
                'bar': 'specific bar type (e.g., "sports bar", "wine bar", "rooftop bar")',
                'eat': 'specific restaurant type (e.g., "pizza place", "burger joint")',
                'eating': 'specific restaurant type (e.g., "pizza place", "burger joint")',
                'restaurant': 'specific restaurant type (e.g., "Italian restaurant", "pizza place")',
                'cuisine': 'specific restaurant type (e.g., "Thai restaurant", "burger joint")'
            }
            
            # Check if the activity contains any broad terms
            activity_is_broad = False
            matched_term = None
            suggestion = None
            
            # Direct match first
            if activity_lower in broad_terms:
                activity_is_broad = True
                matched_term = activity_lower
                suggestion = broad_terms[activity_lower]
            else:
                # Check if activity contains broad terms
                for broad_term, broad_suggestion in broad_terms.items():
                    if broad_term in activity_lower and len(activity_lower.split()) <= 2:
                        activity_is_broad = True
                        matched_term = broad_term
                        suggestion = broad_suggestion
                        break
            
            if activity_is_broad:
                resp.message(f'"{activity}" is a bit broad. Try being more specific like:\n\n"{suggestion}"\n\nWhat specific type of venue are you looking for?')
                return
            
            # Store activity in event notes or add an activity field
            event.activity = activity  # Assuming we'll add this field to the Event model
            event.workflow_stage = 'selecting_venue'
            event.save()
            
            # Generate venue suggestions using simplified AI
            try:
                venue_suggestions = suggest_venues(activity, event.location)
                
                if venue_suggestions.get('success'):
                    venues = venue_suggestions['venues'][:3]  # Top 3 suggestions
                    
                    response_text = f"🎯 Perfect! Looking for {activity} in {event.location}.\n\n"
                    response_text += "Here are some great options:\n\n"
                    
                    for i, venue in enumerate(venues, 1):
                        response_text += f"{i}. {venue.get('name', 'Unknown venue')}\n"
                        response_text += f"{venue.get('link', '')}\n"
                        if venue.get('description'):
                            response_text += f"- {venue['description']}\n\n"
                        else:
                            response_text += "\n"
                    
                    response_text += "Select an option (1,2,3) or say:\n"
                    response_text += "- 'New list' for more options\n"
                    response_text += "- 'Activity' to change the activity\n"
                    response_text += "- 'Location' to change the location"
                    
                    # Store venue suggestions for later selection
                    event.venue_suggestions = json.dumps(venues)
                    event.save()
                    
                else:
                    # AI failed - ask user to be more specific
                    error_message = venue_suggestions.get('error', 'Please be more specific about the venue type.')
                    response_text = f"🤔 {error_message}\n\n"
                    response_text += "Try being more specific, like:\n"
                    response_text += f"- 'Italian restaurant' instead of 'dinner'\n"
                    response_text += f"- 'Sports bar' instead of 'drinks'\n"
                    response_text += f"- 'Coffee shop' instead of 'casual meetup'\n\n"
                    response_text += "What specific type of venue are you looking for?"
                    
                    # Stay in collecting_activity stage for retry
                    event.workflow_stage = 'collecting_activity'
                    event.save()
                
                resp.message(response_text)
                
            except Exception as e:
                logger.error(f"Error in venue suggestion process: {e}")
                resp.message("I'm having trouble with venue suggestions right now. "
                           "Please try being more specific about what type of venue you want.")
        
        elif stage == 'selecting_venue':
            # Handle venue selection or other options
            message_lower = message.lower().strip()
            
            if message.strip().isdigit():
                # Venue selection (1-3)
                venue_number = int(message.strip())
                if 1 <= venue_number <= 3:
                    try:
                        # Get stored venue suggestions
                        venue_suggestions = json.loads(event.venue_suggestions or '[]')
                        
                        if venue_number <= len(venue_suggestions):
                            selected_venue = venue_suggestions[venue_number - 1]
                            
                            # Store selected venue
                            event.selected_venue = json.dumps(selected_venue)
                            event.workflow_stage = 'final_confirmation'
                            # Keep status as 'selecting_time' until invitations are sent
                            event.save()
                            
                            # Create final event summary
                            date_obj = event.start_date
                            formatted_date = date_obj.strftime('%A, %B %-d') if date_obj else "TBD"
                            
                            if event.start_time and event.end_time:
                                start_time = event.start_time.strftime('%I:%M%p').lower()
                                end_time = event.end_time.strftime('%I:%M%p').lower()
                                time_str = f"{start_time}-{end_time}"
                            else:
                                time_str = "All day"
                            
                            guest_names = [guest.name for guest in event.guests if guest.name]
                            attendees = ", ".join(guest_names) if guest_names else f"{len(event.guests)} guests"
                            
                            confirmation_msg = "🎉 Event Ready to Send!\n\n"
                            confirmation_msg += f"📅 Date: {formatted_date}\n"
                            confirmation_msg += f"🕒 Time: {time_str}\n"
                            confirmation_msg += f"🏢 Activity: {selected_venue.get('name', 'Selected venue')}\n"
                            confirmation_msg += f"👥 Attendees: {attendees}\n\n"
                            confirmation_msg += "Would you like to:\n"
                            confirmation_msg += "1. Send invitations to guests\n"
                            confirmation_msg += "Or reply 'restart' to start over with a new event"
                            
                            resp.message(confirmation_msg)
                        else:
                            resp.message("❌ Invalid selection. Please choose a number from the list.")
                    except Exception as e:
                        logger.error(f"Error processing venue selection: {e}")
                        resp.message("Sorry, there was an error processing your selection. Please try again.")
                else:
                    resp.message("❌ Invalid selection. Please choose a number from 1-3.")
            
            elif 'new list' in message_lower or 'different options' in message_lower:
                # Regenerate venue suggestions with different criteria
                try:
                    # Get previously suggested venues to avoid duplicates
                    previous_venues = []
                    if event.venue_suggestions:
                        try:
                            previous_suggestions = json.loads(event.venue_suggestions)
                            previous_venues = [venue.get('name', '') for venue in previous_suggestions]
                        except:
                            previous_venues = []
                    
                    # Create requirements to get different types of venues
                    requirements = []
                    if previous_venues:
                        requirements.append(f"different from: {', '.join(previous_venues)}")
                        requirements.append("alternative style venues")
                        requirements.append("different price range options")
                    
                    venue_suggestions = suggest_venues(event.activity, event.location, requirements)
                    
                    if venue_suggestions and venue_suggestions.get('success'):
                        venues = venue_suggestions['venues'][:3]  # Top 3 suggestions
                        
                        response_text = f"🔄 Here are some different options for {event.activity} in {event.location}:\n\n"
                        
                        for i, venue in enumerate(venues, 1):
                            response_text += f"{i}. {venue.get('name', 'Unknown venue')}\n"
                            # Generate proper Google Maps search link if no website provided
                            if venue.get('link') and venue['link'].strip():
                                response_text += f"{venue['link']}\n"
                            else:
                                # Create a proper Google Maps search URL
                                venue_name = venue.get('name', '').replace(' ', '+')
                                activity_clean = event.activity.replace(' ', '+')
                                maps_url = f"https://www.google.com/maps/search/{venue_name}+{activity_clean}+{event.location.replace(' ', '+')}"
                                response_text += f"{maps_url}\n"
                            if venue.get('description'):
                                response_text += f"- {venue['description']}\n\n"
                        
                        response_text += "Select an option (1,2,3) or say:\n"
                        response_text += "- 'New list' for more options\n"
                        response_text += "- 'Activity' to change the activity\n"
                        response_text += "- 'Location' to change the location"
                        
                        # Store new venue suggestions
                        event.venue_suggestions = json.dumps(venues)
                        event.save()
                        
                        resp.message(response_text)
                    else:
                        resp.message("Sorry, I couldn't generate new suggestions. Please try a different activity or location.")
                except Exception as e:
                    logger.error(f"Error regenerating venue suggestions: {e}")
                    resp.message("Sorry, I'm having trouble generating new suggestions. Please try again.")
            
            elif 'activity' in message_lower and 'different' not in message_lower:
                # Go back to activity collection
                event.workflow_stage = 'collecting_activity'
                event.save()
                
                response_text = "🎯 What would you like to do instead?\n\n"
                response_text += "Please describe the activity (e.g., 'boozy brunch', 'Chinese restaurant', 'coffee and catch up', etc.)"
                
                resp.message(response_text)
            
            elif 'location' in message_lower and 'different' not in message_lower:
                # Go back to location collection
                event.workflow_stage = 'collecting_location'
                event.save()
                
                response_text = "🌍 Where should the hangout be?\n\n"
                response_text += "Please specify a location (e.g., 'Williamsburg', 'Manhattan', 'St. Louis', etc.)"
                
                resp.message(response_text)
            
            else:
                resp.message("Please select a venue (1,2,3) or say:\n"
                           "- 'New list' for more options\n"
                           "- 'Activity' to change the activity\n"
                           "- 'Location' to change the location")

        elif stage == 'final_confirmation':
            # Handle final actions: send invitations or start over
            if message.strip() == '1':
                # Send invitations to guests - NOW finalize the event
                event.status = 'finalized'
                event.save()
                
                # Create the final event details message
                date_obj = event.start_date
                formatted_date = date_obj.strftime('%A, %B %-d') if date_obj else "TBD"
                
                if event.start_time and event.end_time:
                    start_time = event.start_time.strftime('%I:%M%p').lower()
                    end_time = event.end_time.strftime('%I:%M%p').lower()
                    time_str = f"{start_time}-{end_time}"
                else:
                    time_str = "All day"
                
                # Get selected venue details
                try:
                    selected_venue = json.loads(event.selected_venue) if event.selected_venue else {}
                except:
                    selected_venue = {}
                
                # Create invitation message for guests
                invitation_msg = f"🎉 You're invited!\n\n"
                invitation_msg += f"📅 Date: {formatted_date}\n"
                invitation_msg += f"🕒 Time: {time_str}\n"
                invitation_msg += f"🏢 Venue: {selected_venue.get('name', 'Selected venue')}\n"
                if selected_venue.get('link'):
                    invitation_msg += f"{selected_venue['link']}\n"
                invitation_msg += f"\nPlanned by: {event.planner.name or format_phone_display(event.planner.phone_number)}\n\n"
                invitation_msg += "Please reply 'Yes', 'No', or 'Maybe' to confirm your attendance!"
                
                # Send invitations to all guests
                sent_count = 0
                for guest in event.guests:
                    try:
                        send_sms(guest.phone_number, invitation_msg)
                        
                        # Update contact's last_contacted timestamp
                        if guest.contact_id:
                            contact = Contact.query.get(guest.contact_id)
                            if contact:
                                contact.last_contacted = datetime.now()
                                db.session.add(contact)
                        
                        # Create guest state for RSVP tracking
                        guest_state = GuestState(
                            phone_number=guest.phone_number,
                            event_id=event.id,
                            current_state='awaiting_rsvp'
                        )
                        guest_state.save()
                        sent_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error sending invitation to {guest.phone_number}: {e}")
                
                # Confirm to planner
                planner_msg = f"📨 Invitations sent to {sent_count}/{len(event.guests)} guests!\n\n"
                planner_msg += f"Event is now FINALIZED. Guests will reply with their RSVPs.\n\n"
                planner_msg += "To plan another event, send respond to this message."
                
                resp.message(planner_msg)
            
            elif message.strip() == '2':
                # This option is now removed - user should use 'restart' instead
                resp.message("Please reply with '1' to send invitations, or 'restart' to start over with a new event.")
            
            elif message_lower in ['new event', 'plan another', 'start new']:
                # This option is now removed - user should use 'restart' instead
                resp.message("Please reply with '1' to send invitations, or 'restart' to start over with a new event.")
                
            else:
                resp.message("Please reply with '1' to send invitations, or 'restart' to start over with a new event.")
        
        else:
            resp.message("I'm not sure how to help with that right now. Try 'status' to see your current events or 'help' for commands.")
            
    except Exception as e:
        logger.error(f"Error handling workflow message: {e}")
        resp.message("Sorry, there was an error. Please try again.")


def handle_guest_message(phone_number: str, message: str, resp: MessagingResponse):
    """
    Handle messages from users with active guest states.
    In the new approach, guest states are temporary and message-driven.
    Once resolved, users automatically return to planner mode.
    """
    try:
        # Get active guest state - this is why we're here
        guest_state = GuestState.query.filter_by(phone_number=phone_number).first()
        
        if not guest_state:
            # No active guest state - this shouldn't happen with new routing
            # Redirect to planner handling
            logger.warning(f"handle_guest_message called without guest_state for {phone_number}")
            planner = Planner.query.filter_by(phone_number=phone_number).first()
            if planner:
                handle_planner_message(planner, message, resp)
            else:
                handle_new_user(phone_number, message, resp)
            return
        
        # Handle based on current guest state
        current_state = guest_state.current_state
        
        if current_state == 'awaiting_availability':
            handle_availability_response(guest_state, message, resp)
        elif current_state == 'confirming_availability':
            handle_availability_confirmation(guest_state, message, resp)
        elif current_state == 'awaiting_rsvp':
            handle_rsvp_response(guest_state, message, resp)
        elif current_state == 'awaiting_confirmation':
            handle_confirmation_response(guest_state, message, resp)
        else:
            # Unknown state - clean up and return to planner mode
            logger.warning(f"Unknown guest state: {current_state} for {phone_number}")
            guest_state.delete()
            
            # Get planner name for response
            event = Event.query.get(guest_state.event_id) if guest_state.event_id else None
            planner_name = event.planner.name if event and event.planner.name else "your event planner"
            resp.message(f"Thanks for your message! I'll let {planner_name} know. You're now back in planning mode.")
            
    except Exception as e:
        logger.error(f"Error handling guest message: {e}")
        resp.message("Sorry, there was an error processing your message. Please try again.")


def cleanup_guest_state_and_return_to_planner(guest_state: GuestState, phone_number: str):
    """
    Helper function to clean up guest state and ensure user returns to planner mode.
    """
    try:
        # Delete the guest state
        guest_state.delete()
        
        # Ensure user has a planner record to return to
        planner = Planner.query.filter_by(phone_number=phone_number).first()
        if not planner:
            # Create planner record if it doesn't exist
            planner = Planner(
                phone_number=phone_number,
                name=None  # Will be collected when they start planning
            )
            planner.save()
            
        return planner
        
    except Exception as e:
        logger.error(f"Error cleaning up guest state: {e}")
        return None


def handle_availability_response(guest_state: GuestState, message: str, resp: MessagingResponse):
    """
    Handle guest availability responses.
    """
    try:
        # Get guest and event info first to provide context
        guest = Guest.query.filter_by(phone_number=guest_state.phone_number).first()
        event = Event.query.get(guest_state.event_id)
        
        if not guest or not event:
            planner_name = event.planner.name if event and event.planner.name else "your event planner"
            resp.message(f"Sorry, I couldn't find your event information. Please contact {planner_name}.")
            return
        
        # Create context for AI parsing
        event_context = {
            'event_notes': event.notes,
            'current_date': datetime.now().isoformat()
        }
        
        # Parse availability using AI with event context
        parsed_availability = parse_availability(message, event_context)
        
        if parsed_availability.get('error'):
            resp.message("I didn't understand your availability. Please try again. "
                       "For example: 'I'm free Monday 2-5pm and Wednesday evening'")
            return
        
        # Format availability for confirmation
        availability_text = "Got it! Here's your availability:\n\n"
        
        available_dates = parsed_availability.get('available_dates', [])
        if available_dates:
            for avail_data in available_dates:
                date_str = avail_data.get('date')
                start_time = avail_data.get('start_time')
                end_time = avail_data.get('end_time')
                all_day = avail_data.get('all_day', False)
                
                if date_str:
                    # Convert date to day name and formatted date
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        day_name = date_obj.strftime('%a')  # Abbreviated day name (Mon, Tue, etc.)
                        # Format date as M/D (no leading zeros)
                        formatted_date = date_obj.strftime('%-m/%-d')
                        date_display = f"{day_name}, {formatted_date}"
                        
                        if all_day:
                            availability_text += f"- {date_display}: All day\n"
                        elif start_time and end_time:
                            # Convert 24-hour to 12-hour format without leading zeros
                            start_12hr = datetime.strptime(start_time, '%H:%M').strftime('%-I:%M%p').lower()
                            end_12hr = datetime.strptime(end_time, '%H:%M').strftime('%-I:%M%p').lower()
                            availability_text += f"- {date_display}: {start_12hr} to {end_12hr}\n"
                        elif start_time:
                            start_12hr = datetime.strptime(start_time, '%H:%M').strftime('%-I:%M%p').lower()
                            availability_text += f"- {date_display}: {start_12hr} onwards\n"
                        else:
                            availability_text += f"- {date_display}: Available\n"
                    except Exception as e:
                        logger.error(f"Error formatting date {date_str}: {e}")
                        availability_text += f"- {date_str}: Available\n"
        else:
            availability_text += "- No specific times provided\n"
        
        availability_text += "\nWould you like to:\n"
        availability_text += "1. Send Availability\n"
        availability_text += "2. Change Availability\n\n"
        availability_text += "Reply with 1 or 2"
        
        # Store the parsed availability in guest state for later use
        guest_state.set_state_data(parsed_availability)  # Store using the helper method
        guest_state.current_state = 'confirming_availability'
        guest_state.save()
        
        resp.message(availability_text)
        
    except Exception as e:
        logger.error(f"Error handling availability response: {e}")
        db.session.rollback()  # Rollback on error
        resp.message("Sorry, there was an error processing your availability. Please try again.")


def handle_availability_confirmation(guest_state: GuestState, message: str, resp: MessagingResponse):
    """
    Handle guest confirmation of their availability (option 1 or 2).
    """
    try:
        logger.info(f"Starting availability confirmation for {guest_state.phone_number}")
        message_stripped = message.strip()
        logger.info(f"Message received: '{message_stripped}'")
        
        if message_stripped == '1':
            # Send/Save the availability
            # Retrieve the stored parsed availability
            try:
                logger.info(f"Retrieving stored availability data for {guest_state.phone_number}")
                parsed_availability = guest_state.get_state_data()  # Get using the helper method
                logger.info(f"Retrieved data: {parsed_availability}")
                if not parsed_availability:
                    raise ValueError("No availability data found")
            except Exception as e:
                logger.error(f"Error retrieving stored availability: {e}")
                resp.message("Sorry, there was an error. Please provide your availability again.")
                guest_state.current_state = 'awaiting_availability'
                guest_state.save()
                return
            
            # Get guest and event info
            logger.info(f"Getting event and guest info for event_id: {guest_state.event_id}")
            event = Event.query.get(guest_state.event_id)
            guest = Guest.query.filter_by(phone_number=guest_state.phone_number, event_id=guest_state.event_id).first()
            
            # Debug: Check what we found
            logger.info(f"Found guest: {guest.id if guest else 'None'}, event: {event.id if event else 'None'}")
            if guest:
                logger.info(f"Guest before update: availability_provided = {guest.availability_provided}")
            
            if not guest or not event:
                planner_name = event.planner.name if event and event.planner.name else "your event planner"
                resp.message(f"Sorry, I couldn't find your event information. Please contact {planner_name}.")
                return
            
            # Create availability records (same logic as before)
            saved_count = 0
            for avail_data in parsed_availability.get('available_dates', []):
                try:
                    # Convert string date to date object
                    date_str = avail_data.get('date')
                    if date_str:
                        if isinstance(date_str, str):
                            availability_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        else:
                            availability_date = date_str
                    else:
                        availability_date = None
                    
                    # Convert string times to time objects if provided
                    start_time_str = avail_data.get('start_time')
                    end_time_str = avail_data.get('end_time')
                    
                    start_time_obj = None
                    end_time_obj = None
                    
                    if start_time_str:
                        start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
                    if end_time_str:
                        end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
                    
                    availability = Availability(
                        event_id=event.id,
                        guest_id=guest.id,
                        date=availability_date,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        all_day=avail_data.get('all_day', False),
                        preference_level=avail_data.get('preference', 'available'),
                        notes=parsed_availability.get('notes')
                    )
                    db.session.add(availability)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving availability: {e}")
                    continue
            
            # Update guest flag - this is the critical step
            logger.info(f"About to update guest {guest.id}: availability_provided from {guest.availability_provided} to True")
            guest.availability_provided = True
            db.session.add(guest)
            
            # Also try direct SQL update as backup
            db.session.execute(
                db.text("UPDATE guests SET availability_provided = 1 WHERE id = :guest_id"),
                {"guest_id": guest.id}
            )
            logger.info(f"Applied direct SQL update for guest {guest.id}")
            
            # Clear guest state and ensure user returns to planner mode
            db.session.delete(guest_state)
            
            # Ensure user has a planner record to return to
            planner_record = Planner.query.filter_by(phone_number=guest_state.phone_number).first()
            if not planner_record:
                # Create planner record for automatic return to planner mode
                planner_record = Planner(
                    phone_number=guest_state.phone_number,
                    name=None  # Will be collected when they start planning
                )
                db.session.add(planner_record)
            
            # Commit all changes in one transaction
            try:
                db.session.commit()
                logger.info(f"Successfully committed database changes for guest {guest.id}")
                
                # Double-check immediately after commit with both methods
                verification_guest = Guest.query.get(guest.id)
                sql_check = db.session.execute(
                    db.text("SELECT availability_provided FROM guests WHERE id = :guest_id"),
                    {"guest_id": guest.id}
                ).scalar()
                logger.info(f"Verification: guest {guest.id} ORM={verification_guest.availability_provided}, SQL={sql_check}")
                
            except Exception as e:
                logger.error(f"Database commit failed: {e}")
                db.session.rollback()
                resp.message("Sorry, there was an error saving your availability. Please try again.")
                return
            
            if saved_count > 0:
                resp.message(f"✅ Thanks! I've recorded your availability. "
                           f"{event.planner.name or 'Your event planner'} will use this to find the best time for everyone.")
            else:
                planner_name = event.planner.name if event.planner.name else "your event planner"
                resp.message(f"✅ Thanks for responding! I'll let {planner_name} know about your availability.")
            
            # Notify planner with availability status
            planner = event.planner
            
            # Use explicit database queries to avoid caching issues
            # Refresh the event to make sure we have latest data
            db.session.refresh(event)
            
            total_guests = Guest.query.filter_by(event_id=event.id).count()
            provided_count = Guest.query.filter_by(event_id=event.id, availability_provided=True).count()
            pending_count = total_guests - provided_count
            
            # Debug: Log the counts immediately after our update
            logger.info(f"Immediate count check - Event {event.id}: total={total_guests}, provided={provided_count}, pending={pending_count}")
            
            # Also try a direct SQL approach as a backup verification
            result = db.session.execute(
                db.text("SELECT COUNT(*) FROM guests WHERE event_id = :event_id AND availability_provided = 1"),
                {"event_id": event.id}
            ).scalar()
            logger.info(f"Direct SQL count of provided availability: {result}")
            
            if pending_count == 0:
                # All guests have responded
                notification_msg = f"🎉 {guest.name or format_phone_display(guest.phone_number)} provided availability for {event.title}!\n\n"
                notification_msg += f"🎉 Everyone has responded!\n\n"
                notification_msg += "Would you like to:\n"
                notification_msg += "1. Pick a time\n"
                notification_msg += "2. Add more guests"
            else:
                # Still waiting for some guests
                notification_msg = f"📅 {guest.name or format_phone_display(guest.phone_number)} provided availability for {event.title}\n\n"
                notification_msg += f"Status: {provided_count}/{total_guests} responded, {pending_count} pending\n\n"
                notification_msg += "Send 'status' to see who's left or 'remind' to follow up."
            
            send_sms(planner.phone_number, notification_msg)
            
        elif message_stripped == '2':
            # Change availability - go back to awaiting availability
            guest_state.current_state = 'awaiting_availability'
            guest_state.set_state_data(None)  # Clear stored data using helper method
            guest_state.save()
            
            resp.message("Please provide your availability again. "
                       "For example: 'I'm free Monday 2-5pm and Wednesday evening'")
        else:
            resp.message("Please reply with 1 to send your availability or 2 to change it.")
            
    except Exception as e:
        logger.error(f"Error handling availability confirmation: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        db.session.rollback()
        resp.message(f"Sorry, there was an error: {str(e)}. Please try again.")


def handle_rsvp_response(guest_state: GuestState, message: str, resp: MessagingResponse):
    """
    Handle guest RSVP responses.
    """
    message_lower = message.lower().strip()
    
    # Determine RSVP status
    if any(word in message_lower for word in ['yes', 'accept', 'coming', 'attend', 'will be there']):
        rsvp_status = 'accepted'
        response_msg = "🎉 Great! You're confirmed for the event."
    elif any(word in message_lower for word in ['no', 'decline', 'cannot', "can't", 'unable']):
        rsvp_status = 'declined'
        response_msg = "😔 Sorry you can't make it. Thanks for letting us know."
    elif any(word in message_lower for word in ['maybe', 'unsure', 'not sure', 'possibly']):
        rsvp_status = 'maybe'
        response_msg = "📝 Thanks! I've marked you as maybe. Please update us when you know for sure."
    else:
        resp.message("Please respond with 'Yes', 'No', or 'Maybe' to confirm your attendance.")
        return
    
    # Update guest RSVP
    guest = Guest.query.filter_by(phone_number=guest_state.phone_number, event_id=guest_state.event_id).first()
    event = Event.query.get(guest_state.event_id)
    
    if guest and event:
        # Store phone number before deleting guest_state
        phone_number = guest_state.phone_number
        
        # Update guest RSVP status
        guest.rsvp_status = rsvp_status
        db.session.add(guest)
        
        # Clear guest state and ensure user returns to planner mode
        db.session.delete(guest_state)
        
        # Ensure user has a planner record to return to
        planner_record = Planner.query.filter_by(phone_number=phone_number).first()
        if not planner_record:
            # Create planner record for automatic return to planner mode
            planner_record = Planner(
                phone_number=phone_number,
                name=None  # Will be collected when they start planning
            )
            db.session.add(planner_record)
        
        db.session.commit()
        
        resp.message(response_msg)
        
        # Notify planner
        planner = event.planner
        # Create a simple event description
        event_desc = "your event"
        if hasattr(event, 'venue') and event.venue:
            event_desc = f"{event.venue}"
        elif hasattr(event, 'selected_venue') and event.selected_venue:
            try:
                import json
                venue_data = json.loads(event.selected_venue)
                if venue_data and venue_data.get('name'):
                    event_desc = venue_data['name']
            except:
                pass
        
        if event.start_date:
            try:
                event_desc += f" on {event.start_date.strftime('%m/%d')}"
            except:
                pass
        
        send_sms(
            planner.phone_number,
            f"📋 {guest.name or format_phone_display(guest.phone_number)} RSVP: {rsvp_status.upper()} for {event_desc}"
        )
    else:
        resp.message("Sorry, I couldn't find your event information.")


def handle_confirmation_response(guest_state: GuestState, message: str, resp: MessagingResponse):
    """
    Handle guest confirmation responses for finalized events.
    """
    resp.message("✅ Thanks for confirming! We'll send you reminders closer to the event date.")
    
    # Clear guest state and ensure user returns to planner mode
    db.session.delete(guest_state)
    
    # Ensure user has a planner record to return to
    planner_record = Planner.query.filter_by(phone_number=guest_state.phone_number).first()
    if not planner_record:
        # Create planner record for automatic return to planner mode
        planner_record = Planner(
            phone_number=guest_state.phone_number,
            name=None  # Will be collected when they start planning
        )
        db.session.add(planner_record)
    
    db.session.commit()


def handle_new_user(phone_number: str, message: str, resp: MessagingResponse):
    """
    Handle messages from new/unknown users.
    Always create a planner account and start the welcome flow.
    """
    # For any new user, create planner account and start welcome flow
    # This skips the intro message and goes straight to onboarding
    planner = Planner(
        phone_number=phone_number,
        name=None
    )
    planner.save()
    
    welcome_text = """🎉 Welcome to Event Planner!

What's your name?"""
    
    resp.message(welcome_text.strip())
