from typing import Dict, List
import logging
import os

logger = logging.getLogger(__name__)

class SMSService:
    """Handles SMS communication via Twilio"""
    
    def __init__(self):
        try:
            from twilio.rest import Client
            account_sid = os.getenv('TWILIO_ACCOUNT_SID') or os.getenv('TWILIO_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN') or os.getenv('TWILIO_AUTH')
            self.from_number = os.getenv('TWILIO_PHONE_NUMBER') or os.getenv('TWILIO_NUMBER')
            
            if not account_sid or not auth_token or not self.from_number:
                logger.error("Missing Twilio credentials - TWILIO_SID, TWILIO_AUTH, and TWILIO_NUMBER required")
                self.client = None
            else:
                self.client = Client(account_sid, auth_token)
                logger.info(f"Twilio client initialized successfully with SID: {account_sid[:8]}... and number: {self.from_number}")
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
            
            # Ensure E.164 format for Twilio
            phone_number = to_number if str(to_number).startswith('+') else f"+1{to_number}"
                
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )
            return True
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False
