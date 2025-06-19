import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                            QDesktopWidget, QSplitter, QScrollArea, QVBoxLayout)
from PyQt5.QtCore import Qt
from left_panel import LeftPanelWidget
from middle_panel import MiddlePanelWidget
from right_panel import RightPanelWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Report Maker")
        
        # Get the screen geometry
        screen = QDesktopWidget().screenGeometry()
        width = screen.width()
        height = screen.height()
        
        # Set window size to screen size
        self.setGeometry(0, 0, width, height)

        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # Create three empty panels
        left_panel = LeftPanelWidget() 
        middle_panel = MiddlePanelWidget()
        
        # Create right panel with scroll area
        right_panel = RightPanelWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)
        
        # Add the content widget to scroll area
        scroll.setWidget(scroll_content)
        
        # Add scroll area to right panel
        right_layout.addWidget(scroll)

        # Add background colors to distinguish panels (optional)
        # left_panel.setStyleSheet("background-color: #f0f0f0;")
        # middle_panel.setStyleSheet("background-color: #e0e0e0;")
        # right_panel.setStyleSheet("background-color: #f0f0f0;")

        # Add widgets to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)

        # Set initial sizes for the three panels (33% each)
        splitter.setSizes([int(width * 0.25), int(width * 0.35), int(width * 0.40)])
        
        # Store references for later use
        self.scroll_layout = scroll_layout
        self.scroll_content = scroll_content

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()