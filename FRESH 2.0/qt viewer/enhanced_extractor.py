"""
Enhanced Invoice Extractor - Integrates extraction functionality with Qt GUI
"""
import sys
import os
import json
import re
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# Try different import strategies
try:
    from extraction.extract import pdf_to_markdown
    from extraction.ollama import generate as ollama_generate
except ImportError:
    # Fallback: try importing from current working directory
    import os
    original_path = sys.path.copy()
    sys.path.insert(0, os.getcwd())
    try:
        from extraction.extract import pdf_to_markdown
        from extraction.ollama import generate as ollama_generate
    except ImportError as e:
        sys.path = original_path  # Restore original path
        raise ImportError(f"Cannot import extraction modules. Please ensure you're running from the project root directory. Error: {e}")


class EnhancedInvoiceExtractor:
    """Enhanced invoice extractor that combines PDF extraction with AI processing"""
    
    def __init__(self):
        self.system_prompts = self.load_system_prompt()
        
    def load_system_prompt(self) -> Dict[str, str]:
        """Load the system prompt templates from system_prompt.txt"""
        # Try multiple possible locations for the system prompt file
        possible_paths = [
            Path(__file__).parent.parent / "extraction" / "system_prompt.txt",  # From qt viewer
            Path.cwd() / "extraction" / "system_prompt.txt",  # From project root
            Path(__file__).parent / ".." / "extraction" / "system_prompt.txt",  # Relative path
        ]
        
        system_prompt_path = None
        for path in possible_paths:
            if path.exists():
                system_prompt_path = path
                break
        
        if system_prompt_path is None:
            raise FileNotFoundError(f"System prompt file not found in any of these locations: {[str(p) for p in possible_paths]}")
        
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the different prompt templates
        prompts = {}
        sections = content.split('\n    \n    ')
        
        for section in sections:
            if ':' in section:
                name, template = section.split(':', 1)
                prompts[name.strip()] = template.strip()
        
        return prompts
    
    def create_final_prompt(self, invoice_content: str, prompt_type: str = "extraction") -> str:
        """Create the final prompt by combining system prompt with invoice content"""
        if prompt_type not in self.system_prompts:
            raise ValueError(f"Prompt type '{prompt_type}' not found in system prompts")
        
        template = self.system_prompts[prompt_type]
        return template.replace("{invoice_text}", invoice_content)
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama model"""
        try:
            return ollama_generate(prompt)
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
    
    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from the response using regex"""
        # Find JSON content between ```json and ``` or just look for JSON object
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if match:
            json_str = match.group(1)
        else:
            # Try to find JSON object directly
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                raise ValueError("No valid JSON found in response")
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    
    def extract_data(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main extraction method that processes a PDF file and returns structured data
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            Dict[str, Any]: Extracted invoice data
        """
        try:
            # Step 1: Convert PDF to markdown
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            markdown_content = pdf_to_markdown(pdf_path)
            
            if not markdown_content.strip():
                raise ValueError("No text content extracted from PDF")
            
            # Step 2: Create extraction prompt
            prompt = self.create_final_prompt(markdown_content, "extraction")
            
            # Step 3: Generate AI response
            response = self.generate_response(prompt)
            
            if not response.strip():
                raise ValueError("Empty response from AI model")
            
            # Step 4: Extract JSON from response
            extracted_data = self.extract_json_from_response(response)
            
            # Step 5: Add metadata and raw text
            extracted_data['_metadata'] = {
                'source_file': pdf_path,
                'extraction_method': 'enhanced_extractor',
                'markdown_length': len(markdown_content),
                'raw_response_length': len(response)
            }
            
            # Add raw text for display in GUI
            extracted_data['raw_text'] = markdown_content
            
            # Validate and format the data
            extracted_data = self.validate_extracted_data(extracted_data)
            
            return extracted_data
            
        except Exception as e:
            # Return error information in a structured format
            return {
                'error': True,
                'error_message': str(e),
                'error_type': type(e).__name__,
                'raw_text': '',
                '_metadata': {
                    'source_file': pdf_path,
                    'extraction_method': 'enhanced_extractor',
                    'failed': True
                }
            }
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted data
        
        Args:
            data (Dict[str, Any]): Raw extracted data
            
        Returns:
            Dict[str, Any]: Validated and cleaned data
        """
        if data.get('error', False):
            return data
        
        # Define required fields
        required_fields = ['invoice_number', 'invoice_date', 'vendor_name', 'total_amount']
        
        validation_results = {
            'is_valid': True,
            'missing_required_fields': [],
            'warnings': []
        }
        
        # Check for required fields
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                validation_results['missing_required_fields'].append(field)
                validation_results['is_valid'] = False
        
        # Add validation results to metadata
        if '_metadata' not in data:
            data['_metadata'] = {}
        data['_metadata']['validation'] = validation_results
        
        return data
    
    def format_for_display(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format extracted data for display in the GUI
        
        Args:
            data (Dict[str, Any]): Extracted data
            
        Returns:
            Dict[str, Any]: Formatted data suitable for GUI display
        """
        if data.get('error', False):
            return {
                'Error': data.get('error_message', 'Unknown error'),
                'Type': data.get('error_type', 'Unknown'),
                'Source': data.get('_metadata', {}).get('source_file', 'Unknown')
            }
        
        # Create a formatted view of the data
        formatted = {}
        
        # Basic information
        basic_info = {}
        if 'invoice_number' in data:
            basic_info['Invoice Number'] = data['invoice_number']
        if 'invoice_date' in data:
            basic_info['Invoice Date'] = data['invoice_date']
        if 'vendor_name' in data:
            basic_info['Vendor Name'] = data['vendor_name']
        if 'total_amount' in data:
            basic_info['Total Amount'] = data['total_amount']
        
        if basic_info:
            formatted['Basic Information'] = basic_info
        
        # Vendor information
        vendor_info = {}
        vendor_fields = ['vendor_address', 'vendor_gst', 'vendor_state', 'vendor_pincode', 
                        'vendor_contact', 'vendor_email']
        for field in vendor_fields:
            if field in data and data[field] is not None:
                display_name = field.replace('vendor_', '').replace('_', ' ').title()
                vendor_info[display_name] = data[field]
        
        if vendor_info:
            formatted['Vendor Information'] = vendor_info
        
        # Line items
        if 'line_items' in data and data['line_items']:
            formatted['Line Items'] = data['line_items']
        
        # Add all other fields
        other_fields = {}
        skip_fields = ['invoice_number', 'invoice_date', 'vendor_name', 'total_amount', 
                      'line_items', '_metadata', 'raw_text', 'error'] + vendor_fields
        
        for key, value in data.items():
            if key not in skip_fields and value is not None:
                display_name = key.replace('_', ' ').title()
                other_fields[display_name] = value
        
        if other_fields:
            formatted['Additional Information'] = other_fields
        
        return formatted
    
    def export_to_json(self, data: Dict[str, Any], file_path: str) -> bool:
        """
        Export extracted data to JSON file
        
        Args:
            data (Dict[str, Any]): Extracted data
            file_path (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a clean copy without GUI-specific fields
            export_data = data.copy()
            
            # Remove internal metadata for cleaner export
            if '_metadata' in export_data:
                del export_data['_metadata']
            if 'raw_text' in export_data:
                del export_data['raw_text']
            
            # Write to file with proper formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting JSON: {e}")
            return False
    
    def export_to_csv(self, data: Dict[str, Any], file_path: str) -> bool:
        """
        Export line items to CSV file
        
        Args:
            data (Dict[str, Any]): Extracted data
            file_path (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            line_items = data.get('line_items', [])
            
            if not line_items:
                # Create a CSV with basic invoice info if no line items
                basic_data = [
                    {
                        'invoice_number': data.get('invoice_number', ''),
                        'invoice_date': data.get('invoice_date', ''),
                        'vendor_name': data.get('vendor_name', ''),
                        'total_amount': data.get('total_amount', ''),
                        'note': 'No line items found'
                    }
                ]
                df = pd.DataFrame(basic_data)
            else:
                # Create DataFrame from line items
                df = pd.DataFrame(line_items)
            
            # Export to CSV
            df.to_csv(file_path, index=False, encoding='utf-8')
            return True
            
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False
    
    def get_extraction_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of the extraction results
        
        Args:
            data (Dict[str, Any]): Extracted data
            
        Returns:
            Dict[str, Any]: Summary information
        """
        if data.get('error', False):
            return {
                'status': 'error',
                'message': data.get('error_message', 'Unknown error'),
                'fields_extracted': 0,
                'line_items_count': 0
            }
        
        # Count extracted fields (non-empty, non-None values)
        fields_extracted = 0
        for key, value in data.items():
            if key not in ['_metadata', 'raw_text'] and value is not None and value != '':
                fields_extracted += 1
        
        line_items_count = len(data.get('line_items', []))
        
        validation = data.get('_metadata', {}).get('validation', {})
        missing_required = len(validation.get('missing_required_fields', []))
        
        return {
            'status': 'success' if validation.get('is_valid', False) else 'warning',
            'fields_extracted': fields_extracted,
            'line_items_count': line_items_count,
            'missing_required_fields': missing_required,
            'validation_warnings': len(validation.get('warnings', []))
        }


if __name__ == "__main__":
    # Test the extractor
    extractor = EnhancedInvoiceExtractor()
    
    # Test with a sample PDF (adjust path as needed)
    test_pdf = Path(__file__).parent.parent / "files" / "invoice-template-1_2.pdf"
    if test_pdf.exists():
        print(f"Testing extraction with: {test_pdf}")
        result = extractor.extract_data(str(test_pdf))
        print("Extraction result:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Test PDF not found: {test_pdf}")
