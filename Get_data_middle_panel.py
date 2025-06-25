from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from config_handler import ConfigHandler

class TemplateHandler:
    def __init__(self):
        # Update scopes to include write permissions
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.file',  # Add permission to create/edit files
            'https://www.googleapis.com/auth/drive'  # Full drive access
        ]
        self.creds = None
        self.service = None
        self.config = ConfigHandler()
        
    def authenticate(self):
        """Authenticate with Google Drive using configs."""
        token_path = self.config.get_token_path()
        
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                self.creds = pickle.load(token)
                
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                credentials_path = self.config.get_credentials_path()
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
                
            with open(token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('drive', 'v3', credentials=self.creds)
        return True

    def get_template_files(self):
        """Get document files from template folder."""
        try:
            # Get template folder ID from config
            folder_id = self.config.get_template_folder_id()
            # print(f"Template Folder ID: {folder_id}")
            
            # Query for documents in the folder
            query = (
                f"parents='{folder_id}' and ("
                "mimeType='application/vnd.google-apps.document' or "
                "mimeType='application/msword' or "
                "mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
                ") and trashed=false"
            )
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields="files(id, name, mimeType)",
                pageSize=100
            ).execute()
            
            files = results.get('files', [])
                    
            return files
            
        except Exception as e:
            print(f"Error getting template files: {str(e)}")
            return []

def main():
    handler = TemplateHandler()
    if handler.authenticate():
        print("Authentication successful")
        templates = handler.get_template_files()
        return templates
    return []

if __name__ == '__main__':
    main()