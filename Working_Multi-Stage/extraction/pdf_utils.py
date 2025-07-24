"""
PDF Utility Functions for Multi-Stage Extraction
Simplified PDF processing functions for the multi-stage invoice processor
"""
import re
import pdfplumber
from pathlib import Path
from typing import Optional, Dict, Any


def pdf_to_markdown(pdf_path: str) -> str:
    """
    Extract text from PDF and format as markdown
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text formatted as markdown
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text from the page
                text = page.extract_text()
                
                if text:
                    # Add page header
                    text_parts.append(f"# Page {page_num}\n")
                    
                    # Clean and format text
                    text = text.replace('\x00', '')  # Remove null characters
                    text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize line breaks
                    
                    text_parts.append(text)
                    text_parts.append("\n\n---\n\n")  # Page separator
            
            if not text_parts:
                return "No readable text found in PDF"
            
            # Join all parts
            markdown_text = "".join(text_parts)
            
            # Final cleanup
            markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)  # Remove excessive line breaks
            
            return markdown_text.strip()
            
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"


def extract_text_simple(pdf_path: str) -> str:
    """
    Simple text extraction from PDF
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted plain text
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n\n".join(text_parts)
            
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def get_pdf_info(pdf_path: str) -> Dict[str, Any]:
    """
    Get basic information about the PDF
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with PDF information
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return {
                'page_count': len(pdf.pages),
                'metadata': pdf.metadata or {},
                'file_size': Path(pdf_path).stat().st_size if Path(pdf_path).exists() else 0
            }
    except Exception as e:
        return {
            'page_count': 0,
            'metadata': {},
            'file_size': 0,
            'error': str(e)
        }
