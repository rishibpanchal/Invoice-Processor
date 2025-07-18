# 🛠️ Development Guide - Invoice Processor FRESH 2.0

This guide provides detailed information for developers who want to understand, modify, or extend the invoice processing application.

## 🏗️ Architecture Overview

### Application Structure

```
FRESH 2.0/
│
├── 🚀 Entry Points
│   ├── launch.py              # Main launcher with setup
│   ├── batch_process.py       # CLI batch processing
│   └── qt viewer/main_qt.py   # GUI application
│
├── 🧠 Core Logic
│   ├── extraction/            # Extraction engine
│   └── qt viewer/enhanced_extractor.py  # GUI integration
│
├── 🎨 User Interface
│   ├── qt viewer/main_qt.py   # Main GUI application
│   └── qt viewer/pdf_viewer.py # PDF viewing widget
│
└── 📄 Configuration
    ├── requirements.txt       # Dependencies
    ├── extraction/system_prompt.txt # AI prompts
    └── files/                 # Sample data
```

### Data Flow

```
PDF File → PDF Extraction → AI Processing → Structured Data → GUI Display
    ↓           ↓                ↓              ↓             ↓
pdfplumber → Markdown → Ollama/Gemma → JSON → PyQt6 Tables
```

## 🔧 Component Details

### 1. Enhanced Extractor (`enhanced_extractor.py`)

**Purpose**: Central extraction engine that integrates PDF processing with AI analysis.

**Key Methods**:
```python
class EnhancedInvoiceExtractor:
    def extract_data(pdf_path: str) -> Dict[str, Any]
    def validate_extracted_data(data: Dict) -> Dict
    def export_to_json(data: Dict, file_path: str) -> bool
    def export_to_csv(data: Dict, file_path: str) -> bool
```

**Customization Points**:
- AI model selection in `generate_response()`
- Field validation rules in `validate_extracted_data()`
- Export formats in `export_to_*()` methods
- Error handling strategies

### 2. GUI Application (`main_qt.py`)

**Purpose**: Modern PyQt6 interface for interactive invoice processing.

**Key Components**:
- `InvoiceProcessorApp`: Main application window
- `ProcessingThread`: Background processing thread
- `PDFViewer`: Integrated PDF viewer widget

**UI Structure**:
```python
QMainWindow
├── QSplitter (horizontal)
│   ├── PDF Viewer Pane (left)
│   │   └── PDFViewer widget
│   └── Controls Pane (right)
│       ├── File Controls
│       ├── Export Actions  
│       └── QTabWidget
│           ├── Invoice Info Table
│           ├── Line Items Table
│           ├── Raw Text View
│           └── JSON Data View
```

**Customization Points**:
- UI styling in `setup_modern_styling()`
- Table display logic in `populate_*_table()`
- Status messages and progress handling
- Menu and toolbar customization

### 3. PDF Viewer (`pdf_viewer.py`)

**Purpose**: Advanced PDF viewing with navigation, zoom, and rotation.

**Features**:
- Multi-page navigation
- Zoom controls (fit to width/height/page)
- Rotation (90-degree increments)
- Modern UI with toolbar controls

**Customization Points**:
- Rendering quality settings
- Navigation controls
- Display modes and layouts

### 4. Extraction Pipeline (`extraction/`)

**Components**:
- `extract.py`: PDF to text conversion using pdfplumber
- `ollama.py`: AI model interface
- `system_prompt.txt`: AI instruction templates
- `main.py`: Command-line extraction tool

## 🎯 Customization Scenarios

### Adding New AI Models

1. **Update Model Configuration**:
```python
# In extraction/ollama.py
def generate(prompt: str, model: str = "your-new-model") -> str:
```

2. **Test Model Compatibility**:
```python
# Test with a sample prompt
extractor = EnhancedInvoiceExtractor()
test_result = extractor.generate_response("Test prompt")
```

3. **Adjust Prompts if Needed**:
```text
# In extraction/system_prompt.txt
extraction: 
Your model-specific instructions...
```

### Adding New Export Formats

1. **Extend Enhanced Extractor**:
```python
def export_to_xml(self, data: Dict[str, Any], file_path: str) -> bool:
    """Export to XML format"""
    try:
        # Implementation here
        return True
    except Exception as e:
        print(f"Error exporting XML: {e}")
        return False
```

2. **Add GUI Button**:
```python
# In main_qt.py create_controls_and_data_pane()
self.export_xml_button = QPushButton("📄 Export XML")
self.export_xml_button.clicked.connect(self.export_xml)
```

3. **Implement Handler**:
```python
def export_xml(self):
    """Export data to XML file"""
    if not self.current_invoice_data:
        QMessageBox.warning(self, "Warning", "No data to export.")
        return
    # Implementation...
```

### Adding New Invoice Fields

1. **Update System Prompt**:
```text
# In extraction/system_prompt.txt
Required fields: invoice_number, invoice_date, vendor_name, total_amount, your_new_field
Optional fields: existing_fields, your_optional_field
```

2. **Update Validation**:
```python
# In enhanced_extractor.py validate_extracted_data()
required_fields = ['invoice_number', 'invoice_date', 'vendor_name', 'total_amount', 'your_new_field']
```

3. **Update Display Logic**:
```python
# In main_qt.py populate_info_table()
field_icons = {
    'your_new_field': '🏷️',
    # ... existing icons
}
```

