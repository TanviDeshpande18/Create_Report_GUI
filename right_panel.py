from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QLabel, QScrollArea, QGroupBox,
                            QPushButton, QHBoxLayout, QMessageBox,
                            QFileDialog)
from PyQt5.QtPrintSupport import QPrinter  # Add for PDF export
from PyQt5.QtCore import Qt, QMarginsF
from PyQt5.QtGui import QTextDocument
from config_handler import ConfigHandler
from Get_data_right_panel import RightPanelHandler
from dnagenome_integrity_html_generator import DNAGI_HTMLGenerator
from adventitious_html_generator import AD_HTMLGenerator
from validation_html_generator import VAL_HTMLGenerator
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
from PyQt5.QtWidgets import QApplication, QComboBox, QLineEdit
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtCore import QUrl, QEventLoop
import sys


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
        # Initialize HTML generators
        self.dnagi_html_generator = DNAGI_HTMLGenerator()  # Default to DNA Genome Integrity
        self.ad_html_generator = AD_HTMLGenerator()
        self.val_html_generator = VAL_HTMLGenerator()

        self.handler = RightPanelHandler()
        # Initialize handler after UI
        self.config_handler = ConfigHandler()
        
    def init_ui(self):
        # Create main layout once
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create top header container
        header_layout = QHBoxLayout()
        
        # Create heading label
        heading_label = QLabel("Miscellanous Options")
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

        # # Create Export DOCX button
        # self.export_docx_btn = QPushButton("Export DOCX")
        # self.export_docx_btn.clicked.connect(self.export_to_docx)
        # self.export_docx_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #2196F3;
        #         color: white;
        #         padding: 5px 15px;
        #         border-radius: 3px;
        #         font-weight: bold;
        #         margin-left: 10px;
        #     }
        #     QPushButton:hover {
        #         background-color: #1976D2;
        #     }
        # """)
        # header_layout.addWidget(self.export_docx_btn)
      
        # Add header to main layout
        layout.addLayout(header_layout)
        layout.addSpacing(20)

        # Add conclusion section
        conclusion_group = QGroupBox("Conclusion")
        conclusion_layout = QVBoxLayout()
        
        self.conclusion_text = QTextEdit()
        self.conclusion_text.setPlaceholderText("Enter your conclusion here...")
        self.conclusion_text.setMinimumHeight(50)
        self.conclusion_text.setMaximumHeight(400)
        conclusion_layout.addWidget(self.conclusion_text)
        
        conclusion_group.setLayout(conclusion_layout)
        conclusion_group.setMaximumHeight(400)
        layout.addWidget(conclusion_group)  

        ## Add appendix section 
        appendix_group = QGroupBox("Add Appendix")
        appendix_layout = QVBoxLayout()
        appendix_layout.setAlignment(Qt.AlignTop)  # Keep content at the top

        # Container to hold all appendix combos
        self.appendix_combos_layout = QVBoxLayout()
        self.appendix_combos_layout.setAlignment(Qt.AlignTop)
        appendix_layout.addLayout(self.appendix_combos_layout)

        # Add first combo
        self.add_appendix_combo()

        # Plus button to add more combos
        add_appendix_btn = QPushButton("Add Appendix +")
        add_appendix_btn.setFixedWidth(120)
        add_appendix_btn.clicked.connect(self.add_appendix_combo)
        appendix_layout.addWidget(add_appendix_btn, alignment=Qt.AlignLeft)

        appendix_group.setLayout(appendix_layout)
        layout.addWidget(appendix_group)

    def add_appendix_combo(self):
        """Add a new combo of text box and dropdown to the appendix section, with dropdown on the next line, a remove button, and a dynamic title."""
        # Count current appendix widgets to determine the number
        count = self.appendix_combos_layout.count() + 1
        appendix_titles = [
            "Appendix 1", "Appendix 2", "Appendix 3", "Appendix 4", "Appendix 5",
            "Appendix 6", "Appendix 7", "Appendix 8", "Appendix 9", "Appendix 10"
        ]
        title = appendix_titles[count - 1] if count <= len(appendix_titles) else f"Appendix {count}"

        combo_widget = QWidget()
        combo_layout = QVBoxLayout(combo_widget)
        combo_layout.setContentsMargins(0, 0, 0, 0)

        # Add the title label
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        combo_layout.addWidget(title_label)

        textbox = QLineEdit()
        textbox.setPlaceholderText("Appendix text")
        dropdown = QComboBox()
        dropdown.addItems(["Option 1", "Option 2", "Option 3"])  # Customize as needed

        # Remove button
        remove_btn = QPushButton("−")
        remove_btn.setFixedWidth(30)
        remove_btn.setToolTip("Remove this appendix")
        remove_btn.clicked.connect(lambda: self.remove_appendix_combo(combo_widget))

        # Layout for dropdown and remove button on the same row
        dropdown_row = QHBoxLayout()
        dropdown_row.addWidget(dropdown)
        dropdown_row.addWidget(remove_btn)
        dropdown_row.addStretch()

        combo_layout.addWidget(textbox)
        combo_layout.addLayout(dropdown_row)

        self.appendix_combos_layout.addWidget(combo_widget)

    def remove_appendix_combo(self, widget):
        """Remove the given appendix combo widget."""
        self.appendix_combos_layout.removeWidget(widget)
        widget.setParent(None)


    def export_to_pdf(self):
        """Export the latest HTML content to PDF using QWebEnginePage."""
        try:
            html_content = self.get_data_and_html_content()
            if not html_content:
                return

            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Export PDF",
                f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )
            if not file_name:
                return

            # Use QWebEnginePage to render and print to PDF
            page = QWebEnginePage()
            loop = QEventLoop()

            def on_pdf_written(path):
                loop.quit()
                QMessageBox.information(
                    self,
                    "Success",
                    f"PDF exported successfully to:\n{file_name}"
                )

            def on_load_finished(ok):
                if ok:
                    page.printToPdf(file_name)
                    page.pdfPrintingFinished.connect(on_pdf_written)
                else:
                    QMessageBox.critical(self, "Error", "Failed to load HTML for PDF export.")
                    loop.quit()

            page.loadFinished.connect(on_load_finished)
            page.setHtml(html_content, QUrl("file:///"))  # base URL for relative paths
            loop.exec_()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export PDF: {str(e)}"
            )


    def get_data_and_html_content(self):
        """Collect report data from both panels and validate."""
        try:
            # Get the main window and find left panel
            main_window = self.window()  # Get the top-level window
            left_panel = main_window.findChild(QWidget, "left_panel")
            middle_panel = main_window.findChild(QWidget, "middle_panel")
            right_panel = main_window.findChild(QWidget, "right_panel")

            report_data, warnings = self.handler.collect_report_data(left_panel, middle_panel, right_panel)
                        
            # If there are warnings, show them and return None
            if warnings:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Please fix the following issues:\n• " + "\n• ".join(warnings)
                )
                return None          
        
            # Generate HTML content 
            if report_data['report_type'] == "DNA Genome Integrity":
                html_content = self.dnagi_html_generator.generate_html(report_data)
            elif report_data['report_type'] == "Adventitious Agent Detection":
                html_content = self.ad_html_generator.generate_html(report_data)
            elif report_data['report_type'] == "PhiX Validation":        
                html_content = self.val_html_generator.generate_html(report_data)
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Please select a valid report type"
                )
                return None

            return html_content

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error creating report: {str(e)}"
            )        

    def create_report(self):
        # Get HTML content and report data
        html_content = self.get_data_and_html_content()

        if html_content:
            # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # # Prepare in-memory file for upload
            # html_bytes = io.BytesIO(html_content.encode('utf-8'))

            # # Set your Google Drive folder ID here
            # html_output_folder_id = self.config_handler.get_html_folder_id()

            # file_metadata = {
            #     'name': f"{str(timestamp)}.html",
            #     'parents': [html_output_folder_id],
            #     'mimeType': 'text/html'
            # }
            # media = MediaIoBaseUpload(html_bytes, mimetype='text/html', resumable=False)

            # if not self.handler.authenticate():
            #     QMessageBox.critical(self, "Error", "Google Drive authentication failed.")
            #     return

            # uploaded_file = self.handler.drive_service.files().create(
            #     body=file_metadata,
            #     media_body=media,
            #     fields='id, webViewLink'
            # ).execute()

            # QMessageBox.information(
            #     self,
            #     "Success",
            #     f"Report uploaded to Google Drive!"
            # )

            # Serve HTML safely
            serve_html.serve_html_safely(html_content)

        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to generate HTML content"
            )



