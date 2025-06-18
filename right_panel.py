from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QLabel, QScrollArea, QGroupBox,
                            QPushButton, QHBoxLayout, QMessageBox,
                            QFileDialog)
from PyQt5.QtPrintSupport import QPrinter  # Add for PDF export
from PyQt5.QtCore import Qt, QMarginsF
from PyQt5.QtGui import QTextDocument
from Get_data_right_panel import RightPanelHandler
from googleapiclient.http import MediaIoBaseDownload
import io
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt
from html.parser import HTMLParser
from io import StringIO



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
        # Initialize handler after UI
        self.right_panel_handler = RightPanelHandler()
        
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
        
        # # Create View Report button
        # self.view_btn = QPushButton("View Report")
        # self.view_btn.clicked.connect(self.view_report)
        # self.view_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #2196F3;
        #         color: white;
        #         padding: 5px 15px;
        #         border-radius: 3px;
        #         font-weight: bold;
        #     }
        #     QPushButton:hover {
        #         background-color: #1976D2;
        #     }
        # """)
        # header_layout.addWidget(self.view_btn)

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
