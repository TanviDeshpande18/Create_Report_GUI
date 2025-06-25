from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QComboBox, 
                            QLabel, QCheckBox, QHBoxLayout, QGroupBox,
                            QRadioButton, QLineEdit)
import Get_data_left_panel as gd

class LeftPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("left_panel") 
        self.init_ui()

    def init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        ## Get data from Google Drive
        project_code_list, sample_name_list, references, company_poi, client_poi = gd.main()  # Call the main function from Get_data_left_panel
        self.full_sample_list = sample_name_list  # Store full list

        # Create heading label with larger font
        heading_label = QLabel("Enter Report Details")
        heading_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(heading_label)
        layout.addSpacing(20)


        # Create Project Code dropdown section
        project_label = QLabel("Select Project Code:")
        self.project_combo = QComboBox()
        self.project_combo.addItems(["None"]+ project_code_list)
        
        # Add spacing after project section
        layout.addWidget(project_label)
        layout.addWidget(self.project_combo)
        layout.addSpacing(20)  # Add 20 pixels of vertical spacing
        
        # Create Analysis Type group
        analysis_group = QGroupBox("Analysis Type")
        analysis_layout = QVBoxLayout()
        
        # Create radio buttons
        self.genome_radio = QRadioButton("Genome")
        self.transcriptome_radio = QRadioButton("Transcriptome")
        
        # Add radio buttons to layout
        analysis_layout.addWidget(self.genome_radio)
        analysis_layout.addWidget(self.transcriptome_radio)
        analysis_group.setLayout(analysis_layout)
        
        # Add analysis group and spacing
        layout.addWidget(analysis_group)
        layout.addSpacing(20)  # Add spacing after analysis group
        
        # Create Reference section with spacing
        reference_label = QLabel("Reference (if any):")
        self.reference_combo = QComboBox()
        self.reference_combo.addItems(["None"] + references)  # Add "None" option and references
        layout.addWidget(reference_label)
        layout.addWidget(self.reference_combo)
        layout.addSpacing(20)  # Add spacing after reference section
        
        # Create Sample Name group
        self.sample_group = QGroupBox("Sample Name:")
        self.sample_layout = QVBoxLayout()
        self.sample_group.setLayout(self.sample_layout)
        
        # Initialize empty dict for checkboxes
        self.sample_checkboxes = {}
        
        # Create a container widget for checkboxes
        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout()
        self.checkbox_container.setLayout(self.checkbox_layout)
        
        # Add checkbox container to sample layout
        self.sample_layout.addWidget(self.checkbox_container)
        
        # Add sample group to main layout
        layout.addWidget(self.sample_group)
        
        # Hide only the checkbox container initially
        self.checkbox_container.hide()

        # Create Report Title section
        layout.addSpacing(20) 
        title_label = QLabel("Report Title:")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter report title...")
        # self.title_input.textChanged.connect(self.on_title_changed)
        
        # Add title section to layout
        layout.addWidget(title_label)
        layout.addWidget(self.title_input)
        layout.addSpacing(50)  # Add spacing after title section

        ## Add 4 dropdown plus text input for adding names of all person of interest
        # Inhouse and client POI
        # 1. Inhouse POI 1
        poi1_label = QLabel("Project coordinator")
        self.poi1_dropdown = QComboBox()
        self.poi1_dropdown.setEditable(True)
        self.poi1_dropdown.addItems(['None']+ company_poi)
        self.poi1_dropdown.setPlaceholderText("Enter or select name...")
        layout.addWidget(poi1_label)
        layout.addWidget(self.poi1_dropdown)
        layout.addSpacing(10)

        # 2. Inhouse POI 2
        poi2_label = QLabel("NGS Technician")
        self.poi2_dropdown = QComboBox()
        self.poi2_dropdown.setEditable(True)
        self.poi2_dropdown.addItems(['None']+ company_poi)
        self.poi2_dropdown.setPlaceholderText("Enter or select name...")
        layout.addWidget(poi2_label)
        layout.addWidget(self.poi2_dropdown)
        layout.addSpacing(10)

        # 3. Client POI 1
        client_poi1_label = QLabel("Project approved by:")
        self.client_poi1_dropdown = QComboBox()
        self.client_poi1_dropdown.setEditable(True)
        self.client_poi1_dropdown.addItems(['None'] + client_poi)
        self.client_poi1_dropdown.setPlaceholderText("Enter or select name...")
        layout.addWidget(client_poi1_label)
        layout.addWidget(self.client_poi1_dropdown)
        layout.addSpacing(10)

        # 4. Client POI 2
        client_poi2_label = QLabel("Client representative")
        self.client_poi2_dropdown = QComboBox()
        self.client_poi2_dropdown.setEditable(True)
        self.client_poi2_dropdown.addItems(['None']+ client_poi)
        self.client_poi2_dropdown.setPlaceholderText("Enter or select name...")
        layout.addWidget(client_poi2_label)
        layout.addWidget(self.client_poi2_dropdown)
        layout.addSpacing(10)
        
        # Add stretch to push widgets to top
        layout.addStretch()

        # Connect signals
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        # self.genome_radio.toggled.connect(self.on_analysis_changed)
        # self.transcriptome_radio.toggled.connect(self.on_analysis_changed)
        # self.reference_combo.currentIndexChanged.connect(self.on_reference_changed)

    def on_project_changed(self, index):
        project_code = self.project_combo.currentText()
        # print(f"Selected project: {project_code}")
        
        # Clear existing checkboxes
        for checkbox in self.sample_checkboxes.values():
            self.checkbox_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.sample_checkboxes.clear()
        
        if project_code != "None":
            # Filter samples that start with the project code
            filtered_samples = [
                sample for sample in self.full_sample_list 
                if sample.startswith(project_code)
            ]
            
            # Create new checkboxes for filtered samples
            for sample_name in filtered_samples:
                checkbox = QCheckBox(sample_name)
                self.sample_checkboxes[sample_name] = checkbox
                self.checkbox_layout.addWidget(checkbox)
                # checkbox.stateChanged.connect(self.on_sample_changed)
            
            self.checkbox_container.show()
        else:
            self.checkbox_container.hide()

    # def on_sample_changed(self, state):
    #     checkbox = self.sender()
    #     print(f"Checkbox '{checkbox.text()}' state: {state}")

    # def on_analysis_changed(self):
    #     if self.genome_radio.isChecked():
    #         print("Analysis type: Genome")
    #     elif self.transcriptome_radio.isChecked():
    #         print("Analysis type: Transcriptome")

    # def on_reference_changed(self, index):
    #     print(f"Selected reference: {self.reference_combo.currentText()}")

    # def on_title_changed(self, text):
    #     """Handle report title changes."""
    #     print(f"Report title changed to: {text}")