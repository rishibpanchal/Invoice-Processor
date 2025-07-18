
import sys
import os
import argparse
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("pdfplumber is required. Please install it with 'pip install pdfplumber'.")
    sys.exit(1)

def pdf_to_markdown(pdf_path):
    """
    Extracts text from a PDF and formats it as Markdown using pdfplumber.
    """
    md = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                md.append(f"## Page {i}\n\n{text.strip()}\n")
    return '\n'.join(md)

def main():
    parser = argparse.ArgumentParser(description="Convert PDF to Markdown.")
    parser.add_argument('pdf_path', type=str, help='Path to the PDF file')
    parser.add_argument('-o', '--output', type=str, help='Output Markdown file (optional)')
    args = parser.parse_args()

    pdf_path = args.pdf_path
    if not os.path.isfile(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    md_content = pdf_to_markdown(pdf_path)

    if args.output:
        output_path = args.output
    else:
        output_path = str(Path(pdf_path).with_suffix('.md'))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Markdown saved to {output_path}")

if __name__ == "__main__":
    main()
