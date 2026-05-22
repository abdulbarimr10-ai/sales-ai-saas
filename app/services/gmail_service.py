import json
import os
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.core.config import settings
from app.core.security import encrypt_data, decrypt_data
from app.repositories.gmail_repository import gmail_repository
from app.core.logging import logger

# Allow insecure HTTP transport for local OAuth flow only in development/debug
if settings.ENV == 'development' or settings.DEBUG:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

class GmailService:
    def get_google_flow(self):
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        }
        
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config,
            scopes=SCOPES
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        return flow

    def generate_auth_url(self) -> tuple[str, str]:
        flow = self.get_google_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return authorization_url, state

    def handle_callback(self, user_id: int, authorization_response: str):
        flow = self.get_google_flow()
        flow.fetch_token(authorization_response=authorization_response)
        
        credentials = flow.credentials
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        email_address = user_info.get('email')
        
        creds_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        encrypted_creds = encrypt_data(json.dumps(creds_dict))
        gmail_repository.save_credentials(user_id, email_address, encrypted_creds)
        return email_address

    def get_user_credentials(self, user_id: int) -> Credentials:
        """Returns the decrypted Google Credentials object for runtime use."""
        conn = gmail_repository.get_connection(user_id)
        if not conn or not conn['is_active']:
            return None
            
        try:
            creds_json = decrypt_data(conn['encrypted_credentials'])
            creds_dict = json.loads(creds_json)
            return Credentials(**creds_dict)
        except Exception as e:
            logger.error(f"Failed to decrypt/load Gmail credentials for user {user_id}: {e}")
            return None

    def get_status(self, user_id: int):
        conn = gmail_repository.get_connection(user_id)
        if not conn:
            return None
        return {
            "gmail_address": conn['gmail_address'],
            "is_active": conn['is_active'],
            "created_at": conn['created_at']
        }

    def disconnect(self, user_id: int):
        gmail_repository.delete_connection(user_id)

    def test_connection(self, user_id: int) -> bool:
        creds = self.get_user_credentials(user_id)
        if not creds:
            return False
            
        try:
            service = build('gmail', 'v1', credentials=creds)
            # Try to get user profile as a ping
            service.users().getProfile(userId='me').execute()
            del creds
            return True
        except Exception as e:
            logger.error(f"Gmail connection test failed: {e}")
            gmail_repository.mark_inactive(user_id)
            return False

gmail_service = GmailService()
