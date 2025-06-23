from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from config_handler import ConfigHandler
from fpdf.fpdf import FPDF  
from datetime import datetime
import markdown
import html2text
import os
import pickle
import io

class RightPanelHandler:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/documents'
        ]
        self.creds = None
        self.drive_service = None  # Changed from self.service
        self.docs_service = None
        self.config = ConfigHandler()

    def authenticate(self):
        """Authenticate with Google Drive and Docs APIs."""
        try:
            token_path = self.config.get_token_path()
            
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    self.creds = pickle.load(token)

            # If credentials are invalid or don't exist, get new ones
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    credentials_path = self.config.get_credentials_path()
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, self.SCOPES)
                    self.creds = flow.run_local_server(port=0)

                # Save the credentials
                with open(token_path, 'wb') as token:
                    pickle.dump(self.creds, token)

            # Initialize both services
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.docs_service = build('docs', 'v1', credentials=self.creds)
            
            return True

        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False
        

    # def get_latest_file(self):
    #     """Get the most recent file from the template list folder."""
    #     try:
    #         template_list_folder = self.config.get_output_folder_id()
            
    #         # Query files in the template list folder, sorted by created time
    #         files = self.drive_service.files().list(
    #             q=f"parents='{template_list_folder}' and trashed=false",
    #             orderBy='createdTime desc',
    #             pageSize=1,
    #             fields='files(id, name, createdTime)'
    #         ).execute().get('files', [])
            
    #         if not files:
    #             print("No template list files found")
    #             return None
                
    #         return files[0]  # Return the most recent file

    #     except Exception as e:
    #         print(f"Error getting latest file: {str(e)}")
    #         return None
        

    # def get_file_content(self, file_id):
    #     """Get content of a file by ID."""
    #     try:
    #         content = self.drive_service.files().export(
    #             fileId=file_id,
    #             mimeType='text/plain'
    #         ).execute()
            
    #         return content.decode('utf-8')

    #     except Exception as e:
    #         print(f"Error getting file content: {str(e)}")
    #         return None

    # def get_template_content(self, template_name):
    #     """Get content of a Google Doc template by name."""
    #     try:
    #         template_folder_id = self.config.get_template_folder_id()
    #         files = self.drive_service.files().list(
    #             q=f"name='{template_name}' and parents='{template_folder_id}' and mimeType='application/vnd.google-apps.document' and trashed=false",
    #             fields='files(id, name, mimeType)'
    #         ).execute().get('files', [])
            
    #         if not files:
    #             print(f"Template not found: {template_name}")
    #             return None
                
    #         # Get document content as plain text
    #         content = self.drive_service.files().export(
    #             fileId=files[0]['id'],
    #             mimeType='text/plain'
    #         ).execute()
            
    #         return content.decode('utf-8')

    #     except Exception as e:
    #         print(f"Error getting template: {str(e)}")
    #         return None

    # def create_merged_document(self, template_list_id):
    #     """Create merged document with raw content."""
    #     try:
    #         content = self.get_file_content(template_list_id)
    #         if not content:
    #             return False
                
    #         # Clean template names
    #         template_names = [name.strip().replace('\ufeff', '') 
    #                         for name in content.split('\n') 
    #                         if name.strip()]
    #         print(f"Template names to process: {template_names}")
            
    #         # Create new Google Doc
    #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #         doc_metadata = {
    #             'name': f'Merged_Report_{timestamp}',
    #             'mimeType': 'application/vnd.google-apps.document',
    #             'parents': [self.config.get_finalreport_folder_id()]
    #         }
            
    #         merged_doc = self.drive_service.files().create(
    #             body=doc_metadata,
    #             fields='id'
    #         ).execute()

    #         # Merge all content in one batch
    #         merged_content = ""
    #         for template_name in template_names:
    #             template_content = self.get_template_content(template_name)
    #             if template_content:
    #                 merged_content += template_content + "\n\n"
            
    #         # Insert all content at once
    #         if merged_content:
    #             self.docs_service.documents().batchUpdate(
    #                 documentId=merged_doc['id'],
    #                 body={
    #                     'requests': [{
    #                         'insertText': {
    #                             'location': {'index': 1},
    #                             'text': merged_content
    #                         }
    #                     }]
    #                 }
    #             ).execute()
            
    #         print(f"Created merged document with ID: {merged_doc['id']}")
    #         return merged_doc['id']  # Return document ID instead of True

    #     except Exception as e:
    #         print(f"Error creating merged document: {str(e)}")
    #         return False
    
# def main():
#     """Test the RightPanelHandler functionality."""
#     handler = RightPanelHandler()
#     if handler.authenticate():
#         print("Authentication successful")
#         latest_file = handler.get_latest_file()
#         if latest_file:
#             print(f"Processing template list: {latest_file['name']}")
#             if handler.create_merged_document(latest_file['id']):
#                 print("Document merged successfully!")
#             else:
#                 print("Failed to merge document")
#     else:
#         print("Authentication failed")

# if __name__ == '__main__':
#     main()