import os
import json

class ConfigHandler:
    def __init__(self):
        self.config_dir = '/home/tanvi/Projects/Create_Report_GUI/configs'
        self.credentials_path = os.path.join(self.config_dir, 'credentials_tanvi.json')
        self.token_path = os.path.join(self.config_dir, 'token.pickle')
        self.folder_config_path = os.path.join(self.config_dir, 'folder_config.json')

    def get_credentials_path(self):
        if os.path.exists(self.credentials_path):
            return self.credentials_path
        raise FileNotFoundError("credentials.json not found in configs directory")

    def get_token_path(self):
        return self.token_path

    def get_folder_id(self):
        if os.path.exists(self.folder_config_path):
            with open(self.folder_config_path, 'r') as f:
                config = json.load(f)
                return config.get('folder_id')
        raise FileNotFoundError("folder_config.json not found in configs directory")
    

    def get_template_folder_id(self):
        """Get template folder ID from config."""
        if os.path.exists(self.folder_config_path):
            with open(self.folder_config_path, 'r') as f:
                config = json.load(f)
                return config.get('template_id')
        raise FileNotFoundError("folder_config.json not found in configs directory")
    
    def get_output_folder_id(self):
        """Get output folder ID from config."""
        if os.path.exists(self.folder_config_path):
            with open(self.folder_config_path, 'r') as f:
                config = json.load(f)
                return config.get('output_folder_id')
        raise FileNotFoundError("folder_config.json not found in configs directory")
    
    def get_finalreport_folder_id(self):
        """Get report folder ID from config."""
        if os.path.exists(self.folder_config_path):
            with open(self.folder_config_path, 'r') as f:
                config = json.load(f)
                return config.get('pdf_report_folder_id')
        raise FileNotFoundError("folder_config.json not found in configs directory")
    
    def get_logo_folder_id(self):
        """Get logo folder ID from config."""
        if os.path.exists(self.folder_config_path):
            with open(self.folder_config_path, 'r') as f:
                config = json.load(f)
                return config.get('logo_folder_id')
        raise FileNotFoundError("folder_config.json not found in configs directory")