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
        
    def get_template_content(self, filename, file_id):
        """
        Download and return the content of a template file from Google Drive.
        """
        try:
            # Ensure authentication
            if not self.drive_service:
                self.authenticate()

            # Get the template folder ID from config
            template_folder_id = self.config.get_template_folder_id()

            # Get file metadata
            file = self.drive_service.files().get(
                fileId=file_id, 
                fields='name,mimeType,parents'
            ).execute()


            # Get content based on file type
            if file['mimeType'] == 'application/vnd.google-apps.document':
                content = self.drive_service.files().export(
                    fileId=file_id,
                    mimeType='text/plain'  # Use 'text/html' for formatting, or 'text/plain' for plain text
                ).execute()
                text_content = content.decode('utf-8')
            else:
                request = self.drive_service.files().get_media(fileId=file_id)
                file_content = io.BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                text_content = file_content.getvalue().decode('utf-8')
            # print(text_content)
            return text_content

        except Exception as e:
            print(f"Error downloading template '{filename}': {str(e)}")
            return None

    def collect_report_data(self,left_panel, middle_panel, right_panel):
        # Initialize warnings list
        warnings = []
        
        # Validate and collect data from left panel
        report_data = {}
        
        # Check project selection
        project_code = left_panel.project_combo.currentText()
        if project_code == "None":
            warnings.append("Please select a project")
        report_data['project'] = project_code if project_code != "None" else None
        
        # Check analysis type
        if not (left_panel.genome_radio.isChecked() or left_panel.transcriptome_radio.isChecked()):
            warnings.append("Please select an analysis type")
        report_data['analysis_type'] = (
            'Genome' if left_panel.genome_radio.isChecked() 
            else 'Transcriptome' if left_panel.transcriptome_radio.isChecked()
            else None
        )
        
        # Check reference
        reference = left_panel.reference_combo.currentText()
        report_data['reference'] = reference if reference != "None" else None
        
        # Check selected samples
        selected_samples = [
            sample for sample, checkbox in left_panel.sample_checkboxes.items()
            if checkbox.isChecked()
        ]
        if not selected_samples:
            warnings.append("Please select at least one sample")
        report_data['selected_samples'] = selected_samples

        # Check title
        title = left_panel.title_input.text().strip()
        if not title:
            warnings.append("Report title is required")
        report_data['title'] = title
        
        # Check selected templates from middle panel
        template_content_dict = {}

        if not middle_panel.selected_templates:
            warnings.append("Please select at least one template")
        
        selected_template_label_text = middle_panel.sel_template_label.text().split('<br>')
        # print(selected_template_label_text)
        template_id_dict = {name: file_id for name, file_id in middle_panel.selected_templates}
        for i in range(len(selected_template_label_text)):
            name = selected_template_label_text[i]
            file_id = template_id_dict[name]
            # print(name)
            template_content_dict[i+1] = self.get_template_content(name, file_id)

        # print(template_content_dict.keys())
        report_data['template_content_dict'] = template_content_dict
        # print(report_data['templates'])


        # Add conclusion to report data
        report_data['conclusion'] = right_panel.conclusion_text.toPlainText()

        # Add POI inhouse and client data
        report_data['coordinator'],report_data['coordinator_email'],report_data['ngs_tech'],report_data['ngs_tech_email']="","","",""
        report_data['client_appr'],report_data['client_rep']="",""
        tmp = left_panel.poi1_dropdown.currentText()
        if tmp != "None":
            report_data['coordinator'] = tmp.split('(')[0]
            report_data['coordinator_email'] = tmp.split('(')[1].strip(')')
        tmp = left_panel.poi2_dropdown.currentText()
        if tmp != "None":
            report_data['ngs_tech'] = tmp.split('(')[0]
            report_data['ngs_tech_email'] = tmp.split('(')[1].strip(')')

        report_data['client_appr'] = left_panel.client_poi1_dropdown.currentText()
        report_data['client_rep'] = left_panel.client_poi2_dropdown.currentText()

        return report_data, warnings