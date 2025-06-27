from datetime import datetime
import os
import base64
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload
from Get_data_middle_panel import TemplateHandler

class HTMLGenerator:
    def __init__(self):
        self.template_path = os.path.join(os.path.dirname(__file__), 'templates/report_template.html')
        self.stylesheet = os.path.join(os.path.dirname(__file__), 'static/style.css')
        self.handler = TemplateHandler()
        if not self.handler.authenticate():
            raise Exception("Authentication failed")
        
    def get_logos(self):
        """Get both DNA and company logos from Google Drive."""
        try:
            logo_folder = self.handler.config.get_logo_folder_id()
            logos = {}
            
            # Query for both logos
            query = f"parents='{logo_folder}' and mimeType contains 'image/' and trashed=false"
            results = self.handler.service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                pageSize=10
            ).execute()
            
            files = results.get('files', [])
            if not files:
                print("No logos found in logo folder")
                return None
            
            # print("IMAGE FILES", files)
            # Find specific logos by name
            for file in files:
                if 'dna' in file['name'].lower():
                    logos['dna'] = self._download_logo(file)
                elif 'company' in file['name'].lower():
                    logos['company'] = self._download_logo(file)
            
            return logos
            
        except Exception as e:
            print(f"Error getting logos: {str(e)}")
            return None

    def _download_logo(self, file):
        """Helper method to download and convert logo to base64."""
        try:
            request = self.handler.service.files().get_media(fileId=file['id'])
            logo_bytes = BytesIO()
            downloader = MediaIoBaseDownload(logo_bytes, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            # Return as base64 data URL
            logo_data = base64.b64encode(logo_bytes.getvalue()).decode()
            return f"data:{file['mimeType']};base64,{logo_data}"
            
        except Exception as e:
            print(f"Error downloading logo {file['name']}: {str(e)}")
            return None
        
    def create_template_content_html(self, template_dict):
        templates_html = ""

        for i, content in template_dict.items():
            content = content.replace('\n', '<br>')  # Convert newlines to <br> for HTML
            templates_html += f"<div class='template-block'>\n"
            # templates_html += f"<h2>{name}</h2>\n"
            templates_html += content  # assuming html_content is safe HTML
            templates_html += "</div>\n"

        return templates_html



    def generate_html(self, report_data):
        """Generate HTML content from template and report data."""
        try:
            # Get both logos
            logos = self.get_logos()

            # Read template
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Format samples and templates lists
            samples_html = '\n'.join([f'<a>{sample}</a>' for sample in report_data['selected_samples']])
            
            #Get template html content with assigned div for html
            templates_html = self.create_template_content_html(report_data['template_content_dict'])

            # Get company and DNA logos
            company_logo = logos['company'] if logos and 'company' in logos else ''
            dna_img = logos['dna'] if logos and 'dna' in logos else ''

            with open(self.stylesheet) as f:
                css = f.read()

            # Replace placeholders
            html_content = template.format(
                css = css,
                dna_img = dna_img,
                company_logo=company_logo,
                title=report_data['title'],
                project=report_data['project'],
                analysis_type=report_data['analysis_type'],
                reference=report_data['reference'] or 'None',
                samples=samples_html,
                templates=templates_html,
                conclusion=report_data['conclusion'],
                poi_prj_coord = report_data['coordinator'],
                poi_ngs_tech = report_data['ngs_tech'],
                email_prj_coord = report_data['coordinator_email'],
                email_ngs_tech = report_data['ngs_tech_email'],
                poi_client_appr = report_data['client_appr'],
                poi_client_rep = report_data['client_rep'],
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            # print(html_content)
            return html_content
            
        except Exception as e:
            print(f"Error generating HTML: {str(e)}")
            return None