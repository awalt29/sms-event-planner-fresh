from typing import Dict, List
import logging
import os

logger = logging.getLogger(__name__)

class SMSService:
    """Handles SMS communication via Twilio"""
    
    def __init__(self):
        try:
            from twilio.rest import Client
            self.client = Client(os.getenv('TWILIO_SID'), os.getenv('TWILIO_AUTH'))
            self.from_number = os.getenv('TWILIO_NUMBER')
        except ImportError:
            logger.warning("Twilio library not available")
            self.client = None
        except Exception as e:
            logger.error(f"Error initializing Twilio client: {e}")
            self.client = None
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS message"""
        try:
            if not self.client:
                logger.info(f"[SMS SIMULATION] To: {to_number}, Message: {message}")
                return True
                
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=f"+1{to_number}"
            )
            return True
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False
