from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QCheckBox, 
                            QLabel, QPushButton, QGroupBox,
                            QDialog, QTextEdit, QMessageBox, QHBoxLayout)
from Get_data_middle_panel import TemplateHandler
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from datetime import datetime
import io

class PreviewDialog(QDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(800, 600)

        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create text display with styling
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("QTextEdit { font-size: 12pt; padding: 10px; }")
        text_edit.setText(content)
        layout.addWidget(text_edit)

        # Add close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

class MiddlePanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.handler = TemplateHandler()  # Create single instance
        self.selected_templates = []  # Initialize selected_templates list
        self.init_ui()
        self.load_documents()

    def init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create heading label with larger font
        heading_label = QLabel("Select Templates for Report")
        heading_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(heading_label)
        layout.addSpacing(20)

        # Create template group box
        template_group = QGroupBox("Available Templates")
        template_layout = QVBoxLayout()
        template_group.setLayout(template_layout)

        # Create dictionary to store checkboxes
        self.template_checkboxes = {}
        
        # Add template group to main layout
        layout.addWidget(template_group)
        
        # Store template layout for later use
        self.template_layout = template_layout

        # Add refresh button
        refresh_btn = QPushButton("Refresh Templates")
        refresh_btn.clicked.connect(self.load_documents)
        layout.addWidget(refresh_btn)  

        # Add buttons container
        button_layout = QHBoxLayout()      
        
        # Add Create Report button
        create_report_btn = QPushButton("Create Report")
        create_report_btn.clicked.connect(self.create_report)
        create_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(create_report_btn)

        # Add button layout to main layout
        layout.addLayout(button_layout)
        
        # Add stretch to push widgets to top
        layout.addStretch()

    def load_documents(self):
        """Load document files from Google Drive template folder"""
        if self.handler.authenticate():
            files = self.handler.get_template_files()
            
            # Clear existing checkboxes
            for checkbox in self.template_checkboxes.values():
                checkbox.deleteLater()
            self.template_checkboxes.clear()
            
            # Add template files as checkboxes
            for file in files:
                checkbox = QCheckBox(file['name'])
                checkbox.setObjectName(file['id'])  # Store file ID in object name
                checkbox.stateChanged.connect(self.on_checkbox_changed)
                self.template_checkboxes[file['id']] = checkbox
                self.template_layout.addWidget(checkbox)

    def show_template_preview(self, name, file_id):
        """Show preview for a single template"""
        try:
            # Get file metadata
            file = self.handler.service.files().get(
                fileId=file_id, 
                fields='name,mimeType'
            ).execute()

            # Get content based on file type
            if file['mimeType'] == 'application/vnd.google-apps.document':
                content = self.handler.service.files().export(
                    fileId=file_id,
                    mimeType='text/plain'
                ).execute()
                text_content = content.decode('utf-8')
            else:
                request = self.handler.service.files().get_media(fileId=file_id)
                file_content = io.BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                text_content = file_content.getvalue().decode('utf-8')

            # Create and show preview dialog
            dialog = PreviewDialog(f"Preview: {name}", text_content, self)
            dialog.exec_()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading template {name}: {str(e)}")

    def on_checkbox_changed(self, state):
        """Handle checkbox state changes"""
        checkbox = self.sender()
        if state:  # Checked
            self.selected_templates.append((checkbox.text(), checkbox.objectName()))
            self.show_template_preview(checkbox.text(), checkbox.objectName())
        else:  # Unchecked
            self.selected_templates = [t for t in self.selected_templates 
                                     if t[1] != checkbox.objectName()]
        print(f"Template '{checkbox.text()}' {'selected' if state else 'unselected'}")

    def create_report(self):
        """Create a new report from selected templates"""
        if not self.selected_templates:
            QMessageBox.warning(self, "Error", "Please select at least one template")
            return

        try:
            # Create a new Google Doc
            file_metadata = {
                'name': f'Generated Report {datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'mimeType': 'application/vnd.google-apps.document',
                'parents': [self.handler.config.get_output_folder_id()]  # Get output folder ID from config
            }

            # Create empty document
            file = self.handler.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            # Append content from each selected template
            combined_content = []
            for template_name, template_id in self.selected_templates:
                try:
                    content = self.handler.service.files().export(
                        fileId=template_id,
                        mimeType='text/plain'
                    ).execute()
                    combined_content.append(content.decode('utf-8'))
                except Exception as e:
                    print(f"Error reading template {template_name}: {str(e)}")

            # Update the new document with combined content
            self.handler.service.files().update(
                fileId=file['id'],
                media_body=MediaIoBaseUpload(
                    io.BytesIO('\n\n'.join(combined_content).encode('utf-8')),
                    mimetype='text/plain'
                )
            ).execute()

            QMessageBox.information(
                self, 
                "Success", 
                f"Report created successfully!\nTemplates used: {len(self.selected_templates)}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create report: {str(e)}")

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MiddlePanelWidget()
    window.show()
    sys.exit(app.exec_())