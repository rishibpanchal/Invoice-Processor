"""
PDF Viewer Widget for PyQt6 - Modern UI
"""
import sys
import os
import fitz  # PyMuPDF
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QScrollArea, QFrame, QSizePolicy, QSlider,
                           QSpinBox, QMessageBox, QToolBar, QToolButton, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QIcon, QAction
from PIL import Image
import io


class PDFViewer(QWidget):
    """Modern PDF Viewer widget using PyMuPDF with Qt6"""
    
    page_changed = pyqtSignal(int)  # Signal emitted when page changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.rotation = 0  # Current rotation in degrees (0, 90, 180, 270)
        self.fit_mode = "none"  # Track current fit mode: "none", "width", "height", "page"
        
        self.setup_ui()
        self.apply_modern_styling()
        self.setup_context_menu()
        
    def apply_modern_styling(self):
        """Apply modern styling to the PDF viewer"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
                color: #212529;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
                color: #212529;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #212529;
                font-weight: bold;
            }
            QPushButton {
                background-color: #007bff;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 12px;
                border-radius: 6px;
                min-width: 80px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
            QToolButton {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                color: #212529;
                padding: 6px;
                border-radius: 4px;
                margin: 2px;
                font-weight: 500;
            }
            QToolButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
                color: #212529;
            }
            QToolButton:pressed {
                background-color: #dee2e6;
                color: #212529;
            }
            QSpinBox {
                padding: 4px 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                min-width: 60px;
                color: #212529;
            }
            QSpinBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QLabel {
                color: #212529;
                font-size: 12px;
                font-weight: 500;
            }
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        
    def setup_ui(self):
        """Setup the modern user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Modern toolbar-style control panel
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # File selection actions
        self.load_action = QAction("📁 Load PDF", self)
        self.load_action.triggered.connect(self.load_pdf_dialog)
        toolbar.addAction(self.load_action)
        
        toolbar.addSeparator()
        
        # Navigation actions
        self.prev_action = QAction("◀ Previous", self)
        self.prev_action.triggered.connect(self.previous_page)
        self.prev_action.setEnabled(False)
        toolbar.addAction(self.prev_action)
        
        self.next_action = QAction("Next ▶", self)
        self.next_action.triggered.connect(self.next_page)
        self.next_action.setEnabled(False)
        toolbar.addAction(self.next_action)
        
        # Page info
        toolbar.addSeparator()
        page_widget = QWidget()
        page_layout = QHBoxLayout(page_widget)
        page_layout.setContentsMargins(5, 0, 5, 0)
        
        page_layout.addWidget(QLabel("Page:"))
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)
        self.page_spinbox.valueChanged.connect(self.go_to_page)
        self.page_spinbox.setEnabled(False)
        page_layout.addWidget(self.page_spinbox)
        
        self.page_label = QLabel("/ 0")
        page_layout.addWidget(self.page_label)
        
        toolbar.addWidget(page_widget)
        
        toolbar.addSeparator()
        
        # Enhanced zoom controls
        self.zoom_out_action = QAction("🔍- Zoom Out", self)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.zoom_out_action.setEnabled(False)
        toolbar.addAction(self.zoom_out_action)
        
        zoom_widget = QWidget()
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(5, 0, 5, 0)
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("font-weight: bold; color: #007bff;")
        zoom_layout.addWidget(self.zoom_label)
        toolbar.addWidget(zoom_widget)
        
        self.zoom_in_action = QAction("🔍+ Zoom In", self)
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_in_action.setEnabled(False)
        toolbar.addAction(self.zoom_in_action)
        
        toolbar.addSeparator()
        
        # Advanced fit controls
        self.fit_width_action = QAction("📐 Fit Width", self)
        self.fit_width_action.triggered.connect(self.fit_to_width)
        self.fit_width_action.setEnabled(False)
        toolbar.addAction(self.fit_width_action)
        
        self.fit_height_action = QAction("📏 Fit Height", self)
        self.fit_height_action.triggered.connect(self.fit_to_height)
        self.fit_height_action.setEnabled(False)
        toolbar.addAction(self.fit_height_action)
        
        self.fit_page_action = QAction("🖼️ Fit Page", self)
        self.fit_page_action.triggered.connect(self.fit_to_page)
        self.fit_page_action.setEnabled(False)
        toolbar.addAction(self.fit_page_action)
        
        self.actual_size_action = QAction("📋 Actual Size", self)
        self.actual_size_action.triggered.connect(self.actual_size)
        self.actual_size_action.setEnabled(False)
        toolbar.addAction(self.actual_size_action)
        
        toolbar.addSeparator()
        
        # Rotation controls
        self.rotate_left_action = QAction("↺ Rotate Left", self)
        self.rotate_left_action.triggered.connect(self.rotate_left)
        self.rotate_left_action.setEnabled(False)
        toolbar.addAction(self.rotate_left_action)
        
        self.rotate_right_action = QAction("↻ Rotate Right", self)
        self.rotate_right_action.triggered.connect(self.rotate_right)
        self.rotate_right_action.setEnabled(False)
        toolbar.addAction(self.rotate_right_action)
        
        layout.addWidget(toolbar)
        
        # Secondary toolbar for quick zoom controls
        quick_toolbar = QToolBar()
        quick_toolbar.setIconSize(QSize(20, 20))
        quick_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        quick_toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 2px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                color: #495057;
                padding: 4px 8px;
                border-radius: 3px;
                margin: 1px;
                font-size: 11px;
            }
            QToolButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        
        # Quick zoom buttons
        self.zoom_25_action = QAction("25%", self)
        self.zoom_25_action.triggered.connect(lambda: self.set_zoom_level(25))
        self.zoom_25_action.setEnabled(False)
        quick_toolbar.addAction(self.zoom_25_action)
        
        self.zoom_50_action = QAction("50%", self)
        self.zoom_50_action.triggered.connect(lambda: self.set_zoom_level(50))
        self.zoom_50_action.setEnabled(False)
        quick_toolbar.addAction(self.zoom_50_action)
        
        self.zoom_75_action = QAction("75%", self)
        self.zoom_75_action.triggered.connect(lambda: self.set_zoom_level(75))
        self.zoom_75_action.setEnabled(False)
        quick_toolbar.addAction(self.zoom_75_action)
        
        self.zoom_100_action = QAction("100%", self)
        self.zoom_100_action.triggered.connect(lambda: self.set_zoom_level(100))
        self.zoom_100_action.setEnabled(False)
        quick_toolbar.addAction(self.zoom_100_action)
        
        self.zoom_125_action = QAction("125%", self)
        self.zoom_125_action.triggered.connect(lambda: self.set_zoom_level(125))
        self.zoom_125_action.setEnabled(False)
        quick_toolbar.addAction(self.zoom_125_action)
        
        self.zoom_150_action = QAction("150%", self)
        self.zoom_150_action.triggered.connect(lambda: self.set_zoom_level(150))
        self.zoom_150_action.setEnabled(False)
        quick_toolbar.addAction(self.zoom_150_action)
        
        self.zoom_200_action = QAction("200%", self)
        self.zoom_200_action.triggered.connect(lambda: self.set_zoom_level(200))
        self.zoom_200_action.setEnabled(False)
        quick_toolbar.addAction(self.zoom_200_action)
        
        layout.addWidget(quick_toolbar)
        
        # Status/Help bar
        help_label = QLabel("💡 Tips: Ctrl+Wheel=Zoom | Ctrl+0=Actual Size | Ctrl+1=Fit Width | Ctrl+2=Fit Height | Ctrl+3=Fit Page | ←→=Navigate")
        help_label.setStyleSheet("""
            QLabel {
                background-color: #e7f3ff;
                border: 1px solid #b8daff;
                border-radius: 4px;
                padding: 6px 10px;
                color: #004085;
                font-size: 11px;
                font-style: italic;
            }
        """)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        # Current file label with modern styling
        self.file_label = QLabel("📄 No PDF loaded")
        self.file_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                color: #212529;
                font-style: italic;
                font-weight: 500;
            }
        """)
        layout.addWidget(self.file_label)
        
        # PDF display area with modern scroll area and horizontal scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)  # Changed to False to enable manual sizing
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background-color: #f8f9fa;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                width: 12px;
            }
            QScrollBar:horizontal {
                height: 12px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background-color: #ced4da;
                border-radius: 6px;
                min-height: 20px;
                min-width: 20px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background-color: #adb5bd;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                border: none;
                background: none;
            }
        """)
        
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: none;
                color: #212529;
                font-size: 14px;
                padding: 40px;
                font-weight: 500;
            }
        """)
        self.pdf_label.setText("📄 No PDF loaded\n\nClick 'Load PDF' to open a document")
        self.pdf_label.setMinimumSize(400, 500)
        
        self.scroll_area.setWidget(self.pdf_label)
        layout.addWidget(self.scroll_area)
        
    def setup_context_menu(self):
        """Setup context menu for PDF viewing area"""
        self.pdf_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pdf_label.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """Show context menu at the given position"""
        if not self.pdf_document:
            return
            
        from PyQt6.QtWidgets import QMenu
        context_menu = QMenu(self)
        
        # Add zoom actions
        context_menu.addAction(self.zoom_in_action)
        context_menu.addAction(self.zoom_out_action)
        context_menu.addSeparator()
        
        # Add fit actions
        context_menu.addAction(self.fit_width_action)
        context_menu.addAction(self.fit_height_action)
        context_menu.addAction(self.fit_page_action)
        context_menu.addAction(self.actual_size_action)
        context_menu.addSeparator()
        
        # Add rotation actions
        context_menu.addAction(self.rotate_left_action)
        context_menu.addAction(self.rotate_right_action)
        context_menu.addSeparator()
        
        # Add navigation actions
        context_menu.addAction(self.prev_action)
        context_menu.addAction(self.next_action)
        
        # Show the menu
        global_position = self.pdf_label.mapToGlobal(position)
        context_menu.exec(global_position)
        
    def load_pdf_dialog(self):
        """Show file dialog to load PDF"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open PDF File", 
            "", 
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            self.load_pdf(file_path)
        
    def load_pdf(self, file_path):
        """Load a PDF file"""
        try:
            if self.pdf_document:
                self.pdf_document.close()
            
            self.pdf_document = fitz.open(file_path)
            self.total_pages = len(self.pdf_document)
            self.current_page = 0
            
            # Update UI controls
            self.page_spinbox.setMaximum(self.total_pages)
            self.page_spinbox.setValue(1)
            self.page_spinbox.setEnabled(True)
            
            self.prev_action.setEnabled(False)
            self.next_action.setEnabled(self.total_pages > 1)
            self.zoom_in_action.setEnabled(True)
            self.zoom_out_action.setEnabled(True)
            self.fit_width_action.setEnabled(True)
            self.fit_height_action.setEnabled(True)
            self.fit_page_action.setEnabled(True)
            self.actual_size_action.setEnabled(True)
            self.rotate_left_action.setEnabled(True)
            self.rotate_right_action.setEnabled(True)
            
            # Enable quick zoom buttons
            self.zoom_25_action.setEnabled(True)
            self.zoom_50_action.setEnabled(True)
            self.zoom_75_action.setEnabled(True)
            self.zoom_100_action.setEnabled(True)
            self.zoom_125_action.setEnabled(True)
            self.zoom_150_action.setEnabled(True)
            self.zoom_200_action.setEnabled(True)
            
            self.zoom_factor = 1.0
            self.rotation = 0
            self.fit_mode = "none"
            self.update_page_display()
            self.file_label.setText(f"📄 {os.path.basename(file_path)} loaded")
            self.file_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: #155724;
                    font-weight: bold;
                }
            """)
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load PDF: {str(e)}")
            self.file_label.setText("❌ Failed to load PDF")
            self.file_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: #721c24;
                    font-weight: bold;
                }
            """)
            return False
            
    def update_page_display(self):
        """Update the displayed page with enhanced rendering"""
        if not self.pdf_document or self.current_page >= self.total_pages:
            return
            
        try:
            # Get the page
            page = self.pdf_document[self.current_page]
            
            # Create transformation matrix for zoom and rotation
            mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            
            # Apply rotation if needed
            if self.rotation != 0:
                rot_mat = fitz.Matrix(self.rotation)
                mat = mat * rot_mat
            
            # Render page to pixmap with high quality
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to QImage with better quality
            img_data = pix.tobytes("ppm")
            qimg = QImage.fromData(img_data, "PPM")
            
            # Convert to QPixmap and display
            pixmap = QPixmap.fromImage(qimg)
            self.pdf_label.setPixmap(pixmap)
            
            # Set the label size to match the pixmap size for proper scrolling
            self.pdf_label.resize(pixmap.size())
            self.pdf_label.setMinimumSize(pixmap.size())
            
            # Update page info with fit mode indicator
            fit_indicator = ""
            if self.fit_mode == "width":
                fit_indicator = " [Fit Width]"
            elif self.fit_mode == "height":
                fit_indicator = " [Fit Height]"
            elif self.fit_mode == "page":
                fit_indicator = " [Fit Page]"
            
            rotation_indicator = ""
            if self.rotation != 0:
                rotation_indicator = f" [Rotated {self.rotation}°]"
            
            self.page_label.setText(f"/ {self.total_pages}{fit_indicator}{rotation_indicator}")
            self.page_spinbox.setValue(self.current_page + 1)
            self.zoom_label.setText(f"{int(self.zoom_factor * 100)}%")
            
            # Update navigation buttons
            self.prev_action.setEnabled(self.current_page > 0)
            self.next_action.setEnabled(self.current_page < self.total_pages - 1)
            
            # Update zoom buttons based on current zoom level
            self.zoom_out_action.setEnabled(self.zoom_factor > self.min_zoom)
            self.zoom_in_action.setEnabled(self.zoom_factor < self.max_zoom)
            
            # Emit page changed signal
            self.page_changed.emit(self.current_page)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display page: {str(e)}")
            
    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_display()
            
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page_display()
            
    def go_to_page(self, page_num):
        """Go to specific page (1-indexed)"""
        if 1 <= page_num <= self.total_pages:
            self.current_page = page_num - 1
            self.update_page_display()
            
    def zoom_in(self):
        """Zoom in"""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor = min(self.zoom_factor * 1.25, self.max_zoom)
            self.update_page_display()
            
    def zoom_out(self):
        """Zoom out"""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor = max(self.zoom_factor / 1.25, self.min_zoom)
            self.update_page_display()
            
    def fit_to_width(self):
        """Fit page to viewer width"""
        if not self.pdf_document:
            return
            
        try:
            page = self.pdf_document[self.current_page]
            page_rect = page.rect
            
            # Calculate zoom factor to fit width
            viewer_width = self.scroll_area.viewport().width() - 20  # Account for margins
            page_width = page_rect.width
            
            if page_width > 0:
                self.zoom_factor = viewer_width / page_width
                self.zoom_factor = max(self.min_zoom, min(self.zoom_factor, self.max_zoom))
                self.fit_mode = "width"
                self.update_page_display()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fit to width: {str(e)}")
            
    def fit_to_height(self):
        """Fit page to viewer height"""
        if not self.pdf_document:
            return
            
        try:
            page = self.pdf_document[self.current_page]
            page_rect = page.rect
            
            # Calculate zoom factor to fit height
            viewer_height = self.scroll_area.viewport().height() - 20  # Account for margins
            page_height = page_rect.height
            
            if page_height > 0:
                self.zoom_factor = viewer_height / page_height
                self.zoom_factor = max(self.min_zoom, min(self.zoom_factor, self.max_zoom))
                self.fit_mode = "height"
                self.update_page_display()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fit to height: {str(e)}")
    
    def fit_to_page(self):
        """Fit entire page to viewer (both width and height)"""
        if not self.pdf_document:
            return
            
        try:
            page = self.pdf_document[self.current_page]
            page_rect = page.rect
            
            # Calculate zoom factor to fit both width and height
            viewer_width = self.scroll_area.viewport().width() - 20
            viewer_height = self.scroll_area.viewport().height() - 20
            page_width = page_rect.width
            page_height = page_rect.height
            
            if page_width > 0 and page_height > 0:
                width_zoom = viewer_width / page_width
                height_zoom = viewer_height / page_height
                # Use the smaller zoom factor to ensure the entire page fits
                self.zoom_factor = min(width_zoom, height_zoom)
                self.zoom_factor = max(self.min_zoom, min(self.zoom_factor, self.max_zoom))
                self.fit_mode = "page"
                self.update_page_display()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fit to page: {str(e)}")
    
    def actual_size(self):
        """Reset to actual size (100% zoom)"""
        self.zoom_factor = 1.0
        self.fit_mode = "none"
        self.update_page_display()
    
    def rotate_left(self):
        """Rotate page 90 degrees counter-clockwise"""
        self.rotation = (self.rotation - 90) % 360
        self.update_page_display()
    
    def rotate_right(self):
        """Rotate page 90 degrees clockwise"""
        self.rotation = (self.rotation + 90) % 360
        self.update_page_display()
    
    def zoom_to_selection(self, rect):
        """Zoom to a specific rectangular area (for future enhancement)"""
        if not self.pdf_document:
            return
        
        try:
            page = self.pdf_document[self.current_page]
            page_rect = page.rect
            
            # Calculate zoom factor based on selection
            viewer_width = self.scroll_area.viewport().width() - 20
            viewer_height = self.scroll_area.viewport().height() - 20
            
            selection_width = rect.width()
            selection_height = rect.height()
            
            if selection_width > 0 and selection_height > 0:
                width_zoom = viewer_width / selection_width
                height_zoom = viewer_height / selection_height
                self.zoom_factor = min(width_zoom, height_zoom)
                self.zoom_factor = max(self.min_zoom, min(self.zoom_factor, self.max_zoom))
                self.fit_mode = "selection"
                self.update_page_display()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to zoom to selection: {str(e)}")
    
    def set_zoom_level(self, zoom_percent):
        """Set specific zoom level by percentage"""
        self.zoom_factor = zoom_percent / 100.0
        self.zoom_factor = max(self.min_zoom, min(self.zoom_factor, self.max_zoom))
        self.fit_mode = "none"
        self.update_page_display()
    
    def get_zoom_level(self):
        """Get current zoom level as percentage"""
        return int(self.zoom_factor * 100)
    
    def close_document(self):
        """Close the current document"""
        if self.pdf_document:
            self.pdf_document.close()
            self.pdf_document = None
            
        self.pdf_label.clear()
        self.pdf_label.setText("No PDF loaded")
        self.current_page = 0
        self.total_pages = 0
        
        # Disable controls
        self.prev_action.setEnabled(False)
        self.next_action.setEnabled(False)
        self.zoom_in_action.setEnabled(False)
        self.zoom_out_action.setEnabled(False)
        self.fit_width_action.setEnabled(False)
        self.fit_height_action.setEnabled(False)
        self.fit_page_action.setEnabled(False)
        self.actual_size_action.setEnabled(False)
        self.rotate_left_action.setEnabled(False)
        self.rotate_right_action.setEnabled(False)
        self.page_spinbox.setEnabled(False)
        
        # Disable quick zoom buttons
        self.zoom_25_action.setEnabled(False)
        self.zoom_50_action.setEnabled(False)
        self.zoom_75_action.setEnabled(False)
        self.zoom_100_action.setEnabled(False)
        self.zoom_125_action.setEnabled(False)
        self.zoom_150_action.setEnabled(False)
        self.zoom_200_action.setEnabled(False)
        
        self.page_label.setText("/ 0")
        self.zoom_label.setText("100%")
        self.file_label.setText("📄 No PDF loaded")
        self.file_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                color: #212529;
                font-style: italic;
                font-weight: 500;
            }
        """)
        
    def closeEvent(self, event):
        """Handle widget close event"""
        self.close_document()
        super().closeEvent(event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming with Ctrl key"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom with Ctrl + wheel
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            # Normal scrolling
            super().wheelEvent(event)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for PDF navigation"""
        key = event.key()
        modifiers = event.modifiers()
        
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
                self.zoom_in()
                event.accept()
            elif key == Qt.Key.Key_Minus:
                self.zoom_out()
                event.accept()
            elif key == Qt.Key.Key_0:
                self.actual_size()
                event.accept()
            elif key == Qt.Key.Key_1:
                self.fit_to_width()
                event.accept()
            elif key == Qt.Key.Key_2:
                self.fit_to_height()
                event.accept()
            elif key == Qt.Key.Key_3:
                self.fit_to_page()
                event.accept()
            else:
                super().keyPressEvent(event)
        elif key == Qt.Key.Key_PageDown or key == Qt.Key.Key_Right:
            self.next_page()
            event.accept()
        elif key == Qt.Key.Key_PageUp or key == Qt.Key.Key_Left:
            self.previous_page()
            event.accept()
        elif key == Qt.Key.Key_Home:
            self.go_to_page(1)
            event.accept()
        elif key == Qt.Key.Key_End:
            self.go_to_page(self.total_pages)
            event.accept()
        else:
            super().keyPressEvent(event)
