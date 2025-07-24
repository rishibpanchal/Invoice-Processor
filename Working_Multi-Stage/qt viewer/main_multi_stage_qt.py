"""
Multi-Stage Invoice Processing Application with PyQt6 GUI
Enhanced version with stage-by-stage processing and detailed progress tracking
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any
import json
import pandas as pd

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, QSplitter,
                           QTableWidget, QTableWidgetItem, QTabWidget,
                           QTextEdit, QLabel, QMessageBox, QMenuBar, QMenu,
                           QStatusBar, QProgressBar, QGroupBox,
                           QHeaderView, QAbstractItemView, QToolBar, QFrame,
                           QTreeWidget, QTreeWidgetItem, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont, QKeySequence, QAction, QColor

from pdf_viewer import PDFViewer
from enhanced_multi_stage_extractor import EnhancedMultiStageExtractor


class MultiStageProcessingThread(QThread):
    """Thread for multi-stage processing of PDF files"""
    
    finished = pyqtSignal(dict)  # Emitted when processing is complete
    error = pyqtSignal(str)      # Emitted when an error occurs
    progress = pyqtSignal(str)   # Emitted to update progress
    stage_completed = pyqtSignal(str, dict)  # Emitted when a stage is completed
    
    def __init__(self, pdf_path: str, extractor: EnhancedMultiStageExtractor):
        super().__init__()
        self.pdf_path = pdf_path
        self.extractor = extractor
        
    def run(self):
        """Run the multi-stage processing in background thread"""
        try:
            # Set up progress callback
            self.extractor.set_progress_callback(self.progress.emit)
            
            # Start extraction
            self.progress.emit("Starting multi-stage extraction...")
            data = self.extractor.extract_data_with_stages(self.pdf_path)
            
            # Get extraction summary
            summary = self.extractor.get_extraction_summary()
            self.stage_completed.emit("extraction_complete", summary)
            
            self.progress.emit("Processing complete!")
            self.finished.emit(data)
            
        except Exception as e:
            self.error.emit(str(e))


class MultiStageInvoiceProcessorApp(QMainWindow):
    """Multi-Stage Invoice Processor Application with Qt6"""
    
    def __init__(self):
        super().__init__()
        self.current_pdf_path = None
        self.current_invoice_data = None
        self.current_extraction_summary = None
        self.invoice_array = []
        self.current_invoice_index = 0
        self.extractor = EnhancedMultiStageExtractor()
        self.processing_thread = None
        
        self.init_ui()
        self.setup_modern_styling()
        self.setup_menu()
        self.setup_status_bar()
        
    def setup_modern_styling(self):
        """Apply modern styling to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                color: #212529;
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            }
            QGroupBox {
                font-weight: 600;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                margin-top: 1ex;
                padding-top: 12px;
                background-color: white;
                font-size: 13px;
                color: #212529;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #212529;
                background-color: white;
                font-weight: bold;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                font-size: 13px;
                font-weight: 500;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #004085, stop:1 #002752);
            }
            QPushButton:disabled {
                background: #6c757d;
                color: #adb5bd;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: #007bff;
                color: white;
            }
            QTabBar::tab:hover {
                background: #6c757d;
                color: white;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-size: 13px;
                color: #212529;
                font-weight: 500;
            }
            QTableWidget::item {
                color: #212529;
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
                font-weight: 500;
            }
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
                font-weight: 600;
            }
            QTableWidget::item:hover {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #495057;
                color: white;
                padding: 12px 8px;
                border: none;
                font-weight: 700;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QTreeWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f1f3f5;
            }
            QTreeWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: #f8f9fa;
                text-align: center;
                font-weight: 600;
                color: #495057;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 6px;
            }
        """)
        
    def init_ui(self):
        """Initialize the user interface - matching original layout"""
        self.setWindowTitle("🧾 Multi-Stage Invoice Processor")
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1200, 700)
        
        # Central widget with modern layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with reduced margins for more space
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        # Compact header section
        header_frame = QFrame()
        header_frame.setMaximumHeight(60)  # Limit header height
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007bff, stop:1 #0056b3);
                border-radius: 8px;
                padding: 8px 15px;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel("📄 Multi-Stage Invoice Processing System")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        subtitle_label = QLabel("Advanced multi-stage PDF invoice data extraction")
        subtitle_label.setStyleSheet("font-size: 11px; color: #e3f2fd; margin-left: 15px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.addStretch()  # Push content to the left
        main_layout.addWidget(header_frame)
        
        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter)
        
        # Left pane - PDF Viewer (expanded to full sidebar)
        left_pane = self.create_pdf_viewer_pane()
        splitter.addWidget(left_pane)
        
        # Right pane - Controls and Data
        right_pane = self.create_controls_and_data_pane()
        splitter.addWidget(right_pane)
        
        # Set initial splitter sizes (50% left for PDF, 50% right for controls/data)
        splitter.setSizes([750, 750])
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
    def create_pdf_viewer_pane(self):
        """Create the PDF viewer pane (left sidebar - expanded)"""
        pane = QWidget()
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # PDF Viewer with modern frame (full height)
        viewer_group = QGroupBox("� PDF Document Viewer")
        viewer_layout = QVBoxLayout(viewer_group)
        viewer_layout.setContentsMargins(5, 15, 5, 5)
        
        self.pdf_viewer = PDFViewer()
        viewer_layout.addWidget(self.pdf_viewer)
        layout.addWidget(viewer_group)
        
        return pane
        
    def create_controls_and_data_pane(self):
        """Create the controls and data pane (right sidebar)"""
        pane = QWidget()
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Top section - PDF controls
        controls_group = QGroupBox("📁 PDF Controls")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(8)
        
        # File selection buttons
        file_layout = QHBoxLayout()
        file_layout.setSpacing(6)
        
        self.load_button = QPushButton("📁 Load PDF")
        self.load_button.clicked.connect(self.open_pdf)
        self.load_button.setToolTip("Select and load a PDF invoice file")
        self.load_button.setMinimumHeight(45)
        self.load_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #17a2b8, stop:1 #138496);
                border: none;
                color: white;
                padding: 12px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: 600;
                border-radius: 10px;
                min-width: 120px;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #138496, stop:1 #0f5d6b);
                border: 2px solid #0f5d6b;
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f5d6b, stop:1 #0a4a54);
                transform: translateY(0px);
            }
        """)
        
        self.process_button = QPushButton("⚡ Multi-Stage Process")
        self.process_button.clicked.connect(self.process_pdf)
        self.process_button.setEnabled(False)
        self.process_button.setToolTip("Extract data using multi-stage approach")
        self.process_button.setMinimumHeight(45)
        self.process_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #1e7e34);
                border: none;
                color: white;
                padding: 12px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: 600;
                border-radius: 10px;
                min-width: 120px;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #155724);
                border: 2px solid #155724;
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #155724, stop:1 #0f3d1a);
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
                border: 2px solid #adb5bd;
                transform: none;
            }
        """)
        
        file_layout.addWidget(self.load_button)
        file_layout.addWidget(self.process_button)
        controls_layout.addLayout(file_layout)
        
        # Current file status
        self.file_label = QLabel("📄 No file loaded")
        self.file_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 6px;
                padding: 8px;
                color: #212529;
                font-style: italic;
                text-align: center;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        controls_layout.addWidget(self.file_label)
        
        layout.addWidget(controls_group)
        
        # Middle section - Export actions
        export_group = QGroupBox("💾 Export Actions")
        export_layout = QHBoxLayout(export_group)
        export_layout.setSpacing(6)
        
        self.export_json_button = QPushButton("📁 Export JSON")
        self.export_json_button.clicked.connect(self.export_json)
        self.export_json_button.setEnabled(False)
        self.export_json_button.setToolTip("Export complete data to JSON format")
        
        self.export_csv_button = QPushButton("📊 Export CSV")
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_csv_button.setEnabled(False)
        self.export_csv_button.setToolTip("Export line items to CSV format")
        
        self.clear_button = QPushButton("🗑️ Clear Data")
        self.clear_button.clicked.connect(self.clear_data)
        self.clear_button.setEnabled(False)
        self.clear_button.setToolTip("Clear all extracted data")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #a71e2a);
            }
        """)
        
        export_layout.addWidget(self.export_json_button)
        export_layout.addWidget(self.export_csv_button)
        export_layout.addWidget(self.clear_button)
        
        layout.addWidget(export_group)
        
        # Navigation section for multiple invoices
        nav_group = QGroupBox("📋 Invoice Navigation")
        nav_layout = QHBoxLayout(nav_group)
        nav_layout.setSpacing(8)
        
        self.prev_button = QPushButton("⬅️ Previous")
        self.prev_button.clicked.connect(self.prev_invoice)
        self.prev_button.setEnabled(False)
        self.prev_button.setToolTip("Show previous invoice")
        self.prev_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #495057);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #495057, stop:1 #343a40);
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        
        self.invoice_counter_label = QLabel("No invoices")
        self.invoice_counter_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 15px;
                color: #212529;
                font-weight: bold;
                text-align: center;
                min-width: 120px;
            }
        """)
        self.invoice_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_button = QPushButton("Next ➡️")
        self.next_button.clicked.connect(self.next_invoice)
        self.next_button.setEnabled(False)
        self.next_button.setToolTip("Show next invoice")
        self.next_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #495057);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #495057, stop:1 #343a40);
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.invoice_counter_label)
        nav_layout.addWidget(self.next_button)
        
        layout.addWidget(nav_group)
        
        # Bottom section - Extracted data
        data_group = QGroupBox("📊 Extracted Data")
        data_layout = QVBoxLayout(data_group)
        data_layout.setContentsMargins(10, 15, 10, 10)
        
        self.tab_widget = QTabWidget()
        
        # Invoice Info Tab with modern table
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(2)
        self.info_table.setHorizontalHeaderLabels(["📋 Field", "📝 Value"])
        self.info_table.horizontalHeader().setStretchLastSection(True)
        self.info_table.setAlternatingRowColors(True)
        self.info_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.info_table.verticalHeader().setVisible(False)
        self.tab_widget.addTab(self.info_table, "📋 Invoice Info")
        
        # Line Items Tab
        self.items_table = QTableWidget()
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.verticalHeader().setVisible(False)
        self.tab_widget.addTab(self.items_table, "� Line Items")
        
        # Raw Text Tab with modern text editor
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setFont(QFont("Consolas", 10))
        self.raw_text.setPlaceholderText("Raw extracted text will appear here...")
        self.tab_widget.addTab(self.raw_text, "📄 Raw Text")
        
        # JSON Tab with syntax highlighting simulation
        self.json_text = QTextEdit()
        self.json_text.setReadOnly(True)
        self.json_text.setFont(QFont("Consolas", 10))
        self.json_text.setPlaceholderText("Structured JSON data will appear here...")
        self.tab_widget.addTab(self.json_text, "🔧 JSON Data")
        
        # Multi-stage progress tab
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setFont(QFont("Consolas", 10))
        self.progress_text.setPlaceholderText("Multi-stage processing progress will appear here...")
        self.tab_widget.addTab(self.progress_text, "🔄 Process Log")
        
        data_layout.addWidget(self.tab_widget)
        layout.addWidget(data_group)
        
        return pane
        
    def clear_data(self):
        """Clear all extracted data"""
        self.current_invoice_data = None
        self.current_extraction_summary = None
        self.invoice_array = []
        self.current_invoice_index = 0
        
        # Clear displays
        self.info_table.setRowCount(0)
        self.items_table.setRowCount(0)
        self.raw_text.clear()
        self.json_text.clear()
        self.progress_text.clear()
        
        # Reset navigation
        self.invoice_counter_label.setText("No invoices")
        self.update_navigation_buttons()
        
        # Disable buttons
        self.export_json_button.setEnabled(False)
        self.export_csv_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        self.statusBar().showMessage("Data cleared")
    
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open PDF", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Processing menu
        process_menu = menubar.addMenu("&Process")
        
        multi_stage_action = QAction("&Multi-Stage Extract", self)
        multi_stage_action.triggered.connect(self.process_pdf)
        process_menu.addAction(multi_stage_action)
        
        # Export menu
        export_menu = menubar.addMenu("&Export")
        
        export_json_action = QAction("Export &JSON", self)
        export_json_action.triggered.connect(self.export_json)
        export_menu.addAction(export_json_action)
        
        export_csv_action = QAction("Export &CSV", self)
        export_csv_action.triggered.connect(self.export_csv)
        export_menu.addAction(export_csv_action)
    
    def setup_status_bar(self):
        """Setup the status bar"""
        self.statusBar().showMessage("Ready - Multi-Stage Invoice Processor")
    
    def open_pdf(self):
        """Open and load a PDF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open PDF File", 
            "", 
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            self.current_pdf_path = file_path
            self.file_label.setText(f"📄 {Path(file_path).name}")
            self.process_button.setEnabled(True)
            
            # Load PDF in viewer
            self.pdf_viewer.load_pdf(file_path)
            
            # Clear previous data
            self.clear_data()
            
            self.statusBar().showMessage(f"PDF loaded: {Path(file_path).name}")
    
    def process_pdf(self):
        """Process the current PDF using multi-stage extraction"""
        if not self.current_pdf_path:
            QMessageBox.warning(self, "Warning", "Please select a PDF file first.")
            return
        
        # Disable buttons during processing
        self.process_button.setEnabled(False)
        self.export_json_button.setEnabled(False)
        self.export_csv_button.setEnabled(False)
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Clear progress log
        self.progress_text.clear()
        
        # Start processing thread
        self.processing_thread = MultiStageProcessingThread(self.current_pdf_path, self.extractor)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        self.processing_thread.progress.connect(self.on_progress_update)
        
        self.processing_thread.start()
        
        self.statusBar().showMessage("Processing PDF with multi-stage extraction...")
    
    def on_processing_finished(self, data):
        """Handle successful processing completion"""
        self.current_invoice_data = data
        
        # Update displays
        self.update_all_displays()
        
        # Re-enable buttons
        self.process_button.setEnabled(True)
        self.export_json_button.setEnabled(True)
        self.export_csv_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        self.statusBar().showMessage("Multi-stage extraction completed successfully!")
    
    def on_processing_error(self, error_message):
        """Handle processing errors"""
        QMessageBox.critical(self, "Processing Error", f"Error during extraction:\n{error_message}")
        
        # Re-enable buttons
        self.process_button.setEnabled(True)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Log error
        self.progress_text.append(f"❌ ERROR: {error_message}")
        
        self.statusBar().showMessage("Processing failed!")
    
    def on_progress_update(self, message):
        """Update progress display"""
        self.statusBar().showMessage(message)
        self.progress_text.append(f"📋 {message}")
        
        # Auto-scroll to bottom
        cursor = self.progress_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.progress_text.setTextCursor(cursor)
    
    def update_all_displays(self):
        """Update all data displays"""
        if not self.current_invoice_data:
            return
        
        if self.current_invoice_data.get('error', False):
            self.show_error_data()
            return
        
        # Update invoice data
        self.invoice_array = self.current_invoice_data.get('invoices', [])
        
        if self.invoice_array:
            self.current_invoice_index = 0
            self.update_current_invoice_display()
            self.update_navigation_buttons()
        
        # Update raw text
        raw_text = self.current_invoice_data.get('raw_text', '')
        self.raw_text.setPlainText(raw_text)
        
        # Update JSON display
        json_data = self.current_invoice_data.copy()
        if 'raw_text' in json_data:
            del json_data['raw_text']  # Remove for cleaner display
        
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        self.json_text.setPlainText(json_str)
    
    def show_error_data(self):
        """Show error information"""
        error_msg = self.current_invoice_data.get('error_message', 'Unknown error')
        self.raw_text.setPlainText(f"Error: {error_msg}")
        self.json_text.setPlainText(json.dumps(self.current_invoice_data, indent=2))
        self.invoice_counter_label.setText("Error occurred")
    
    def update_current_invoice_display(self):
        """Update the display for the current invoice"""
        if not self.invoice_array or self.current_invoice_index >= len(self.invoice_array):
            return
        
        current_invoice = self.invoice_array[self.current_invoice_index]
        
        # Update invoice counter
        invoice_num = current_invoice.get('invoice_number', f'Invoice {self.current_invoice_index + 1}')
        total_invoices = len(self.invoice_array)
        self.invoice_counter_label.setText(f"{self.current_invoice_index + 1}/{total_invoices}: {invoice_num}")
        
        # Update invoice info table
        self.populate_invoice_table(current_invoice)
        
        # Update line items table
        self.populate_line_items_table(current_invoice)
    
    def populate_invoice_table(self, invoice_data):
        """Populate the invoice info table"""
        # Define fields to display
        field_mapping = [
            ('invoice_number', 'Invoice Number'),
            ('invoice_date', 'Invoice Date'),
            ('vendor_name', 'Vendor Name'),
            ('vendor_address', 'Vendor Address'),
            ('vendor_gst', 'Vendor GST'),
            ('vendor_contact', 'Vendor Contact'),
            ('vendor_email', 'Vendor Email'),
            ('buyer_name', 'Buyer Name'),
            ('buyer_address', 'Buyer Address'),
            ('buyer_gst', 'Buyer GST'),
            ('total_amount', 'Total Amount'),
            ('currency', 'Currency'),
            ('due_date', 'Due Date'),
            ('payment_terms', 'Payment Terms'),
            ('place_of_supply', 'Place of Supply')
        ]
        
        # Filter out empty values
        display_data = []
        for field_key, field_label in field_mapping:
            value = invoice_data.get(field_key)
            if value is not None and str(value).strip():
                display_data.append((field_label, str(value)))
        
        # Populate table
        self.info_table.setRowCount(len(display_data))
        
        for i, (field, value) in enumerate(display_data):
            self.info_table.setItem(i, 0, QTableWidgetItem(field))
            self.info_table.setItem(i, 1, QTableWidgetItem(value))
        
        # Resize columns
        self.info_table.resizeColumnsToContents()
    
    def populate_line_items_table(self, invoice_data):
        """Populate the line items table"""
        line_items = invoice_data.get('line_items', [])
        
        if not line_items:
            self.items_table.setRowCount(0)
            self.items_table.setColumnCount(1)
            self.items_table.setHorizontalHeaderLabels(["No Line Items"])
            return
        
        # Define columns for line items
        columns = [
            ('item_description', 'Description'),
            ('quantity', 'Quantity'),
            ('total_item_value', 'Total Value'),
            ('hsn_sac_code', 'HSN/SAC'),
            ('taxable_value', 'Taxable Value'),
            ('cgst_amount', 'CGST'),
            ('sgst_amount', 'SGST'),
            ('igst_amount', 'IGST')
        ]
        
        self.items_table.setRowCount(len(line_items))
        self.items_table.setColumnCount(len(columns))
        self.items_table.setHorizontalHeaderLabels([col[1] for col in columns])
        
        for row, item in enumerate(line_items):
            for col, (key, _) in enumerate(columns):
                value = item.get(key, '')
                if value is None:
                    value = ''
                self.items_table.setItem(row, col, QTableWidgetItem(str(value)))
        
        # Resize columns
        self.items_table.resizeColumnsToContents()
    
    def update_navigation_buttons(self):
        """Update navigation button states"""
        if not self.invoice_array:
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return
        
        self.prev_button.setEnabled(self.current_invoice_index > 0)
        self.next_button.setEnabled(self.current_invoice_index < len(self.invoice_array) - 1)
    
    def prev_invoice(self):
        """Navigate to previous invoice"""
        if self.current_invoice_index > 0:
            self.current_invoice_index -= 1
            self.update_current_invoice_display()
            self.update_navigation_buttons()
    
    def next_invoice(self):
        """Navigate to next invoice"""
        if self.current_invoice_index < len(self.invoice_array) - 1:
            self.current_invoice_index += 1
            self.update_current_invoice_display()
            self.update_navigation_buttons()
    
    def show_previous_invoice(self):
        """Show previous invoice (alias for compatibility)"""
        self.prev_invoice()
    
    def show_next_invoice(self):
        """Show next invoice (alias for compatibility)"""
        self.next_invoice()
    
    def export_json(self):
        """Export data to JSON file"""
        if not self.current_invoice_data:
            QMessageBox.warning(self, "Warning", "No data to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export JSON", 
            f"invoice_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_invoice_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Success", f"Data exported to:\n{file_path}")
                self.statusBar().showMessage(f"JSON exported to: {Path(file_path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export JSON file:\n{str(e)}")
    
    def export_csv(self):
        """Export line items to CSV file"""
        if not self.current_invoice_data:
            QMessageBox.warning(self, "Warning", "No data to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export CSV", 
            f"invoice_line_items_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                # Collect all line items from all invoices
                all_items = []
                invoices = self.current_invoice_data.get('invoices', [])
                
                for invoice in invoices:
                    invoice_num = invoice.get('invoice_number', 'Unknown')
                    line_items = invoice.get('line_items', [])
                    
                    for item in line_items:
                        row = {
                            'invoice_number': invoice_num,
                            'item_description': item.get('item_description', ''),
                            'quantity': item.get('quantity', ''),
                            'total_item_value': item.get('total_item_value', ''),
                            'hsn_sac_code': item.get('hsn_sac_code', ''),
                            'taxable_value': item.get('taxable_value', ''),
                            'cgst_amount': item.get('cgst_amount', ''),
                            'sgst_amount': item.get('sgst_amount', ''),
                            'igst_amount': item.get('igst_amount', '')
                        }
                        all_items.append(row)
                
                if all_items:
                    df = pd.DataFrame(all_items)
                    df.to_csv(file_path, index=False)
                    QMessageBox.information(self, "Success", f"Line items exported to:\n{file_path}")
                    self.statusBar().showMessage(f"CSV exported to: {Path(file_path).name}")
                else:
                    QMessageBox.warning(self, "Warning", "No line items found to export.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export CSV file:\n{str(e)}")


def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Multi-Stage Invoice Processor")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("DataNorth")
    
    # Create and show the main window
    window = MultiStageInvoiceProcessorApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
