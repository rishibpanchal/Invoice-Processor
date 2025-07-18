# 🧾 Invoice Data Processor - FRESH 2.0

A modern, AI-powered invoice processing application that combines a beautiful PyQt6 GUI with advanced PDF extraction capabilities using Ollama AI models.

## ✨ Features

### 🎨 Modern GUI Interface
- **Beautiful Qt6 Interface**: Modern, responsive design with professional styling
- **PDF Viewer**: Built-in PDF viewer with zoom, rotation, and navigation controls
- **Multi-tab Data Display**: Organized tabs for invoice info, line items, raw text, and JSON
- **Real-time Processing**: Background processing with progress indicators
- **Export Capabilities**: Export to JSON and CSV formats

### 🤖 AI-Powered Extraction
- **Advanced Text Extraction**: Uses pdfplumber for reliable PDF text extraction
- **AI Data Structuring**: Ollama-based AI models for intelligent data parsing
- **Flexible Schema**: Comprehensive field extraction including vendor info, line items, taxes
- **Error Handling**: Robust error handling with detailed feedback
- **Validation**: Automatic validation of extracted data with warnings

### 📊 Data Management
- **Structured Output**: Clean, validated JSON output
- **Line Items**: Detailed extraction of individual invoice line items
- **Metadata**: Processing metadata and extraction statistics
- **Export Options**: Multiple export formats (JSON, CSV)

## 🏗️ Project Structure

```
FRESH 2.0/
├── launch.py                  # Application launcher and setup script
├── requirements.txt           # Python dependencies
├── extraction/                # Core extraction logic
│   ├── extract.py            # PDF to text extraction
│   ├── ollama.py             # Ollama AI interface
│   └── system_prompt.txt     # AI prompts and templates
├── qt viewer/                 # GUI application
│   ├── main_qt.py           # Main GUI application
│   ├── pdf_viewer.py        # PDF viewer widget
│   └── enhanced_extractor.py # Integrated extractor class
└── files/                     # Sample invoice files
    └── invoice-template-1_2.pdf
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed on your system
2. **Ollama** installed and running ([Download here](https://ollama.ai))
3. **Required AI Model** - The application uses `gemma3n:e2b` by default

### Installation

1. **Clone or download** this repository
2. **Run the launcher** - It will handle all setup automatically:
   ```bash
   python launch.py
   ```

The launcher will:
- ✅ Check Python version compatibility
- 📦 Install required Python packages
- 🤖 Verify Ollama server is running
- 🔍 Check for the required AI model
- 🧪 Test the extraction functionality
- 🚀 Launch the GUI application

### Manual Installation

If you prefer manual setup:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure Ollama is running
ollama serve

# Install the required model
ollama pull gemma3n:e2b

# Launch the GUI
cd "qt viewer"
python main_qt.py
```

## 📖 Usage Guide

### Using the GUI Application

1. **Launch the Application**
   ```bash
   python launch.py
   ```

2. **Load a PDF Invoice**
   - Click "📂 Load PDF" button
   - Select your invoice PDF file
   - The PDF will display in the left panel

3. **Process the Invoice**
   - Click "⚡ Process PDF" button
   - Wait for AI processing to complete
   - View results in the tabs on the right

4. **Review Extracted Data**
   - **📋 Invoice Info**: Key invoice fields
   - **📦 Line Items**: Individual invoice line items
   - **📄 Raw Text**: Original extracted text
   - **🔧 JSON Data**: Complete structured data

5. **Export Results**
   - **📁 Export JSON**: Complete data export
   - **📊 Export CSV**: Line items in spreadsheet format

### Using the Command Line

For batch processing or scripting:

```bash
cd extraction
python main.py path/to/invoice.pdf
```

## 🔧 Configuration

### AI Model Configuration

Edit `extraction/ollama.py` to change the default model:

```python
def generate(prompt: str, model: str = "your-model-name") -> str:
```

### Extraction Templates

Customize the extraction prompts in `extraction/system_prompt.txt`:

```text
extraction: 
Your custom extraction prompt here...
Required fields: invoice_number, invoice_date, vendor_name, total_amount
{invoice_text}
```

### GUI Customization

The GUI styling can be customized in `qt viewer/main_qt.py` in the `setup_modern_styling()` method.

## 📋 Supported Invoice Fields

### Required Fields
- Invoice Number
- Invoice Date  
- Vendor Name
- Total Amount

### Optional Fields
- Vendor information (address, GST, contact details)
- Line items (description, quantity, price, taxes)
- Customer/Consignee information
- Payment terms and bank details
- Tax details (CGST, SGST, IGST, UTGST)
- Shipping and billing addresses

## 🛠️ Dependencies

### Python Packages
- `PyQt6` - Modern GUI framework
- `pdfplumber` - PDF text extraction
- `requests` - HTTP client for Ollama API
- `PyMuPDF` - PDF rendering for viewer
- `pillow` - Image processing
- `pandas` - Data manipulation for CSV export

### External Services
- **Ollama** - Local AI model server
- **AI Model** - Default: `gemma3n:e2b` (or compatible model)

## 🔍 Troubleshooting

### Common Issues

**"Ollama server not accessible"**
- Ensure Ollama is installed and running
- Check if service is available at `http://localhost:11434`
- Try: `ollama serve` to start the server

**"Model not found"**
- Install the required model: `ollama pull gemma3n:e2b`
- Or update the model name in `extraction/ollama.py`

**"Import errors"**
- Run: `pip install -r requirements.txt`
- Ensure you're using Python 3.8+

**"PDF not loading"**
- Ensure PDF file is not corrupted
- Check if PDF contains extractable text (not just images)
- Try with a different PDF file

**"No data extracted"**
- Verify Ollama model is responding
- Check the raw text tab to see if text was extracted
- Review the JSON tab for error messages

### Getting Help

1. **Check the Status Bar** - Shows current operation status
2. **Review Error Messages** - Detailed error info in the GUI
3. **Check Console Output** - Additional debug information
4. **Test with Sample Files** - Use provided sample invoices

## 🎯 Advanced Usage

### Batch Processing

Create a script for batch processing:

```python
from qt_viewer.enhanced_extractor import EnhancedInvoiceExtractor
import json
from pathlib import Path

extractor = EnhancedInvoiceExtractor()
input_dir = Path("invoices/")
output_dir = Path("results/")

for pdf_file in input_dir.glob("*.pdf"):
    result = extractor.extract_data(str(pdf_file))
    output_file = output_dir / f"{pdf_file.stem}.json"
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
```

### Custom AI Models

To use a different AI model:

1. Install the model: `ollama pull your-model-name`
2. Update `extraction/ollama.py`
3. Optionally adjust prompts in `system_prompt.txt`

### Integration with Other Systems

The `EnhancedInvoiceExtractor` class can be imported and used in other applications:

```python
from enhanced_extractor import EnhancedInvoiceExtractor

extractor = EnhancedInvoiceExtractor()
result = extractor.extract_data("invoice.pdf")

# Use the structured data
invoice_data = result
vendor_name = invoice_data.get("vendor_name")
total_amount = invoice_data.get("total_amount")
```

## 📈 Performance Tips

- **Large PDFs**: May take longer to process - progress is shown in status bar
- **Model Response**: First request may be slower as model loads
- **Memory Usage**: Close unused PDFs to free memory
- **Batch Processing**: Process multiple files sequentially for best results

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional AI model support
- Enhanced PDF extraction methods
- Improved field validation
- Additional export formats
- Localization support

## 📄 License

This project is provided as-is for educational and development purposes.

---

**Built with ❤️ using PyQt6, Ollama, and modern AI technology**
