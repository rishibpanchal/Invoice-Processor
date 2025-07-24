"""
Enhanced Multi-Stage Invoice Extractor - Qt Integration
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

try:
    from extraction.multi_stage_extractor import MultiStageInvoiceExtractor
    from extraction.pdf_utils import pdf_to_markdown
except ImportError as e:
    raise ImportError(f"Cannot import multi-stage extraction modules: {e}")


class EnhancedMultiStageExtractor:
    """Enhanced multi-stage extractor with additional features for Qt integration"""
    
    def __init__(self):
        self.multi_stage_extractor = MultiStageInvoiceExtractor()
        self.current_extraction_data = None
        self.current_stage = None
        self.progress_callback = None
        
    def set_progress_callback(self, callback):
        """Set progress callback for updates"""
        self.progress_callback = callback
        
    def extract_data_with_stages(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract data using multi-stage approach with detailed progress tracking
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            Dict[str, Any]: Extracted invoice data with stage information
        """
        try:
            result = self.multi_stage_extractor.extract_data(pdf_path, self.progress_callback)
            
            # Add stage-specific metadata
            if '_metadata' in result:
                result['_metadata']['extraction_stages'] = {
                    'stage_1_invoice_identification': 'completed',
                    'stage_2_content_segmentation': 'completed',
                    'stage_3_skeleton_creation': 'completed',
                    'stage_4_basic_data_extraction': 'completed',
                    'stage_5_detailed_data_extraction': 'completed',
                    'stage_6_line_items_extraction': 'completed'
                }
            
            self.current_extraction_data = result
            return result
            
        except Exception as e:
            error_result = {
                'error': True,
                'error_message': str(e),
                'error_type': type(e).__name__,
                'raw_text': '',
                '_metadata': {
                    'source_file': pdf_path,
                    'extraction_method': 'enhanced_multi_stage_extractor',
                    'failed': True,
                    'extraction_stages': {
                        'stage_1_invoice_identification': 'failed',
                        'stage_2_content_segmentation': 'not_started',
                        'stage_3_skeleton_creation': 'not_started',
                        'stage_4_basic_data_extraction': 'not_started',
                        'stage_5_detailed_data_extraction': 'not_started',
                        'stage_6_line_items_extraction': 'not_started'
                    }
                }
            }
            self.current_extraction_data = error_result
            return error_result
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get a summary of the extraction process"""
        if not self.current_extraction_data:
            return {"status": "no_extraction_performed"}
        
        if self.current_extraction_data.get('error', False):
            return {
                "status": "error",
                "error_message": self.current_extraction_data.get('error_message', 'Unknown error'),
                "stages": self.current_extraction_data.get('_metadata', {}).get('extraction_stages', {})
            }
        
        metadata = self.current_extraction_data.get('_metadata', {})
        invoices = self.current_extraction_data.get('invoices', [])
        
        summary = {
            "status": "success",
            "invoice_count": len(invoices),
            "invoice_numbers": [inv.get('invoice_number') for inv in invoices if inv.get('invoice_number')],
            "extraction_method": metadata.get('extraction_method', 'unknown'),
            "stages_completed": metadata.get('extraction_stages', {}),
            "document_stats": {
                "document_length": metadata.get('document_length', 0),
                "source_file": metadata.get('source_file', '')
            }
        }
        
        # Add per-invoice statistics
        invoice_stats = []
        for invoice in invoices:
            stats = {
                "invoice_number": invoice.get('invoice_number'),
                "vendor_name": invoice.get('vendor_name'),
                "total_amount": invoice.get('total_amount'),
                "line_items_count": len(invoice.get('line_items', [])),
                "fields_populated": sum(1 for v in invoice.values() if v is not None and v != '' and v != [])
            }
            invoice_stats.append(stats)
        
        summary["invoice_statistics"] = invoice_stats
        return summary
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted data with multi-stage specific validation
        
        Args:
            data (Dict[str, Any]): Raw extracted data
            
        Returns:
            Dict[str, Any]: Validated data with validation results
        """
        if data.get('error', False):
            return data
        
        validation_results = {
            'is_valid': True,
            'overall_score': 0,
            'invoices_validation': [],
            'warnings': [],
            'critical_issues': []
        }
        
        invoices = data.get('invoices', [])
        
        if not invoices:
            validation_results['is_valid'] = False
            validation_results['critical_issues'].append("No invoices found in extracted data")
            data['_validation'] = validation_results
            return data
        
        required_fields = ['invoice_number', 'invoice_date', 'vendor_name', 'total_amount']
        important_fields = ['vendor_address', 'buyer_name', 'line_items']
        
        total_score = 0
        max_possible_score = 0
        
        for i, invoice in enumerate(invoices):
            invoice_validation = {
                'invoice_index': i,
                'invoice_number': invoice.get('invoice_number', f'Invoice_{i}'),
                'missing_required_fields': [],
                'missing_important_fields': [],
                'populated_fields_count': 0,
                'total_fields_count': 0,
                'completeness_percentage': 0,
                'validation_score': 0
            }
            
            # Check required fields
            for field in required_fields:
                if field not in invoice or invoice[field] is None or invoice[field] == '':
                    invoice_validation['missing_required_fields'].append(field)
                    validation_results['is_valid'] = False
                else:
                    invoice_validation['validation_score'] += 25  # 25 points per required field
            
            # Check important fields
            for field in important_fields:
                if field not in invoice or invoice[field] is None or invoice[field] == '' or invoice[field] == []:
                    invoice_validation['missing_important_fields'].append(field)
                else:
                    invoice_validation['validation_score'] += 10  # 10 points per important field
            
            # Calculate completeness
            populated_count = 0
            total_count = 0
            
            for key, value in invoice.items():
                if not key.startswith('_'):  # Skip metadata fields
                    total_count += 1
                    if value is not None and value != '' and value != []:
                        populated_count += 1
            
            invoice_validation['populated_fields_count'] = populated_count
            invoice_validation['total_fields_count'] = total_count
            invoice_validation['completeness_percentage'] = (populated_count / total_count * 100) if total_count > 0 else 0
            
            # Add line items validation
            line_items = invoice.get('line_items', [])
            if line_items:
                invoice_validation['line_items_count'] = len(line_items)
                invoice_validation['validation_score'] += min(len(line_items) * 5, 50)  # Max 50 points for line items
            else:
                validation_results['warnings'].append(f"No line items found for {invoice_validation['invoice_number']}")
            
            # Normalize validation score (max 130 points)
            invoice_validation['validation_score'] = min(invoice_validation['validation_score'], 130)
            
            total_score += invoice_validation['validation_score']
            max_possible_score += 130
            
            validation_results['invoices_validation'].append(invoice_validation)
        
        # Calculate overall score
        validation_results['overall_score'] = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        # Add overall assessment
        if validation_results['overall_score'] >= 80:
            validation_results['quality_assessment'] = 'excellent'
        elif validation_results['overall_score'] >= 60:
            validation_results['quality_assessment'] = 'good'
        elif validation_results['overall_score'] >= 40:
            validation_results['quality_assessment'] = 'fair'
        else:
            validation_results['quality_assessment'] = 'poor'
        
        data['_validation'] = validation_results
        return data
    
    def export_to_csv(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export extracted data to CSV format
        
        Args:
            data (Dict[str, Any]): Extracted invoice data
            output_path (str): Path for the output CSV file
            
        Returns:
            bool: Success status
        """
        try:
            if data.get('error', False):
                raise ValueError("Cannot export error data to CSV")
            
            invoices = data.get('invoices', [])
            if not invoices:
                raise ValueError("No invoices to export")
            
            # Flatten invoice data for CSV
            csv_data = []
            
            for invoice in invoices:
                # Basic invoice data
                row = {
                    'invoice_number': invoice.get('invoice_number', ''),
                    'invoice_date': invoice.get('invoice_date', ''),
                    'vendor_name': invoice.get('vendor_name', ''),
                    'vendor_address': invoice.get('vendor_address', ''),
                    'vendor_gst': invoice.get('vendor_gst', ''),
                    'buyer_name': invoice.get('buyer_name', ''),
                    'buyer_address': invoice.get('buyer_address', ''),
                    'buyer_gst': invoice.get('buyer_gst', ''),
                    'total_amount': invoice.get('total_amount', ''),
                    'currency': invoice.get('currency', ''),
                    'due_date': invoice.get('due_date', ''),
                    'line_items_count': len(invoice.get('line_items', []))
                }
                
                # Add line items as separate rows or concatenate
                line_items = invoice.get('line_items', [])
                if line_items:
                    for i, item in enumerate(line_items):
                        item_row = row.copy()
                        item_row.update({
                            'line_item_index': i + 1,
                            'item_description': item.get('item_description', ''),
                            'quantity': item.get('quantity', ''),
                            'unit_of_measurement': item.get('unit_of_measurement', ''),
                            'total_item_value': item.get('total_item_value', ''),
                            'hsn_sac_code': item.get('hsn_sac_code', ''),
                            'taxable_value': item.get('taxable_value', ''),
                            'cgst_rate': item.get('cgst_rate', ''),
                            'cgst_amount': item.get('cgst_amount', ''),
                            'sgst_rate': item.get('sgst_rate', ''),
                            'sgst_amount': item.get('sgst_amount', ''),
                            'igst_rate': item.get('igst_rate', ''),
                            'igst_amount': item.get('igst_amount', ''),
                        })
                        csv_data.append(item_row)
                else:
                    # Add invoice without line items
                    row.update({
                        'line_item_index': '',
                        'item_description': '',
                        'quantity': '',
                        'unit_of_measurement': '',
                        'total_item_value': '',
                        'hsn_sac_code': '',
                        'taxable_value': '',
                        'cgst_rate': '',
                        'cgst_amount': '',
                        'sgst_rate': '',
                        'sgst_amount': '',
                        'igst_rate': '',
                        'igst_amount': '',
                    })
                    csv_data.append(row)
            
            # Write to CSV
            if csv_data:
                df = pd.DataFrame(csv_data)
                df.to_csv(output_path, index=False)
                return True
            else:
                raise ValueError("No data to export")
                
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def export_detailed_json(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export detailed JSON with validation and metadata
        
        Args:
            data (Dict[str, Any]): Extracted invoice data
            output_path (str): Path for the output JSON file
            
        Returns:
            bool: Success status
        """
        try:
            # Add timestamp and additional metadata
            enhanced_data = data.copy()
            
            if '_metadata' not in enhanced_data:
                enhanced_data['_metadata'] = {}
            
            enhanced_data['_metadata']['export_timestamp'] = pd.Timestamp.now().isoformat()
            enhanced_data['_metadata']['export_format'] = 'detailed_json'
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
