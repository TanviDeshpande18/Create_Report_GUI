from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QCheckBox, 
                            QLabel, QPushButton, QGroupBox,
                            QDialog, QTextEdit, QMessageBox, QHBoxLayout)
from Get_data_middle_panel import TemplateHandler
from html_generator import HTMLGenerator
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
        self.setObjectName("middle_panel") 
        self.handler = TemplateHandler()  # Create single instance
        self.html_generator = HTMLGenerator()
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
        """Collect report data from both panels and validate."""
        try:
            # Get the main window and find left panel
            main_window = self.window()  # Get the top-level window
            left_panel = main_window.findChild(QWidget, "left_panel")
            right_panel = main_window.findChild(QWidget, "right_panel")
            
            if not all([left_panel, right_panel]):
                QMessageBox.critical(self, "Error", "Could not find required panels")
                return
            
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
            if not self.selected_templates:
                warnings.append("Please select at least one template")
            report_data['templates'] = [
                {'name': name, 'id': file_id}
                for name, file_id in self.selected_templates
            ]
            
            # If there are warnings, show them and return None
            if warnings:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Please fix the following issues:\n• " + "\n• ".join(warnings)
                )
                return None
                
            print(report_data)
                
        
            # Generate HTML content
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = self.html_generator.generate_html(report_data)
            if html_content:
                # Display in right panel
                right_panel.content_display.setHtml(html_content)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Success",
                    "Report preview generated successfully!"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to generate HTML content"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error creating report: {str(e)}"
            )
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MiddlePanelWidget()
    window.show()
    sys.exit(app.exec_())