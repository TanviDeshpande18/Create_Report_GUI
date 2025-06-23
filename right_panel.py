from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QLabel, QScrollArea, QGroupBox,
                            QPushButton, QHBoxLayout, QMessageBox,
                            QFileDialog)
from PyQt5.QtPrintSupport import QPrinter  # Add for PDF export
from PyQt5.QtCore import Qt, QMarginsF
from PyQt5.QtGui import QTextDocument
from config_handler import ConfigHandler
from Get_data_right_panel import RightPanelHandler
from html_generator import HTMLGenerator
import serve_html_content as serve_html
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt
from html.parser import HTMLParser
from io import StringIO
import tempfile
import webbrowser



# Add new HTMLParser subclass after imports
class HTMLToDocxParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = StringIO()
        
    def handle_data(self, data):
        self.text.write(data)
        
    def get_text(self):
        return self.text.getvalue()


class RightPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setObjectName("right_panel") 
        self.html_generator = HTMLGenerator()
        self.handler = RightPanelHandler()
        # Initialize handler after UI
        self.config_handler = ConfigHandler()
        
    def init_ui(self):
        # Create main layout once
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Create top header container
        header_layout = QHBoxLayout()
        
        # Create heading label
        heading_label = QLabel("Report Preview")
        heading_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(heading_label)
        
        # Add stretch to push button to right
        header_layout.addStretch()
        
        # Add Create Report button to header
        create_report_btn = QPushButton("Create Report")
        create_report_btn.clicked.connect(self.create_report)
        create_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        header_layout.addWidget(create_report_btn)

        # Create Export PDF button
        self.export_btn = QPushButton("Export PDF")
        self.export_btn.clicked.connect(self.export_to_pdf)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        header_layout.addWidget(self.export_btn)

        # Create Export DOCX button
        self.export_docx_btn = QPushButton("Export DOCX")
        self.export_docx_btn.clicked.connect(self.export_to_docx)
        self.export_docx_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        header_layout.addWidget(self.export_docx_btn)
      
        # Add header to main layout
        self.main_layout.addLayout(header_layout)
        self.main_layout.addSpacing(20)

        # Create preview group box with scroll area
        preview_group = QGroupBox("Document Content")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)

        # Create text edit for content display
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        preview_layout.addWidget(self.content_display)

        # Add preview group to main layout
        self.main_layout.addWidget(preview_group)

    def export_to_pdf(self):
        """Export the current content to PDF."""
        try:
            # Get save location from user
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Export PDF",
                f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if file_name:
                # Create printer object
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_name)
                
                # Set margins in millimeters
                printer.setPageMargins(20, 20, 20, 20, QPrinter.Millimeter)
                
                # Create document and print
                document = QTextDocument()
                document.setHtml(self.content_display.toHtml())
                document.print_(printer)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"PDF exported successfully to:\n{file_name}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export PDF: {str(e)}"
            )

    def export_to_docx(self):
        """Export the current content to DOCX format."""
        try:
            # Get save location from user
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Export DOCX",
                f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                "Word Documents (*.docx)"
            )
            
            if file_name:
                # Create new document
                doc = Document()
                
                # Configure basic document styles
                style = doc.styles['Normal']
                style.font.name = 'Arial'
                style.font.size = Pt(11)
                
                # Get HTML content and convert to text
                html_content = self.content_display.toHtml()
                parser = HTMLToDocxParser()
                parser.feed(html_content)
                text_content = parser.get_text()
                
                # Add content to document
                # Split by newlines to handle paragraphs
                for paragraph in text_content.split('\n'):
                    if paragraph.strip():
                        doc.add_paragraph(paragraph.strip())
                
                # Save the document
                doc.save(file_name)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Document exported successfully to:\n{file_name}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export DOCX: {str(e)}"
            )

    def create_report(self):
        """Collect report data from both panels and validate."""
        try:
            # Get the main window and find left panel
            main_window = self.window()  # Get the top-level window
            left_panel = main_window.findChild(QWidget, "left_panel")
            middle_panel = main_window.findChild(QWidget, "middle_panel")
            right_panel = main_window.findChild(QWidget, "right_panel")
            
            if not all([left_panel, middle_panel, right_panel]):
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
            if not middle_panel.selected_templates:
                warnings.append("Please select at least one template")
            report_data['templates'] = [
                {'name': name, 'id': file_id}
                for name, file_id in middle_panel.selected_templates
            ]

            # Add conclusion to report data
            report_data['conclusion'] = middle_panel.conclusion_text.toPlainText()
            
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
                # Prepare in-memory file for upload
                html_bytes = io.BytesIO(html_content.encode('utf-8'))

                # Set your Google Drive folder ID here
                html_output_folder_id = self.config_handler.get_html_folder_id()

                file_metadata = {
                    'name': f"{report_data['title']}.html",
                    'parents': [html_output_folder_id],
                    'mimeType': 'text/html'
                }
                media = MediaIoBaseUpload(html_bytes, mimetype='text/html', resumable=False)

                if not self.handler.authenticate():
                    QMessageBox.critical(self, "Error", "Google Drive authentication failed.")
                    return

                uploaded_file = self.handler.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()

                # Serve HTML safely
                serve_html.serve_html_safely(html_content, serve_time=10)
                # web_link = uploaded_file.get('webViewLink')
                # # print(f"HTML file uploaded to Drive. View at: {web_link}")

                # # Open the uploaded HTML file in the default web browser
                # webbrowser.open(web_link)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Report uploaded to Google Drive!"
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
