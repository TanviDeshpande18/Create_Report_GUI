from datetime import datetime
import os
import math
import base64
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload
from Get_data_middle_panel import TemplateHandler

class DNAGI_HTMLGenerator:
    def __init__(self):
        self.template_path = os.path.join(os.path.dirname(__file__), 'templates/dnagenome_integrity_report_template.html')
        self.stylesheet = os.path.join(os.path.dirname(__file__), 'static/dnagi_style.css')
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
        
    def create_template_content_html(self, template_dict, company_logo):
        #Below are variables used to calcultae how many lines fit on a page
        #Bigger line take up more rows of html, to take that into account. we need to see how many characters fit on a line
        lines_fit_on_1_page = 40
        characters_on_1_line = 72
        next_section_continue_cutoff = 30
        templates_html = ""

        def add_header_logo():
            template = "<div class='a4-container'>\n \
                        <div class='flex-rows'>\n \
                        <div class='page-header'>\n"
            template += f"<img src='{company_logo}' alt='Sample Image 2' class='logo-header'>\n \
                        </div>"

            return template
        
        def add_footer():
            template = "<div class='page-footer'>\n \
                        <p style='color: gray; text-align: right;'>2020 Epidote Healthcare LLP </p>\n \
                        </div>"
            return template
        
        current_line = 0
        # print("TEMPLATE DICT", template_dict)
        # Iterate through the template dictionary
        # template_dict is expected to be a dictionary with keys as template numbers and values as content
        # Each content is expected to be a string with the first line as title and the rest as text body
        if len(template_dict) != 0:
            for i, content in template_dict.items():
                content = content.strip().splitlines()  # Clean up whitespace and newlines and split into lines            
                title,text_body = content[0].replace("Title: ", ""), content[1:]
                # print("TITLE", title)
                # print("TEXT BODY", text_body)
                # text_body = text_body.replace('\n', '<br>')  # Convert newlines to <br> for HTML
                if i == 1:
                    templates_html += add_header_logo()
                    templates_html += "<div class='page-body'>\n"
                else:
                    # Check how much space is left on the page, if there are only few lines, go to next page
                    if current_line >= next_section_continue_cutoff:
                        # close current template block and page body
                        templates_html += "</div>\n</div>\n"
                        templates_html += add_footer()
                        # Close flex-rows and a4-container divs
                        templates_html += "</div>\n</div>\n"
                        templates_html += add_header_logo()
                        templates_html += "<div class='page-body'>\n"
                        current_line = 0  
                    else:
                        # Close template block of previous template
                        templates_html += "</div>\n"

                # Add title
                templates_html += "<div class='template-title'>\n"
                templates_html += f"<h3>{title}</h3>\n"
                templates_html += "</div>\n"
                current_line += 1


                # Add line by line text body
                templates_html += "<div class='template-block'>\n"
                for line in text_body:

                    if line.strip() == "":
                        current_line += 1  # Empty line counts as a line
                    else:
                        ## Here you need to add a check if the next line that you are adding will fit the remaining space on the page
                        # Need to calculate math.ceil(len(line) / characters_on_1_line) to see how many lines it will take
                        # if more than remaining lines, go to next page
                        space_needed = math.ceil(len(line) / characters_on_1_line)
                        if current_line + space_needed < lines_fit_on_1_page:       
                            # If it fits, add the line
                            current_line += space_needed  
                        else:
                            # close current template block and page body
                            templates_html += "</div>\n</div>\n"
                            templates_html += add_footer()
                            # Close flex-rows and a4-container divs
                            templates_html += "</div>\n</div>\n"
                            templates_html += add_header_logo()
                            templates_html += "<div class='page-body'>\n"
                            templates_html += "<div class='template-block'>\n"
                            current_line = 0    
                    templates_html += f"<p>{line}</p>\n"
                templates_html += "<br><br>"
                current_line += 2

            #Close the last template block and page body
            templates_html += "</div>\n</div>\n"
            templates_html += add_footer()
            # Close flex-rows and a4-container divs
            templates_html += "</div>\n</div>\n"
    

        # print(templates_html)
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

            # Get company and DNA logos
            company_logo = logos['company'] if logos and 'company' in logos else ''
            dna_img = logos['dna'] if logos and 'dna' in logos else ''
            
            #Get template html content with assigned div for html
            templates_html = self.create_template_content_html(report_data['template_content_dict'],company_logo)

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