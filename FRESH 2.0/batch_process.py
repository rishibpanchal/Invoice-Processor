"""
Batch Invoice Processing Script
Process multiple PDF invoices and export results
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

# Add qt viewer to path for imports
sys.path.append(str(Path(__file__).parent / "qt viewer"))

try:
    from enhanced_extractor import EnhancedInvoiceExtractor
except ImportError as e:
    print(f"❌ Error importing enhanced_extractor: {e}")
    print("Make sure all dependencies are installed and Ollama is running")
    sys.exit(1)


def process_single_invoice(extractor: EnhancedInvoiceExtractor, pdf_path: Path) -> Dict[str, Any]:
    """Process a single invoice and return results"""
    print(f"📄 Processing: {pdf_path.name}")
    
    try:
        result = extractor.extract_data(str(pdf_path))
        
        if result.get('error', False):
            print(f"   ❌ Error: {result.get('error_message', 'Unknown error')}")
            return result
        
        # Get summary
        summary = extractor.get_extraction_summary(result)
        print(f"   ✅ Success: {summary['fields_extracted']} fields, {summary['line_items_count']} line items")
        
        if summary['missing_required_fields'] > 0:
            print(f"   ⚠️ Warning: {summary['missing_required_fields']} required fields missing")
        
        return result
        
    except Exception as e:
        error_result = {
            'error': True,
            'error_message': str(e),
            'error_type': type(e).__name__,
            'source_file': str(pdf_path)
        }
        print(f"   ❌ Exception: {e}")
        return error_result


def batch_process_invoices(input_dir: str, output_dir: str = None) -> List[Dict[str, Any]]:
    """Process all PDF files in the input directory"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return []
    
    # Find all PDF files
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in: {input_dir}")
        return []
    
    print(f"🔍 Found {len(pdf_files)} PDF files")
    
    # Set up output directory
    if output_dir is None:
        output_dir = input_path / "extracted_data"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Initialize extractor
    try:
        extractor = EnhancedInvoiceExtractor()
        print("✅ Enhanced extractor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize extractor: {e}")
        return []
    
    # Process each file
    results = []
    successful = 0
    failed = 0
    
    print("\n" + "="*60)
    print("PROCESSING INVOICES")
    print("="*60)
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] {pdf_file.name}")
        
        result = process_single_invoice(extractor, pdf_file)
        results.append(result)
        
        # Save individual result
        output_file = output_dir / f"{pdf_file.stem}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"   💾 Saved: {output_file.name}")
        except Exception as e:
            print(f"   ❌ Failed to save: {e}")
        
        # Update counters
        if result.get('error', False):
            failed += 1
        else:
            successful += 1
    
    # Save summary
    summary_data = {
        'processing_summary': {
            'total_files': len(pdf_files),
            'successful': successful,
            'failed': failed,
            'success_rate': f"{(successful/len(pdf_files)*100):.1f}%"
        },
        'files_processed': [
            {
                'filename': Path(result.get('_metadata', {}).get('source_file', 'unknown')).name,
                'status': 'error' if result.get('error', False) else 'success',
                'fields_extracted': 0 if result.get('error', False) else 
                    len([k for k, v in result.items() if k not in ['_metadata', 'raw_text', 'error'] and v is not None]),
                'line_items': len(result.get('line_items', [])),
                'error_message': result.get('error_message') if result.get('error', False) else None
            }
            for result in results
        ]
    }
    
    summary_file = output_dir / "processing_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    # Create consolidated CSV with all line items
    create_consolidated_csv(results, output_dir / "all_line_items.csv")
    
    # Print final summary
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(successful/len(pdf_files)*100):.1f}%")
    print(f"📁 Results saved to: {output_dir}")
    print(f"📋 Summary: {summary_file.name}")
    
    return results


def create_consolidated_csv(results: List[Dict[str, Any]], output_file: Path):
    """Create a consolidated CSV file with all line items"""
    try:
        all_line_items = []
        
        for result in results:
            if result.get('error', False):
                continue
                
            source_file = Path(result.get('_metadata', {}).get('source_file', 'unknown')).name
            invoice_number = result.get('invoice_number', 'N/A')
            vendor_name = result.get('vendor_name', 'N/A')
            invoice_date = result.get('invoice_date', 'N/A')
            
            line_items = result.get('line_items', [])
            
            if not line_items:
                # Add a row even if no line items
                all_line_items.append({
                    'source_file': source_file,
                    'invoice_number': invoice_number,
                    'vendor_name': vendor_name,
                    'invoice_date': invoice_date,
                    'item_description': 'No line items found',
                    'quantity': '',
                    'unit_price': '',
                    'total_amount': result.get('total_amount', '')
                })
            else:
                for item in line_items:
                    row = {
                        'source_file': source_file,
                        'invoice_number': invoice_number,
                        'vendor_name': vendor_name,
                        'invoice_date': invoice_date,
                    }
                    row.update(item)
                    all_line_items.append(row)
        
        if all_line_items:
            # Get all unique field names
            fieldnames = set()
            for item in all_line_items:
                fieldnames.update(item.keys())
            fieldnames = sorted(fieldnames)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_line_items)
            
            print(f"📊 Consolidated CSV created: {output_file.name} ({len(all_line_items)} rows)")
        else:
            print("⚠️ No line items to export to CSV")
            
    except Exception as e:
        print(f"❌ Failed to create consolidated CSV: {e}")


def main():
    """Main function for batch processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch process invoice PDFs")
    parser.add_argument("input_dir", nargs='?', help="Directory containing PDF invoices")
    parser.add_argument("-o", "--output", help="Output directory for results")
    parser.add_argument("--test", action="store_true", help="Test with sample files")
    
    args = parser.parse_args()
    
    if args.test:
        # Test with sample files
        sample_dir = Path(__file__).parent / "files"
        if sample_dir.exists():
            print("🧪 Testing with sample files...")
            batch_process_invoices(str(sample_dir), args.output)
        else:
            print("❌ No sample files directory found")
    elif args.input_dir:
        # Process specified directory
        batch_process_invoices(args.input_dir, args.output)
    else:
        print("❌ Please specify input directory or use --test flag")
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
