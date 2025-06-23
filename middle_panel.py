from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QCheckBox, 
                            QLabel, QPushButton, QGroupBox,
                            QDialog, QTextEdit, QMessageBox, QHBoxLayout,
                            QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt
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
        self.setObjectName("middle_panel") 
        self.handler = TemplateHandler()  # Create single instance        
        self.selected_templates = []  # Initialize selected_templates list
        self.init_ui()
        self.load_documents()

    def init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create header container
        header_layout = QHBoxLayout()

        # Create heading label with larger font
        heading_label = QLabel("Select Templates for Report")
        heading_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(heading_label)
        header_layout.addStretch()  # Add stretch to push button to right
    
        # Add header layout to main layout
        layout.addLayout(header_layout)
        layout.addSpacing(20)

        # Create template group box
        template_group = QGroupBox("Available Templates")
        template_group_layout = QVBoxLayout()
        template_group.setLayout(template_group_layout)
        template_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        template_group.setMinimumHeight(int(self.height() * 1.2))  

        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFixedHeight(int(self.height() * 1.2))

        # Create container for templates
        self.template_container = QWidget()
        self.template_layout = QVBoxLayout(self.template_container)
        self.template_container.setLayout(self.template_layout)

        # Set container in scroll area
        scroll_area.setWidget(self.template_container)
        
        # Add scroll area to group layout
        template_group_layout.addWidget(scroll_area)
        
        # Add template group to main layout
        layout.addWidget(template_group)

        # Create dictionary to store checkboxes
        self.template_checkboxes = {}        
        
        # Add refresh button
        refresh_btn = QPushButton("Refresh Templates")
        refresh_btn.clicked.connect(self.load_documents)
        layout.addWidget(refresh_btn) 
        # layout.addSpacing(20) 


        # Add conclusion section
        conclusion_group = QGroupBox("Conclusion")
        conclusion_layout = QVBoxLayout()
        
        self.conclusion_text = QTextEdit()
        self.conclusion_text.setPlaceholderText("Enter your conclusion here...")
        self.conclusion_text.setMinimumHeight(50)
        conclusion_layout.addWidget(self.conclusion_text)
        
        conclusion_group.setLayout(conclusion_layout)
        layout.addWidget(conclusion_group)   
        
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
                checkbox.setObjectName(file['id'])
                checkbox.stateChanged.connect(self.on_checkbox_changed)
                self.template_checkboxes[file['id']] = checkbox
                self.template_layout.addWidget(checkbox)
            
            # Add stretch at the end
            self.template_layout.addStretch()

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



if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MiddlePanelWidget()
    window.show()
    sys.exit(app.exec_())