### Custom Processing Workflows

1. **Pre-processing Hooks**:
```python
class CustomInvoiceExtractor(EnhancedInvoiceExtractor):
    def extract_data(self, pdf_path: str) -> Dict[str, Any]:
        # Custom pre-processing
        pdf_path = self.preprocess_pdf(pdf_path)
        
        # Call parent method
        result = super().extract_data(pdf_path)
        
        # Custom post-processing
        return self.postprocess_result(result)
```

2. **Custom Validation Rules**:
```python
def custom_validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Custom validation logic"""
    # Business-specific validation
    if data.get('total_amount', 0) > 10000:
        # Require additional approval fields
        pass
    
    return data
```

## 🧪 Testing and Development

### Running Tests

```bash
# Test extraction functionality
python -c "
from qt_viewer.enhanced_extractor import EnhancedInvoiceExtractor
extractor = EnhancedInvoiceExtractor()
result = extractor.extract_data('files/invoice-template-1_2.pdf')
print('Fields extracted:', len([k for k,v in result.items() if v]))
"

# Test GUI components
python qt_viewer/main_qt.py

# Test batch processing
python batch_process.py --test
```

### Development Environment Setup

1. **Install Development Dependencies**:
```bash
pip install -r requirements.txt
pip install pytest black pylint  # Additional dev tools
```

2. **Enable Debug Mode**:
```python
# In main_qt.py or enhanced_extractor.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

3. **Use Virtual Environment**:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Debugging Common Issues

1. **Extraction Failures**:
```python
# Add debug output to enhanced_extractor.py
def extract_data(self, pdf_path: str):
    try:
        markdown_content = pdf_to_markdown(pdf_path)
        print(f"DEBUG: Extracted {len(markdown_content)} characters")
        
        prompt = self.create_final_prompt(markdown_content)
        print(f"DEBUG: Prompt length: {len(prompt)}")
        
        response = self.generate_response(prompt)
        print(f"DEBUG: Response length: {len(response)}")
        # ... rest of method
```

2. **GUI Issues**:
```python
# Enable Qt debug output
import sys
from PyQt6.QtCore import QLoggingCategory
QLoggingCategory.setFilterRules("qt.*.debug=true")
```

3. **Model Issues**:
```bash
# Test Ollama directly
curl http://localhost:11434/api/generate -d '{
  "model": "gemma3n:e2b",
  "prompt": "Test prompt"
}'
```

## 📚 API Reference

### EnhancedInvoiceExtractor

```python
class EnhancedInvoiceExtractor:
    def __init__(self) -> None
    def load_system_prompt(self) -> Dict[str, str]
    def extract_data(self, pdf_path: str) -> Dict[str, Any]
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]
    def format_for_display(self, data: Dict[str, Any]) -> Dict[str, Any]
    def export_to_json(self, data: Dict[str, Any], file_path: str) -> bool
    def export_to_csv(self, data: Dict[str, Any], file_path: str) -> bool
    def get_extraction_summary(self, data: Dict[str, Any]) -> Dict[str, Any]
```

### Data Structure

**Extracted Data Format**:
```python
{
    # Required fields
    "invoice_number": str,
    "invoice_date": str,  # YYYY-MM-DD format
    "vendor_name": str,
    "total_amount": float,
    
    # Optional vendor info
    "vendor_address": str,
    "vendor_gst": str,
    "vendor_contact": str,
    
    # Line items
    "line_items": [
        {
            "item_description": str,
            "quantity": float,
            "unit_price": float,
            "total_amount": float,
            "tax_amount": float
        }
    ],
    
    # Metadata
    "_metadata": {
        "source_file": str,
        "extraction_method": str,
        "validation": {
            "is_valid": bool,
            "missing_required_fields": [str],
            "warnings": [str]
        }
    },
    
    # GUI-specific
    "raw_text": str  # Original extracted text
}
```

## 🚀 Deployment

### Creating Standalone Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onedir --windowed \
    --add-data "extraction;extraction" \
    --add-data "files;files" \
    --name "InvoiceProcessor" \
    launch.py
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "batch_process.py", "/data"]
```

### Configuration Management

```python
# config.py
import os
from pathlib import Path

class Config:
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    MODEL_NAME = os.getenv("MODEL_NAME", "gemma3n:e2b")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "50000000"))  # 50MB
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
```

## 🔍 Performance Optimization

### Processing Large Files

```python
def extract_large_pdf(self, pdf_path: str, chunk_size: int = 1000) -> Dict[str, Any]:
    """Process large PDFs in chunks"""
    # Implementation for chunked processing
    pass
```

### Caching Strategies

```python
import functools
from functools import lru_cache

class EnhancedInvoiceExtractor:
    @lru_cache(maxsize=128)
    def cached_extract_text(self, pdf_path: str) -> str:
        """Cache text extraction results"""
        return pdf_to_markdown(pdf_path)
```

### Memory Management

```python
def process_batch_efficiently(self, file_list: List[str]) -> None:
    """Process files with memory management"""
    for file_path in file_list:
        result = self.extract_data(file_path)
        # Process result immediately
        self.save_result(result)
        # Clear memory
        del result
```

---

This development guide provides the foundation for extending and customizing the invoice processor. For specific implementation questions, refer to the inline code documentation and the main README.md file.
