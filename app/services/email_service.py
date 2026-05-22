import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from app.services.gmail_service import gmail_service
from app.core.logging import logger

class EmailService:
    def send_user_email(self, user_id: int, to_email: str, subject: str, html_content: str) -> bool:
        """
        Sends an email using the authenticated user's Gmail account.
        Automatically handles token refresh via google.oauth2.credentials.
        """
        if not to_email:
            logger.error("Missing recipient email")
            return False

        creds = gmail_service.get_user_credentials(user_id)
        if not creds:
            logger.error(f"Missing or inactive Gmail OAuth credentials for user {user_id}")
            return False

        try:
            service = build('gmail', 'v1', credentials=creds)
            
            message = MIMEText(html_content, 'html')
            message['to'] = to_email
            message['subject'] = subject
            
            # The 'from' address is automatically determined by 'me' 
            # but we can fetch the user's connected address for logging
            status = gmail_service.get_status(user_id)
            if status:
                message['from'] = status['gmail_address']

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            create_message = {'raw': raw_message}

            send_message = service.users().messages().send(userId="me", body=create_message).execute()
            
            logger.info(f"Email successfully sent to {to_email}. Message Id: {send_message['id']}")
            
            # Destroy credentials reference
            del creds
            del service
            
            return True

        except Exception as e:
            logger.error(f"General Email Error for {to_email}: {e}")
            return False

email_service = EmailService()
