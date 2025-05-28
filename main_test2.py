import sys
import os.path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QDesktopWidget, QListWidget, QPushButton, QMessageBox)
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2 import service_account
import pickle
from googleapiclient.http import MediaIoBaseDownload
import io

# Update SCOPES at the top of the file
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.readonly']

# Add folder ID constant (replace with your folder ID)
FOLDER_ID = '1LjSC6S-iS_bHlb0yjlnznQefyWhTu5Zl'

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Report Maker")
        
        # Get the screen geometry
        screen = QDesktopWidget().screenGeometry()
        width = screen.width()
        height = screen.height()
        
        # Set window size to screen size
        self.setGeometry(0, 0, width, height)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Add list widget to display files
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)
        self.file_list.itemDoubleClicked.connect(self.read_file_content)

        # Add refresh button
        refresh_btn = QPushButton("Refresh Files")
        refresh_btn.clicked.connect(self.load_drive_files)
        layout.addWidget(refresh_btn)

        # Initialize Google Drive service
        self.drive_service = self.init_google_drive()
        
        # Load files initially
        if self.drive_service:
            self.load_drive_files()

    def init_google_drive(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                
        # If there are no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        '/home/tanvi/Projects/Create_Report_GUI/credentials_tanvi.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    QMessageBox.critical(self, "Error", 
                                      f"Failed to initialize Google Drive: {str(e)}")
                    return None
                    
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        try:
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to build Drive service: {str(e)}")
            return None

    def load_drive_files(self):
        if not self.drive_service:
            return
            
        try:
            self.file_list.clear()
            # Update query to only look in specific folder
            query = f"'{FOLDER_ID}' in parents and trashed=false"
            results = self.drive_service.files().list(
                pageSize=100,
                q=query,
                fields="nextPageToken, files(id, name, mimeType)").execute()
            items = results.get('files', [])

            if not items:
                self.file_list.addItem('No files found in the specified folder.')
            else:
                for item in items:
                    self.file_list.addItem(f"{item['name']} ({item['mimeType']})")
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", 
                              f"Failed to load files: {str(e)}")
            
    def read_file_content(self, item):
        try:
            # Get file name from the item text (remove mime type part)
            file_name = item.text().split(' (')[0]
            
            # Search for the file by name in the folder
            query = f"name='{file_name}' and '{FOLDER_ID}' in parents"
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                QMessageBox.warning(self, "Error", "File not found")
                return

            file_id = files[0]['id']
            mime_type = files[0]['mimeType']

            # Handle different Google Workspace file types
            if 'google-apps' in mime_type:
                if mime_type == 'application/vnd.google-apps.document':
                    request = self.drive_service.files().export_media(
                        fileId=file_id,
                        mimeType='text/plain'
                    )
                elif mime_type == 'application/vnd.google-apps.spreadsheet':
                    request = self.drive_service.files().export_media(
                        fileId=file_id,
                        mimeType='text/csv'
                    )
                elif mime_type == 'application/vnd.google-apps.presentation':
                    request = self.drive_service.files().export_media(
                        fileId=file_id,
                        mimeType='text/plain'
                    )
                else:
                    QMessageBox.warning(self, "Error", 
                        f"Unsupported Google Workspace file type: {mime_type}")
                    return
            else:
                # Handle regular files as before
                request = self.drive_service.files().get_media(fileId=file_id)

            # Download the file content
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                _, done = downloader.next_chunk()

            # Read the content
            content = file_content.getvalue().decode('utf-8')
            
            # Show content in a message box
            QMessageBox.information(self, "File Content", content[:1000] + 
                                "\n\n[Content truncated...]" if len(content) > 1000 else content)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read file: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()