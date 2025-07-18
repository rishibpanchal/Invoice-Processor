"""
Main Invoice Processing Application with PyQt6 GUI - Modern UI
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
                           QHeaderView, QAbstractItemView, QToolBar, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont, QKeySequence, QAction

from pdf_viewer import PDFViewer
from enhanced_extractor import EnhancedInvoiceExtractor as InvoiceExtractor


class ProcessingThread(QThread):
    """Thread for processing PDF files"""
    
    finished = pyqtSignal(dict)  # Emitted when processing is complete
    error = pyqtSignal(str)      # Emitted when an error occurs
    progress = pyqtSignal(str)   # Emitted to update progress
    
    def __init__(self, pdf_path: str, extractor: InvoiceExtractor):
        super().__init__()
        self.pdf_path = pdf_path
        self.extractor = extractor
        
    def run(self):
        """Run the processing in background thread"""
        try:
            self.progress.emit("Extracting data from PDF...")
            data = self.extractor.extract_data(self.pdf_path)
            self.progress.emit("Processing complete!")
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class InvoiceProcessorApp(QMainWindow):
    """Modern Invoice Processor Application with Qt6"""
    
    def __init__(self):
        super().__init__()
        self.current_pdf_path = None
        self.current_invoice_data = None
        self.extractor = InvoiceExtractor()
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
                min-height: 35px;
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
                background-color: #6c757d;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
                margin-top: -1px;
            }
            QTabBar::tab {
                background: #e9ecef;
                border: 1px solid #dee2e6;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
                color: #212529;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #007bff;
                color: #007bff;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background: #f8f9fa;
                color: #212529;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 12px;
                color: #212529;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
                color: #212529;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                color: #212529;
                padding: 10px;
                border: 1px solid #dee2e6;
                font-weight: 600;
                font-size: 12px;
            }
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
                color: #212529;
            }
            QSplitter::handle {
                background-color: #dee2e6;
                border-radius: 2px;
            }
            QSplitter::handle:horizontal {
                width: 6px;
                margin: 2px 0px;
            }
            QStatusBar {
                background-color: #e9ecef;
                border-top: 1px solid #dee2e6;
                color: #212529;
                font-size: 12px;
            }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                text-align: center;
                background-color: #f8f9fa;
                height: 16px;
                color: #212529;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007bff, stop:1 #0056b3);
                border-radius: 7px;
            }
        """)
        
    def init_ui(self):
        """Initialize the modern user interface"""
        self.setWindowTitle("🧾 Invoice Data Processor")
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
        
        title_label = QLabel("📄 Invoice Processing System")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        subtitle_label = QLabel("Advanced PDF invoice data extraction")
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
        
    def create_pdf_viewer_pane(self):
        """Create the PDF viewer pane (left sidebar - expanded)"""
        pane = QWidget()
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # PDF Viewer with modern frame (full height)
        viewer_group = QGroupBox("📖 PDF Document Viewer")
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
        
        self.load_button = QPushButton("📂 Load PDF")
        self.load_button.clicked.connect(self.load_pdf)
        self.load_button.setToolTip("Select and load a PDF invoice file")
        
        self.process_button = QPushButton("⚡ Process PDF")
        self.process_button.clicked.connect(self.process_invoice)
        self.process_button.setEnabled(False)
        self.process_button.setToolTip("Extract data from the loaded PDF")
        self.process_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #1e7e34);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #155724);
            }
            QPushButton:disabled {
                background-color: #6c757d;
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
        export_group = QGroupBox("� Export Actions")
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
        
        # Bottom section - Extracted data
        data_group = QGroupBox("� Extracted Data")
        data_layout = QVBoxLayout(data_group)
        data_layout.setContentsMargins(10, 15, 10, 10)
        
        self.tab_widget = QTabWidget()
        
        # Invoice Info Tab with modern table
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(2)
        self.info_table.setHorizontalHeaderLabels(["� Field", "📝 Value"])
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
        self.tab_widget.addTab(self.items_table, "📦 Line Items")
        
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
        
        data_layout.addWidget(self.tab_widget)
        layout.addWidget(data_group)
        
        return pane
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
        
        controls_layout.addWidget(self.export_json_button)
        controls_layout.addWidget(self.export_csv_button)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addStretch()
        
        layout.addWidget(controls_group)
        
        # Modern tab widget for different data views
        data_group = QGroupBox("📋 Extracted Data")
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
        self.tab_widget.addTab(self.items_table, "📦 Line Items")
        
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
        
        data_layout.addWidget(self.tab_widget)
        layout.addWidget(data_group)
        
        return pane
        
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('📂 Open PDF', self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.load_pdf)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_json_action = QAction('📁 Export JSON', self)
        export_json_action.triggered.connect(self.export_json)
        file_menu.addAction(export_json_action)
        
        export_csv_action = QAction('📊 Export CSV', self)
        export_csv_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_csv_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('❌ Exit', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Process menu
        process_menu = menubar.addMenu('⚡ Process')
        
        process_action = QAction('🔄 Process Current PDF', self)
        process_action.setShortcut('Ctrl+P')
        process_action.triggered.connect(self.process_invoice)
        process_menu.addAction(process_action)
        
        clear_action = QAction('🗑️ Clear Data', self)
        clear_action.triggered.connect(self.clear_data)
        process_menu.addAction(clear_action)
        
        # Help menu
        help_menu = menubar.addMenu('❓ Help')
        
        about_action = QAction('ℹ️ About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar for processing
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_bar.showMessage("Ready")
        
    def load_pdf(self):
        """Load a PDF file with modern UI feedback"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select PDF Invoice File", 
            "", 
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            if self.pdf_viewer.load_pdf(file_path):
                self.current_pdf_path = file_path
                filename = os.path.basename(file_path)
                self.file_label.setText(f"✅ {filename}")
                self.file_label.setStyleSheet("""
                    QLabel {
                        background-color: #d4edda;
                        border: 2px solid #c3e6cb;
                        border-radius: 8px;
                        padding: 12px;
                        color: #155724;
                        font-weight: bold;
                        font-size: 13px;
                    }
                """)
                self.process_button.setEnabled(True)
                self.status_bar.showMessage(f"📄 PDF loaded successfully: {filename}")
            else:
                self.file_label.setText("❌ Failed to load PDF")
                self.file_label.setStyleSheet("""
                    QLabel {
                        background-color: #f8d7da;
                        border: 2px solid #f5c6cb;
                        border-radius: 8px;
                        padding: 12px;
                        color: #721c24;
                        font-weight: bold;
                        font-size: 13px;
                    }
                """)
                self.process_button.setEnabled(False)
                self.status_bar.showMessage("❌ Failed to load PDF file")
                
    def process_invoice(self):
        """Process the current invoice"""
        if not self.current_pdf_path:
            QMessageBox.warning(self, "Warning", "Please load a PDF file first.")
            return
            
        # Disable UI during processing
        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start processing in background thread
        self.processing_thread = ProcessingThread(self.current_pdf_path, self.extractor)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        self.processing_thread.progress.connect(self.on_processing_progress)
        self.processing_thread.start()
        
    def on_processing_finished(self, data: Dict[str, Any]):
        """Handle successful processing completion"""
        self.current_invoice_data = data
        self.display_invoice_data(data)
        
        # Re-enable UI
        self.process_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Enable export buttons only if extraction was successful
        if not data.get('error', False):
            self.export_json_button.setEnabled(True)
            self.export_csv_button.setEnabled(True)
            self.clear_button.setEnabled(True)
        else:
            self.clear_button.setEnabled(True)  # Allow clearing even on error
        
        # Update status based on extraction results
        if data.get('error', False):
            self.status_bar.showMessage("❌ Processing completed with errors")
        else:
            summary = self.extractor.get_extraction_summary(data)
            if summary['status'] == 'warning':
                self.status_bar.showMessage("⚠️ Processing completed with warnings")
            else:
                self.status_bar.showMessage("✅ Processing completed successfully")
        
    def on_processing_error(self, error_msg: str):
        """Handle processing error"""
        QMessageBox.critical(self, "Processing Error", f"Error processing invoice:\n{error_msg}")
        
        # Re-enable UI
        self.process_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.status_bar.showMessage("Processing failed")
        
    def on_processing_progress(self, message: str):
        """Handle processing progress updates"""
        self.status_bar.showMessage(message)
        
    def display_invoice_data(self, data: Dict[str, Any]):
        """Display extracted invoice data in the tables"""
        
        # Check if extraction failed
        if data.get('error', False):
            self.display_error_data(data)
            return
        
        # Display invoice info
        self.populate_info_table(data)
        
        # Display line items
        self.populate_items_table(data)
        
        # Display raw text
        self.raw_text.setPlainText(data.get('raw_text', ''))
        
        # Display JSON
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        self.json_text.setPlainText(json_str)
        
        # Update status with summary
        summary = self.extractor.get_extraction_summary(data)
        status_message = f"✅ Extracted {summary['fields_extracted']} fields"
        if summary['line_items_count'] > 0:
            status_message += f", {summary['line_items_count']} line items"
        if summary['missing_required_fields'] > 0:
            status_message += f" ⚠️ {summary['missing_required_fields']} required fields missing"
        
        self.status_bar.showMessage(status_message)
        
    def display_error_data(self, data: Dict[str, Any]):
        """Display error information when extraction fails"""
        # Clear existing data
        self.info_table.setRowCount(0)
        self.items_table.setRowCount(0)
        self.raw_text.clear()
        
        # Show error in info table
        error_data = {
            'Error Type': data.get('error_type', 'Unknown'),
            'Error Message': data.get('error_message', 'Unknown error occurred'),
            'Source File': data.get('_metadata', {}).get('source_file', 'Unknown'),
            'Extraction Method': data.get('_metadata', {}).get('extraction_method', 'Unknown')
        }
        
        self.info_table.setRowCount(len(error_data))
        for row, (key, value) in enumerate(error_data.items()):
            # Field name with error icon
            field_item = QTableWidgetItem(f"❌ {key}")
            field_item.setFlags(field_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            field_item.setForeground(Qt.GlobalColor.red)
            self.info_table.setItem(row, 0, field_item)
            
            # Field value
            value_item = QTableWidgetItem(str(value))
            value_item.setForeground(Qt.GlobalColor.red)
            self.info_table.setItem(row, 1, value_item)
        
        # Resize columns
        self.info_table.resizeColumnsToContents()
        self.info_table.horizontalHeader().setStretchLastSection(True)
        
        # Show error in JSON tab
        error_json = json.dumps(data, indent=2, ensure_ascii=False)
        self.json_text.setPlainText(error_json)
        
    def populate_info_table(self, data: Dict[str, Any]):
        """Populate the invoice info table with modern styling - only non-null values"""
        # Exclude line items, raw text, metadata, and null values from main info
        info_data = {}
        for k, v in data.items():
            if (k not in ['line_items', 'raw_text', '_metadata', 'error'] and 
                v is not None and v != '' and v != 'null'):
                info_data[k] = v
        
        self.info_table.setRowCount(len(info_data))
        
        for row, (key, value) in enumerate(info_data.items()):
            # Field name with emoji icons
            field_icons = {
                'invoice_number': '🧾',
                'invoice_date': '📅',
                'due_date': '⏰',
                'vendor_name': '🏢',
                'vendor_address': '📍',
                'vendor_gst': '🏛️',
                'vendor_contact': '📞',
                'vendor_email': '📧',
                'consignee_name': '👤',
                'buyer_name': '🏪',
                'total_amount': '�',
                'total_invoice_value': '💰',
                'currency': '💱',
                'subtotal': '🧮',
                'tax': '📊',
                'billing_address': '🏠',
                'shipping_address': '🚚'
            }
            
            icon = field_icons.get(key, '📋')
            display_name = f"{icon} {key.replace('_', ' ').title()}"
            
            field_item = QTableWidgetItem(display_name)
            field_item.setFlags(field_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.info_table.setItem(row, 0, field_item)
            
            # Field value with formatting
            value_str = str(value)
            value_item = QTableWidgetItem(value_str)
            
            # Apply special formatting for certain fields
            if key in ['total_amount', 'total_invoice_value', 'subtotal'] and value:
                value_item.setForeground(Qt.GlobalColor.darkGreen)
                value_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            elif key in ['vendor_name', 'consignee_name', 'buyer_name']:
                value_item.setForeground(Qt.GlobalColor.darkBlue)
                value_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                
            self.info_table.setItem(row, 1, value_item)
            
        # Resize columns to content
        self.info_table.resizeColumnsToContents()
        self.info_table.horizontalHeader().setStretchLastSection(True)
        
    def populate_items_table(self, data: Dict[str, Any]):
        """Populate the line items table with modern styling in specified order"""
        line_items = data.get('line_items', [])
        
        if not line_items:
            self.items_table.setRowCount(1)
            self.items_table.setColumnCount(1)
            self.items_table.setHorizontalHeaderLabels(["📦 Line Items"])
            no_items = QTableWidgetItem("No line items extracted")
            no_items.setForeground(Qt.GlobalColor.gray)
            self.items_table.setItem(0, 0, no_items)
            return
        
        # Define the specific order for line item columns
        ordered_columns = [
            'item_description',
            'quantity', 
            'hsn_sac_code',
            'total_item_value',
            'cgst_rate',
            'cgst_amount',
            'sgst_rate', 
            'sgst_amount',
            'igst_rate',
            'igst_amount',
            'tax_amount'
        ]
        
        # Filter to only include columns that exist and have non-null values in at least one item
        existing_columns = []
        for col in ordered_columns:
            # Check if column exists and has at least one non-null value
            has_data = False
            for item in line_items:
                if col in item and item[col] is not None and item[col] != '' and item[col] != 'null':
                    has_data = True
                    break
            if has_data:
                existing_columns.append(col)
        
        # Create display headers with emojis
        column_display_names = {
            'item_description': '📝 Description',
            'quantity': '🔢 Quantity',
            'hsn_sac_code': '🏷️ HSN/SAC',
            'total_item_value': '💰 Item Value',
            'cgst_rate': '📊 CGST Rate',
            'cgst_amount': '💵 CGST Amount',
            'sgst_rate': '📊 SGST Rate',
            'sgst_amount': '💵 SGST Amount',
            'igst_rate': '📊 IGST Rate',
            'igst_amount': '� IGST Amount',
            'tax_amount': '💰 Tax Amount'
        }
        
        display_headers = [column_display_names.get(col, col.replace('_', ' ').title()) for col in existing_columns]
        
        self.items_table.setRowCount(len(line_items))
        self.items_table.setColumnCount(len(existing_columns))
        self.items_table.setHorizontalHeaderLabels(display_headers)
        
        # Populate data with formatting
        for row, item in enumerate(line_items):
            for col, column_name in enumerate(existing_columns):
                value = item.get(column_name, '')
                
                # Skip null values - display empty string
                if value is None or value == 'null' or value == '':
                    value = ''
                
                table_item = QTableWidgetItem(str(value))
                
                # Apply special formatting based on column type
                if 'amount' in column_name or 'value' in column_name:
                    table_item.setForeground(Qt.GlobalColor.darkGreen)
                    table_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                elif 'rate' in column_name:
                    table_item.setForeground(Qt.GlobalColor.darkBlue)
                elif column_name == 'quantity':
                    table_item.setForeground(Qt.GlobalColor.darkMagenta)
                elif column_name == 'item_description':
                    table_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                    
                self.items_table.setItem(row, col, table_item)
                
        # Resize columns to content
        self.items_table.resizeColumnsToContents()
        
        # Set minimum column widths for better readability
        for i in range(self.items_table.columnCount()):
            if self.items_table.columnWidth(i) < 80:
                self.items_table.setColumnWidth(i, 80)
        
    def export_json(self):
        """Export data to JSON file"""
        if not self.current_invoice_data:
            QMessageBox.warning(self, "Warning", "No data to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export JSON", 
            "invoice_data.json", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if self.extractor.export_to_json(self.current_invoice_data, file_path):
                QMessageBox.information(self, "Success", f"Data exported to {file_path}")
                self.status_bar.showMessage(f"Exported to {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export JSON file.")
                
    def export_csv(self):
        """Export line items to CSV file"""
        if not self.current_invoice_data:
            QMessageBox.warning(self, "Warning", "No data to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export CSV", 
            "invoice_items.csv", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            if self.extractor.export_to_csv(self.current_invoice_data, file_path):
                QMessageBox.information(self, "Success", f"Line items exported to {file_path}")
                self.status_bar.showMessage(f"Exported to {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export CSV file.")
                
    def clear_data(self):
        """Clear all displayed data"""
        self.current_invoice_data = None
        
        # Clear tables
        self.info_table.setRowCount(0)
        self.items_table.setRowCount(0)
        self.items_table.setColumnCount(0)
        
        # Clear text areas
        self.raw_text.clear()
        self.json_text.clear()
        
        # Disable export buttons
        self.export_json_button.setEnabled(False)
        self.export_csv_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        self.status_bar.showMessage("Data cleared")
        
    def show_about(self):
        """Show modern about dialog"""
        QMessageBox.about(
            self, 
            "About Invoice Processor Pro",
            """
            <h2>🧾 Invoice Data Processor Pro v2.0</h2>
            
            <p><b>Modern AI-powered invoice processing system</b></p>
            
            <p>A state-of-the-art tool for extracting structured data from invoice PDFs 
            using advanced parsing algorithms and modern Qt6 interface.</p>
            
            <h3>✨ Key Features:</h3>
            <ul>
                <li>📄 Advanced PDF viewing and navigation</li>
                <li>🤖 AI-powered data extraction</li>
                <li>📊 Beautiful tabulated data display</li>
                <li>💾 JSON and CSV export capabilities</li>
                <li>🎨 Modern, responsive user interface</li>
                <li>⚡ High-performance processing</li>
            </ul>
            
            <h3>🛠️ Technology Stack:</h3>
            <p><b>Powered by:</b> Gemma3n:e2b, PyQt6, PyMuPDF, Pandas</p>
            
            <p><i>Built with ❤️ for efficient invoice processing</i></p>
            """
        )
        
    def closeEvent(self, event):
        """Handle application close event"""
        # Stop any running processing thread
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait()
            
        # Close PDF viewer
        self.pdf_viewer.close_document()
        
        event.accept()


def main():
    """Main application entry point with modern Qt6 styling"""
    app = QApplication(sys.argv)
    app.setApplicationName("Invoice Processor")
    app.setApplicationVersion("2.0")
    
    # Set modern application style
    app.setStyle('Fusion')
    
    # Set application icon if available
    try:
        app.setWindowIcon(QIcon("📄"))  # Fallback to emoji
    except:
        pass
    
    # Create and show main window
    window = InvoiceProcessorApp()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
