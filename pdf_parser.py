import PyPDF2
import sys
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    """
    Extract all text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_file.suffix.lower() == '.pdf':
        raise ValueError(f"File must be a PDF: {pdf_path}")
    
    text_content = []
    
    try:
        with open(pdf_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"Extracting text from {num_pages} pages...", file=sys.stderr)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)
            
            full_text = "\n\n".join(text_content)
            print(f"Extracted {len(full_text)} characters from PDF", file=sys.stderr)
            
            return full_text
            
    except Exception as e:
        raise RuntimeError(f"Error reading PDF: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_parser.py <path_to_pdf>", file=sys.stderr)
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    text = extract_text_from_pdf(pdf_path)
    print(text)
