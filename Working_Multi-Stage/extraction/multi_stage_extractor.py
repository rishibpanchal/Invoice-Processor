"""
Multi-Stage Invoice Extractor - Simplified version
"""
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from .pdf_utils import pdf_to_markdown
from .ollama import generate_ollama_response


class MultiStageInvoiceExtractor:
    """
    A simplified multi-stage extractor that processes invoices in steps:
    1. Identify invoice numbers
    2. Extract basic data for each invoice
    3. Fill detailed data progressively
    """
    
    def __init__(self):
        self.prompts = self.load_prompts()
        
    def load_prompts(self) -> Dict[str, str]:
        """Load all prompt templates"""
        return {
            "identify_invoices": """
You are an expert document analyzer. Find all unique invoice numbers in this document.

Look for patterns like:
- Invoice No: ABC123
- Invoice Number: INV-001
- Bill No: 12345
- Invoice #: XYZ789

Document text:
{document_text}

Return ONLY a JSON array like: ["INV001", "INV002", "INV003"]
If no invoice numbers found, return: []
""",
            
            "extract_basic_data": """
You are an expert invoice data extractor. Extract data for invoice {invoice_number} only.

Invoice content:
{invoice_content}

Extract these fields for invoice {invoice_number}:
- invoice_number
- invoice_date
- vendor_name
- total_amount
- vendor_address
- buyer_name

Return JSON format:
{{
    "invoice_number": "{invoice_number}",
    "invoice_date": "YYYY-MM-DD or null",
    "vendor_name": "vendor name or null",
    "total_amount": "number or null", 
    "vendor_address": "address or null",
    "buyer_name": "buyer name or null"
}}

ONLY extract data clearly visible for invoice {invoice_number}. Use null for missing fields.
""",
            
            "extract_detailed_data": """
You are an expert invoice data extractor. Extract detailed data for invoice {invoice_number}.

Current data:
{current_data}

Invoice content:
{invoice_content}

Add these additional fields:
- vendor_gst, vendor_contact, vendor_email
- buyer_address, buyer_gst, buyer_contact, buyer_email
- due_date, currency, payment_terms
- place_of_supply, total_invoice_value

Return the complete updated JSON with all fields (keep existing + add new ones).
Use null for fields not found.
""",
            
            "extract_line_items": """
You are an expert at extracting line items from invoice {invoice_number}.

Current data:
{current_data}

Invoice content:
{invoice_content}

Extract all line items for invoice {invoice_number} and add them to the "line_items" array.

Each line item should have:
- item_description
- quantity
- total_item_value
- hsn_sac_code (if available)
- taxable_value (if available)
- cgst_amount, sgst_amount, igst_amount (if available)

Return the complete updated JSON with the line_items array filled.
"""
        }
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama model"""
        try:
            return generate_ollama_response(prompt)
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
    
    def extract_json_from_response(self, response: str) -> Any:
        """Extract JSON from the response"""
        response = response.strip()
        
        # Remove markdown formatting
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        
        # Find JSON content
        json_pattern = r'\{.*\}|\[.*\]'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if match:
            json_str = match.group(0)
        else:
            raise ValueError("No valid JSON found in response")
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    
    def find_invoice_numbers(self, document_text: str) -> List[str]:
        """Find all invoice numbers in the document"""
        try:
            prompt = self.prompts["identify_invoices"].format(document_text=document_text)
            response = self.generate_response(prompt)
            
            invoice_numbers = self.extract_json_from_response(response)
            if isinstance(invoice_numbers, list):
                return invoice_numbers
            else:
                return []
        except Exception as e:
            print(f"Error finding invoice numbers: {e}")
            # Fallback: try regex patterns
            patterns = [
                r'Invoice\s*(?:No|Number|#)[\s:]*([A-Z0-9-/]+)',
                r'Bill\s*(?:No|Number|#)[\s:]*([A-Z0-9-/]+)',
                r'INV[\s#]*([A-Z0-9-/]+)',
            ]
            
            invoice_numbers = set()
            for pattern in patterns:
                matches = re.findall(pattern, document_text, re.IGNORECASE)
                invoice_numbers.update(matches)
            
            return list(invoice_numbers)
    
    def extract_basic_data(self, document_text: str, invoice_number: str) -> Dict[str, Any]:
        """Extract basic invoice data"""
        try:
            prompt = self.prompts["extract_basic_data"].format(
                invoice_number=invoice_number,
                invoice_content=document_text
            )
            response = self.generate_response(prompt)
            return self.extract_json_from_response(response)
        except Exception as e:
            print(f"Error extracting basic data for {invoice_number}: {e}")
            return {
                "invoice_number": invoice_number,
                "invoice_date": None,
                "vendor_name": None,
                "total_amount": None,
                "vendor_address": None,
                "buyer_name": None
            }
    
    def extract_detailed_data(self, document_text: str, invoice_number: str, current_data: Dict) -> Dict[str, Any]:
        """Extract detailed invoice data"""
        try:
            prompt = self.prompts["extract_detailed_data"].format(
                invoice_number=invoice_number,
                current_data=json.dumps(current_data, indent=2),
                invoice_content=document_text
            )
            response = self.generate_response(prompt)
            return self.extract_json_from_response(response)
        except Exception as e:
            print(f"Error extracting detailed data for {invoice_number}: {e}")
            return current_data
    
    def extract_line_items(self, document_text: str, invoice_number: str, current_data: Dict) -> Dict[str, Any]:
        """Extract line items"""
        try:
            prompt = self.prompts["extract_line_items"].format(
                invoice_number=invoice_number,
                current_data=json.dumps(current_data, indent=2),
                invoice_content=document_text
            )
            response = self.generate_response(prompt)
            result = self.extract_json_from_response(response)
            
            # Ensure line_items is an array
            if "line_items" not in result:
                result["line_items"] = []
            
            return result
        except Exception as e:
            print(f"Error extracting line items for {invoice_number}: {e}")
            current_data["line_items"] = []
            return current_data
    
    def extract_data(self, pdf_path: str, progress_callback=None) -> Dict[str, Any]:
        """
        Main extraction method using simplified multi-stage approach
        """
        try:
            if progress_callback:
                progress_callback("Converting PDF to text...")
            
            # Convert PDF to text
            document_text = pdf_to_markdown(pdf_path)
            
            if not document_text.strip():
                raise ValueError("No text content extracted from PDF")
            
            if progress_callback:
                progress_callback("Step 1: Finding invoice numbers...")
            
            # Step 1: Find invoice numbers
            invoice_numbers = self.find_invoice_numbers(document_text)
            
            if not invoice_numbers:
                # Try to process as single invoice
                invoice_numbers = ["UNKNOWN"]
            
            if progress_callback:
                progress_callback(f"Found {len(invoice_numbers)} invoice(s): {', '.join(invoice_numbers)}")
            
            # Process each invoice
            invoices = []
            
            for i, invoice_number in enumerate(invoice_numbers):
                if progress_callback:
                    progress_callback(f"Processing invoice {i+1}/{len(invoice_numbers)}: {invoice_number}")
                
                # Step 2: Extract basic data
                if progress_callback:
                    progress_callback(f"  - Extracting basic data for {invoice_number}")
                basic_data = self.extract_basic_data(document_text, invoice_number)
                
                # Step 3: Extract detailed data
                if progress_callback:
                    progress_callback(f"  - Extracting detailed data for {invoice_number}")
                detailed_data = self.extract_detailed_data(document_text, invoice_number, basic_data)
                
                # Step 4: Extract line items
                if progress_callback:
                    progress_callback(f"  - Extracting line items for {invoice_number}")
                final_data = self.extract_line_items(document_text, invoice_number, detailed_data)
                
                invoices.append(final_data)
            
            # Create result
            result = {
                "invoices": invoices,
                "_metadata": {
                    "source_file": pdf_path,
                    "extraction_method": "multi_stage_extractor",
                    "invoice_count": len(invoices),
                    "invoice_numbers": invoice_numbers,
                    "document_length": len(document_text)
                },
                "raw_text": document_text
            }
            
            if progress_callback:
                progress_callback("Multi-stage extraction completed!")
            
            return result
            
        except Exception as e:
            return {
                'error': True,
                'error_message': str(e),
                'error_type': type(e).__name__,
                'raw_text': document_text if 'document_text' in locals() else '',
                '_metadata': {
                    'source_file': pdf_path,
                    'extraction_method': 'multi_stage_extractor',
                    'failed': True
                }
            }
    
    def identify_invoice_numbers(self, document_text: str) -> List[str]:
        """Identify all invoice numbers in the document using AI model"""
        prompt = self.prompts["identify_invoices"].format(document_text=document_text)
        response = self.generate_response(prompt)
        
        try:
            invoice_numbers = self.extract_json_from_response(response)
            if not isinstance(invoice_numbers, list):
                raise ValueError("Expected list of invoice numbers")
            return invoice_numbers
        except Exception as e:
            print(f"Error identifying invoice numbers: {e}")
            # Fallback: try to find invoice numbers manually
            return self.find_invoice_numbers_with_regex(document_text)
    
    def find_invoice_numbers_with_regex(self, text: str) -> List[str]:
        """Find invoice numbers using regex patterns as fallback method"""
        patterns = [
            r'Invoice\s*(?:No|Number|#)[\s:]*([A-Z0-9-/]+)',
            r'Bill\s*(?:No|Number|#)[\s:]*([A-Z0-9-/]+)',
            r'INV[\s#]*([A-Z0-9-/]+)',
        ]
        
        invoice_numbers = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            invoice_numbers.update(matches)
        
        return list(invoice_numbers)
    
    def get_invoice_specific_content(self, document_text: str, invoice_number: str) -> str:
        """Get content relevant to a specific invoice number
        
        Note: For simplified approach, we use the full document text
        but focus the AI on the specific invoice number
        """
        return document_text
    
    def create_invoice_data_structure(self, invoice_numbers: List[str]) -> Dict[str, Any]:
        """Create initial data structure for all invoices with empty fields"""
        invoice_template = {
            "invoice_number": None,
            "invoice_date": None,
            "vendor_name": None,
            "vendor_address": None,
            "vendor_gst": None,
            "vendor_state": None,
            "vendor_pincode": None,
            "vendor_contact": None,
            "vendor_email": None,
            "total_amount": None,
            "due_date": None,
            "currency": None,
            "consignee_name": None,
            "consignee_address": None,
            "consignee_gst": None,
            "consignee_state": None,
            "consignee_pincode": None,
            "consignee_contact": None,
            "consignee_email": None,
            "buyer_name": None,
            "buyer_address": None,
            "buyer_gst": None,
            "buyer_state": None,
            "buyer_pincode": None,
            "buyer_contact": None,
            "buyer_email": None,
            "place_of_supply": None,
            "discount": None,
            "total_invoice_value": None,
            "reverse_charge_applicable": None,
            "supplier_signature": None,
            "buyer_pan": None,
            "shipping_address": None,
            "billing_address": None,
            "terms_of_supply": None,
            "payment_terms": None,
            "bank_account_details": None,
            "eway_bill_number": None,
            "vehicle_number": None,
            "invoice_reference_number": None,
            "remarks": None,
            "line_items": []
        }
        
        invoices = []
        for invoice_num in invoice_numbers:
            invoice = invoice_template.copy()
            invoice["invoice_number"] = invoice_num
            invoices.append(invoice)
        
        return {"invoices": invoices}
    
    def extract_basic_invoice_data(self, document_text: str, invoice_number: str, 
                             current_structure: Dict) -> Dict[str, Any]:
        """Extract basic invoice data for a specific invoice"""
        invoice_content = self.get_invoice_specific_content(document_text, invoice_number)
        
        prompt = self.prompts["extract_basic_data"].format(
            invoice_number=invoice_number,
            invoice_content=invoice_content
        )
        response = self.generate_response(prompt)
        
        try:
            extracted_data = self.extract_json_from_response(response)
            # Update the specific invoice in current_structure
            for invoice in current_structure['invoices']:
                if invoice['invoice_number'] == invoice_number:
                    invoice.update(extracted_data)
                    break
            return current_structure
        except Exception as e:
            print(f"Error extracting basic data for {invoice_number}: {e}")
            return current_structure
    
    def extract_detailed_invoice_data(self, document_text: str, invoice_number: str, 
                                current_structure: Dict) -> Dict[str, Any]:
        """Extract detailed invoice data for a specific invoice"""
        invoice_content = self.get_invoice_specific_content(document_text, invoice_number)
        
        # Get current invoice data to pass to the prompt
        current_invoice = None
        for invoice in current_structure['invoices']:
            if invoice['invoice_number'] == invoice_number:
                current_invoice = invoice
                break
        
        prompt = self.prompts["extract_detailed_data"].format(
            invoice_number=invoice_number,
            invoice_content=invoice_content,
            current_data=json.dumps(current_invoice, indent=2)
        )
        response = self.generate_response(prompt)
        
        try:
            extracted_data = self.extract_json_from_response(response)
            # Update the specific invoice in current_structure
            for invoice in current_structure['invoices']:
                if invoice['invoice_number'] == invoice_number:
                    invoice.update(extracted_data)
                    break
            return current_structure
        except Exception as e:
            print(f"Error extracting detailed data for {invoice_number}: {e}")
            return current_structure
    
    def extract_invoice_line_items(self, document_text: str, invoice_number: str, 
                                current_structure: Dict) -> Dict[str, Any]:
        """Extract line items for a specific invoice"""
        invoice_content = self.get_invoice_specific_content(document_text, invoice_number)
        
        # Get current invoice data to pass to the prompt
        current_invoice = None
        for invoice in current_structure['invoices']:
            if invoice['invoice_number'] == invoice_number:
                current_invoice = invoice
                break
        
        prompt = self.prompts["extract_line_items"].format(
            invoice_number=invoice_number,
            invoice_content=invoice_content,
            current_data=json.dumps(current_invoice, indent=2)
        )
        response = self.generate_response(prompt)
        
        try:
            extracted_data = self.extract_json_from_response(response)
            # Update the specific invoice in current_structure
            for invoice in current_structure['invoices']:
                if invoice['invoice_number'] == invoice_number:
                    invoice.update(extracted_data)
                    break
            return current_structure
        except Exception as e:
            print(f"Error extracting line items for {invoice_number}: {e}")
            return current_structure
    
    def extract_data(self, pdf_path: str, progress_callback=None) -> Dict[str, Any]:
        """
        Main extraction method using multi-stage approach
        
        Args:
            pdf_path (str): Path to the PDF file
            progress_callback (callable): Optional callback for progress updates
            
        Returns:
            Dict[str, Any]: Extracted invoice data
        """
        try:
            if progress_callback:
                progress_callback("Converting PDF to text...")
            
            # Convert PDF to markdown
            document_text = pdf_to_markdown(pdf_path)
            
            if not document_text.strip():
                raise ValueError("No text content extracted from PDF")
            
            if progress_callback:
                progress_callback("Step 1: Identifying invoice numbers...")
            
            # Step 1: Identify invoice numbers
            invoice_numbers = self.identify_invoice_numbers(document_text)
            
            if not invoice_numbers:
                raise ValueError("No invoice numbers found in the document")
            
            if progress_callback:
                progress_callback(f"Found {len(invoice_numbers)} invoice(s): {', '.join(invoice_numbers)}")
                progress_callback("Step 2: Preparing data structure...")
            
            # Step 2: Create skeleton (simplified - no segmentation needed)
            result = self.create_invoice_data_structure(invoice_numbers)
            
            # Steps 3-5: Process each invoice
            for i, invoice_number in enumerate(invoice_numbers):
                if progress_callback:
                    progress_callback(f"Processing invoice {i+1}/{len(invoice_numbers)}: {invoice_number}")
                
                # Step 3: Fill basic data
                if progress_callback:
                    progress_callback(f"  - Extracting basic data for {invoice_number}")
                result = self.extract_basic_invoice_data(document_text, invoice_number, result)
                
                # Step 4: Fill detailed data
                if progress_callback:
                    progress_callback(f"  - Extracting detailed data for {invoice_number}")
                result = self.extract_detailed_invoice_data(document_text, invoice_number, result)
                
                # Step 5: Extract line items
                if progress_callback:
                    progress_callback(f"  - Extracting line items for {invoice_number}")
                result = self.extract_invoice_line_items(document_text, invoice_number, result)
            
            # Add metadata
            result['_metadata'] = {
                'source_file': pdf_path,
                'extraction_method': 'multi_stage_extractor',
                'invoice_count': len(invoice_numbers),
                'invoice_numbers': invoice_numbers,
                'document_length': len(document_text)
            }
            
            result['raw_text'] = document_text
            
            if progress_callback:
                progress_callback("Extraction complete!")
            
            return result
            
        except Exception as e:
            return {
                'error': True,
                'error_message': str(e),
                'error_type': type(e).__name__,
                'raw_text': document_text if 'document_text' in locals() else '',
                '_metadata': {
                    'source_file': pdf_path,
                    'extraction_method': 'multi_stage_extractor',
                    'failed': True
                }
            }
