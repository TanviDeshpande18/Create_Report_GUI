from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QLabel, QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt
from Get_data_middle_panel import TemplateHandler
from googleapiclient.http import MediaIoBaseDownload
import io

class RightPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.template_handler = TemplateHandler()

    def init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create heading label
        heading_label = QLabel("Report Preview")
        heading_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(heading_label)
        layout.addSpacing(20)

        # Create preview group box
        preview_group = QGroupBox("Document Content")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)

        # Create text edit for content display
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        preview_layout.addWidget(self.content_display)

        # Add preview group to main layout
        layout.addWidget(preview_group)

    def display_template_content(self, file_id):
        """Display the content of the selected template"""
        if not file_id:
            self.content_display.clear()
            return

        try:
            if self.template_handler.authenticate():
                # Get file metadata
                file = self.template_handler.service.files().get(
                    fileId=file_id, 
                    fields='name,mimeType'
                ).execute()

                # For Google Docs
                if file['mimeType'] == 'application/vnd.google-apps.document':
                    content = self.template_handler.service.files().export(
                        fileId=file_id,
                        mimeType='text/plain'
                    ).execute()
                    text_content = content.decode('utf-8')
                else:
                    # For other document types
                    request = self.template_handler.service.files().get_media(fileId=file_id)
                    file_content = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_content, request)
                    done = False
                    while not done:
                        _, done = downloader.next_chunk()
                    text_content = file_content.getvalue().decode('utf-8')

                # Display content
                self.content_display.setText(text_content)
                self.content_display.setDocumentTitle(file['name'])

        except Exception as e:
            self.content_display.setText(f"Error loading template content: {str(e)}")