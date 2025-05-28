from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QComboBox, 
                            QLabel, QCheckBox, QHBoxLayout, QGroupBox,
                            QRadioButton)
import Get_data_left_panel as gd

class LeftPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        ## Get data from Google Drive
        project_code_list, sample_name_list, references = gd.main()  # Call the main function from Get_data_left_panel

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
        sample_group = QGroupBox("Sample Name:")
        sample_layout = QVBoxLayout()
        
        # Create checkboxes dynamically from sample_name_list
        self.sample_checkboxes = {}
        for sample_name in sample_name_list:
            checkbox = QCheckBox(sample_name)
            self.sample_checkboxes[sample_name] = checkbox
            sample_layout.addWidget(checkbox)
            checkbox.stateChanged.connect(self.on_sample_changed)
            
        sample_group.setLayout(sample_layout)
        
        # Add sample group to main layout
        layout.addWidget(sample_group)
        
        # Add stretch to push widgets to top
        layout.addStretch()

        # Connect signals
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        self.genome_radio.toggled.connect(self.on_analysis_changed)
        self.transcriptome_radio.toggled.connect(self.on_analysis_changed)
        self.reference_combo.currentIndexChanged.connect(self.on_reference_changed)

    def on_project_changed(self, index):
        print(f"Selected project: {self.project_combo.currentText()}")

    def on_sample_changed(self, state):
        checkbox = self.sender()
        print(f"Checkbox '{checkbox.text()}' state: {state}")

    def on_analysis_changed(self):
        if self.genome_radio.isChecked():
            print("Analysis type: Genome")
        elif self.transcriptome_radio.isChecked():
            print("Analysis type: Transcriptome")

    def on_reference_changed(self, index):
        print(f"Selected reference: {self.reference_combo.currentText()}")