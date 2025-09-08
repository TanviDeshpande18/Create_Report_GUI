from datetime import datetime
import os
import math
import base64
import json
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload
from Get_data_middle_panel import TemplateHandler

class VAL_HTMLGenerator:
    def __init__(self):
        self.template_path = os.path.join(os.path.dirname(__file__), 'templates/validation_report_template.html')
        self.stylesheet = os.path.join(os.path.dirname(__file__), 'static/val_style.css')
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
                    logos['dna'] = self._download_file(file,"image")
                elif 'company' in file['name'].lower():
                    logos['company'] = self._download_file(file,"image")
            
            return logos
            
        except Exception as e:
            print(f"Error getting logos: {str(e)}")
            return None
        
    def get_val_data_images_and_json(self, project_name):
        try:
            valdata_folder = self.handler.config.get_validation_data_folder_id()
            data_images = {}
            json_data = {}
            
            # Query for both logos
            query = (
                f"'{valdata_folder}' in parents and "
                "(mimeType contains 'image/' or mimeType = 'application/json') and trashed=false"
            )
            results = self.handler.service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                pageSize=10
            ).execute()
            
            files = results.get('files', [])
            # print("FILES", files)
            if not files:
                print("No logos found in logo folder")
                return None
            
            # print("IMAGE FILES", files)
            # Find specific logos by name
            for file in files:
                if file['name'].lower().startswith(project_name.lower()):
                    if 'adapter_content' in file['name'].lower():
                        data_images['adapter_content'] = self._download_file(file,"image")
                    elif 'average_base_calling_accuracy' in file['name'].lower():
                        data_images['average_base_calling_accuracy'] = self._download_file(file,"image")
                    elif 'basecoverage' in file['name'].lower():
                        data_images['basecoverage'] = self._download_file(file,"image")
                    elif 'per_base_quality' in file['name'].lower():
                        data_images['per_base_quality'] = self._download_file(file,"image")
                    elif file['name'].lower().endswith('validation_data.json'):
                        json_data = self._download_file(file,"json")
            
            print("json_data", json_data)
            return data_images,json_data
            
        except Exception as e:
            print(f"Error getting logos: {str(e)}")
            return None
        

    def _download_file(self, file,what):
        """Helper method to download and convert logo to base64."""
        try:
            request = self.handler.service.files().get_media(fileId=file['id'])
            file_bytes = BytesIO()
            downloader = MediaIoBaseDownload(file_bytes, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            # Return as base64 data URL
            if what == 'image':
                logo_data = base64.b64encode(file_bytes.getvalue()).decode()
                return f"data:{file['mimeType']};base64,{logo_data}"
            elif what == 'json':
                file_bytes.seek(0)
                return json.load(file_bytes)    
            
        except Exception as e:
            print(f"Error downloading logo {file['name']}: {str(e)}")
            return None        


    def generate_html(self, report_data):
        """Generate HTML content from template and report data."""
        try:
            # Get both logos
            logos = self.get_logos()

            # Get data images and validation json with all values for the report                                                                                     
            val_data_images, val_json = self.get_val_data_images_and_json(report_data['project'])

            # Read template
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Format samples and templates lists
            samples_list = report_data.get('selected_samples')
            samples_list = [x.split(' (')[1].strip(')') for x in samples_list]
            samples_html = '\n'.join([f'<a>{sample}</a>' for sample in samples_list])

            # Get company and DNA logos
            company_logo = logos['company'] if logos and 'company' in logos else ''
            dna_img = logos['dna'] if logos and 'dna' in logos else ''

            # Get data images
            adapter_content_img = val_data_images['adapter_content'] if val_data_images and 'adapter_content' in val_data_images else ''
            average_base_calling_accuracy_img = val_data_images['average_base_calling_accuracy'] if val_data_images and 'average_base_calling_accuracy' in val_data_images else ''
            basecoverage_img = val_data_images['basecoverage'] if val_data_images and 'basecoverage' in val_data_images else ''
            per_base_quality_img = val_data_images['per_base_quality'] if val_data_images and 'per_base_quality' in val_data_images else '' 

            # Calculate Statistics for the report
            #Number of bases sequenced in Mb = number of reads (in fastqc file) x 2 (if paired end) x read length (in fastqc file) bases ---- convert to Mb
            bases_sequenced_bp = val_json['Number_of_reads'] * val_json['Paired_end']
            bases_sequenced_in_Mb = ((val_json['Number_of_reads'] * val_json['Paired_end'] * val_json['Read_length']) / 1e6)
            total_number_of_bases = val_json['Read_length'] * val_json['Number_of_reads'] * val_json['Paired_end']
            expected_coverage = total_number_of_bases / (val_json['Genome_size_Kb'] * 1e3)
            #X coverage of sequenced data =( Number of bases sequenced in Mb (above calc) * 1000000  (if converted to Mb)) / Genome size in bp (in json file)
            coverage = (bases_sequenced_in_Mb * 1e6) / (val_json['Genome_size_Kb'] * 1e3)
            

            with open(self.stylesheet) as f:
                css = f.read()

            # Replace placeholders
            html_content = template.format(
                css = css,
                dna_img = dna_img,
                company_logo=company_logo,

                # Data numbers and images
                run = val_json['Run'],
                flow_cell = val_json['Flow_cell'],
                run_date = val_json['Run_date'],
                tech = val_json['Technician'],
                genome_size = val_json['Genome_size_Kb'],
                genome_size_in_bp  = val_json['Genome_size_Kb'] * 1e3,
                bases_sequenced_in_Mb = round(bases_sequenced_in_Mb,2),
                
                coverage =round(coverage,2),
                alignment_stats = val_json['Alignment_statistics'].replace('\n', '<br><br>'),
                read_length = val_json['Read_length'],
                bases_sequenced_bp = bases_sequenced_bp,
                total_number_of_bases = total_number_of_bases,
                expected_coverage = round(expected_coverage,2),

                adapter_content_img=adapter_content_img,
                average_base_calling_accuracy_img=average_base_calling_accuracy_img,
                basecoverage_img=basecoverage_img,
                per_base_quality_img=per_base_quality_img,
                val_json=val_json,


                title=report_data['title'],
                project=report_data['project'],
                analysis_type=report_data['analysis_type'],
                reference=report_data['reference'] or 'None',
                samples=samples_html,
                # templates=templates_html,
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