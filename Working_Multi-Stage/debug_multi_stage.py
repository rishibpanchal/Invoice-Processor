#!/usr/bin/env python3
"""
Debug test for multi-stage extraction issue
"""
import sys
import os
from pathlib import Path

# Add the extraction directory to the path
sys.path.append(str(Path(__file__).parent / 'extraction'))
sys.path.append(str(Path(__file__).parent / 'qt viewer'))

def run_extraction_debug_test():
    """Run comprehensive debug test for multi-stage extraction system"""
    print("🔍 DEBUG: Testing Multi-Stage Extraction")
    print("=" * 60)
    
    try:
        # Test 1: Import the simplified extractor directly
        print("1. Testing direct import of MultiStageInvoiceExtractor...")
        from extraction.multi_stage_extractor import MultiStageInvoiceExtractor
        extractor = MultiStageInvoiceExtractor()
        print("✅ Direct import successful")
        
        # Test 2: Import the enhanced wrapper
        print("\n2. Testing import of EnhancedMultiStageExtractor...")
        from enhanced_multi_stage_extractor import EnhancedMultiStageExtractor
        enhanced_extractor = EnhancedMultiStageExtractor()
        print("✅ Enhanced import successful")
        
        # Test 3: Test with sample file
        test_files = [
            "files/invoice-template-1_2.pdf",
            "files/S23 & Charger.pdf"
        ]
        
        for pdf_file in test_files:
            if not os.path.exists(pdf_file):
                print(f"⚠️  Test file not found: {pdf_file}")
                continue
                
            print(f"\n3. Testing extraction with: {pdf_file}")
            print("-" * 40)
            
            def progress_callback(message):
                print(f"  📊 Progress: {message}")
            
            try:
                # Test with enhanced extractor (what the GUI uses)
                enhanced_extractor.set_progress_callback(progress_callback)
                result = enhanced_extractor.extract_data_with_stages(pdf_file)
                
                print(f"\n📋 EXTRACTION RESULTS:")
                print(f"   Error: {result.get('error', False)}")
                
                if result.get('error', False):
                    print(f"   Error Message: {result.get('error_message', 'N/A')}")
                    print(f"   Error Type: {result.get('error_type', 'N/A')}")
                else:
                    invoices = result.get('invoices', [])
                    print(f"   Invoices Found: {len(invoices)}")
                    
                    for i, invoice in enumerate(invoices, 1):
                        print(f"\n   🧾 Invoice {i}:")
                        print(f"      Number: {invoice.get('invoice_number', 'N/A')}")
                        print(f"      Date: {invoice.get('invoice_date', 'N/A')}")
                        print(f"      Vendor: {invoice.get('vendor_name', 'N/A')}")
                        print(f"      Total: {invoice.get('total_amount', 'N/A')}")
                        
                        line_items = invoice.get('line_items', [])
                        print(f"      Line Items: {len(line_items)} items")
                        
                        if line_items:
                            print(f"      First Item: {line_items[0].get('item_description', 'N/A')}")
                
                # Test metadata
                metadata = result.get('_metadata', {})
                print(f"\n📈 Metadata:")
                print(f"   Method: {metadata.get('extraction_method', 'N/A')}")
                print(f"   Invoice Count: {metadata.get('invoice_count', 'N/A')}")
                print(f"   Document Length: {metadata.get('document_length', 'N/A')} chars")
                
                extraction_stages = metadata.get('extraction_stages', {})
                if extraction_stages:
                    print(f"   Stages: {extraction_stages}")
                
                break  # Test only first available file
                
            except Exception as e:
                print(f"❌ Extraction failed: {str(e)}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Import or setup failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_extraction_debug_test()
