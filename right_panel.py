from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QLabel, QScrollArea, QGroupBox,
                            QPushButton, QHBoxLayout, QMessageBox)
from PyQt5.QtCore import Qt
from Get_data_right_panel import RightPanelHandler
from googleapiclient.http import MediaIoBaseDownload
import io

class RightPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.right_panel_handler = RightPanelHandler()

    def init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create top header container
        header_layout = QHBoxLayout()
        
        # Create heading label
        heading_label = QLabel("Report Preview")
        heading_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(heading_label)
        
        # Add stretch to push button to right
        header_layout.addStretch()
        
        # Create View Report button
        self.view_btn = QPushButton("View Report")
        self.view_btn.clicked.connect(self.view_report)
        self.view_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        header_layout.addWidget(self.view_btn)
        
        # Add header to main layout
        layout.addLayout(header_layout)
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

        
    def view_report(self):
        """Handle View Report button click and display content."""
        try:
            if self.right_panel_handler.authenticate():
                print("Authentication successful")
                latest_file = self.right_panel_handler.get_latest_file()
                if latest_file:
                    print(f"Processing template list: {latest_file['name']}")
                    merged_doc_id = self.right_panel_handler.create_merged_document(latest_file['id'])
                    if merged_doc_id:
                        # Get content of merged document
                        merged_content = self.right_panel_handler.get_file_content(merged_doc_id)
                        if merged_content:
                            # Display content in preview
                            self.content_display.setText(merged_content)
                            QMessageBox.information(self, "Success", 
                                "Report merged successfully! Check the preview below.")
                        else:
                            QMessageBox.warning(self, "Error", 
                                "Failed to load merged document content.")
                    else:
                        QMessageBox.warning(self, "Error", 
                            "Failed to merge document. Check the console for details.")
                else:
                    QMessageBox.warning(self, "Error", 
                        "No template list found. Please create one first.")
            else:
                QMessageBox.critical(self, "Error", 
                    "Authentication failed. Check your credentials.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"An error occurred while creating the report: {str(e)}")

