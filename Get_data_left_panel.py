from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from config_handler import ConfigHandler
import pandas as pd
import io
import os.path
import pickle

class DriveDataHandler:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive'
        ]
        self.creds = None
        self.service = None
        self.config = ConfigHandler()
        
    def authenticate(self):
        """Authenticate with Google Drive using configs."""
        token_path = self.config.get_token_path()
        
        # Check if token exists
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

        self.service = build('drive', 'v3', credentials=self.creds)
        return True

    def get_folder_files(self):
        """Get all files from configured folder."""
        try:
            folder_id = self.config.get_main_folder_id()
            print(f"Folder ID: {folder_id}")
            
            query = f"parents='{folder_id}' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields="files(id, name, mimeType, fileExtension)",
                pageSize=1000
            ).execute()
            
            files = results.get('files', [])
            if not files:
                print("No files found in the specified folder.")
            else:
                print(f"Found {len(files)} files:")
                for file in files:
                    print(f"- {file['name']} (Type: {file['mimeType']})")
            print(files)  
            return files
            
        except Exception as e:
            print(f"Error getting folder contents: {str(e)}")
            return []
            

    def is_excel_file(self, mime_type):
        """Check if file is an Excel file based on MIME type or extension."""
        excel_mime_types = {
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # xlsx
            'application/vnd.ms-excel',  # xls
            'application/x-vnd.oasis.opendocument.spreadsheet',  # ods
            'application/vnd.oasis.opendocument.spreadsheet',  # ods alternative
            'application/vnd.google-apps.spreadsheet'  # Google Sheets
        }
        return mime_type in excel_mime_types or mime_type.endswith('.xlsx') or mime_type.endswith('.xls')

    def read_excel_direct(self, file_id):
        """Read Excel file or Google Sheet directly."""
        try:
            # Get file metadata
            file_metadata = self.service.files().get(fileId=file_id).execute()
            mime_type = file_metadata['mimeType']

            if not self.is_excel_file(mime_type):
                print(f"File {file_metadata['name']} is not a spreadsheet")
                return None

            # Create file stream
            file_stream = io.BytesIO()

            if mime_type == 'application/vnd.google-apps.spreadsheet':
                # Handle Google Sheets - export as Excel
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                # Handle regular Excel files
                request = self.service.files().get_media(fileId=file_id)

            # Download the file content
            downloader = MediaIoBaseDownload(file_stream, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            # Read the spreadsheet data
            file_stream.seek(0)
            df = pd.read_excel(file_stream)
            return df

        except Exception as e:
            print(f"Error reading spreadsheet: {str(e)}")
            return None

def main():
    # Initialize lists to store data
    project_code_list = []
    sample_name_list = []
    references = []
    
    handler = DriveDataHandler()
    if handler.authenticate():
        print("Authenticated successfully.")
        files = handler.get_folder_files()
        
        for file in files:
            if handler.is_excel_file(file['mimeType']):
                print(f"\nReading file: {file['name']}")
                df = handler.read_excel_direct(file['id'])
                
                if df is not None:
                    # Process different files based on their names
                            
                    if 'sample' in file['name'].lower():
                        for i,row in df.iterrows():
                            sample_name_list.append(row['Inhouse Sample Name'] + ' ('+ row['Original Sample Name'] + ')' )  # Assuming 'Sample Name' is a column in the DataFrame
                        project_code_list.extend(list(set(df['Project Code'])))
                            
                    elif 'reference' in file['name'].lower():
                        # Assuming references are in a column named 'Reference'
                        if 'References' in df.columns:
                            references.extend(df['References'].tolist())
            else:
                print(f"\nSkipping non-Excel file: {file['name']}")
        
        return project_code_list, sample_name_list, references



if __name__ == '__main__':
    main()