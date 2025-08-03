from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """Service class for handling SMS operations with Twilio."""
    
    def __init__(self):
        self.client = None
    
    def _initialize_client(self):
        """Initialize Twilio client with configuration."""
        try:
            sid = current_app.config.get('TWILIO_SID')
            auth_token = current_app.config.get('TWILIO_AUTH')
            
            if not sid or not auth_token or sid == 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' or auth_token == 'your_auth_token_here':
                logger.warning("Twilio credentials not properly configured - using mock mode")
                self.client = None  # Don't initialize, use mock mode
                return
            
            self.client = Client(sid, auth_token)
            logger.info("Twilio client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            self.client = None  # Set to None instead of raising
    
    def send_sms(self, to_number, message, from_number=None):
        """
        Send SMS message to a phone number.
        
        Args:
            to_number (str): Recipient phone number
            message (str): Message content
            from_number (str, optional): Sender phone number (uses default if not provided)
            
        Returns:
            dict: Result with success status and message SID or error
        """
        try:
            if not self.client:
                self._initialize_client()
            
            from_number = from_number or current_app.config.get('TWILIO_NUMBER')
            if not from_number:
                raise ValueError("No sender phone number configured")
            
            # Send the message
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully to {to_number}, SID: {message_obj.sid}")
            
            return {
                'success': True,
                'message_sid': message_obj.sid,
                'status': message_obj.status
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_bulk_sms(self, recipients, message, from_number=None):
        """
        Send SMS to multiple recipients.
        
        Args:
            recipients (list): List of phone numbers
            message (str): Message content
            from_number (str, optional): Sender phone number
            
        Returns:
            dict: Results for each recipient
        """
        results = {}
        
        for recipient in recipients:
            result = self.send_sms(recipient, message, from_number)
            results[recipient] = result
        
        return results
    
    def create_twiml_response(self, message=None):
        """
        Create TwiML response for webhook handling.
        
        Args:
            message (str, optional): Response message
            
        Returns:
            MessagingResponse: TwiML response object
        """
        resp = MessagingResponse()
        
        if message:
            resp.message(message)
        
        return resp
    
    def get_message_status(self, message_sid):
        """
        Get status of a sent message.
        
        Args:
            message_sid (str): Twilio message SID
            
        Returns:
            dict: Message status information
        """
        try:
            if not self.client:
                self._initialize_client()
            
            message = self.client.messages(message_sid).fetch()
            
            return {
                'success': True,
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent,
                'date_updated': message.date_updated
            }
            
        except Exception as e:
            logger.error(f"Failed to get message status for {message_sid}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global SMS service instance (initialized lazily)
_sms_service = None


def get_sms_service():
    """Get or create SMS service instance."""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service


def send_sms(to_number, message, from_number=None):
    """
    Convenience function for sending SMS.
    
    Args:
        to_number (str): Recipient phone number
        message (str): Message content
        from_number (str, optional): Sender phone number
        
    Returns:
        dict: Result with success status and details
    """
    return get_sms_service().send_sms(to_number, message, from_number)


def send_bulk_sms(recipients, message, from_number=None):
    """
    Convenience function for sending bulk SMS.
    
    Args:
        recipients (list): List of phone numbers
        message (str): Message content
        from_number (str, optional): Sender phone number
        
    Returns:
        dict: Results for each recipient
    """
    return get_sms_service().send_bulk_sms(recipients, message, from_number)


def create_twiml_response(message=None):
    """
    Convenience function for creating TwiML response.
    
    Args:
        message (str, optional): Response message
        
    Returns:
        MessagingResponse: TwiML response object
    """
    return get_sms_service().create_twiml_response(message)
