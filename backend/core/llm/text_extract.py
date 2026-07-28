import os
import pdfplumber
import docx

class TextExtractor:
    """
    A utility class for extracting text from PDF, Word, and text files.
    Usage:
        extracted_text = TextExtractor.extract(file_path, file_type)
    """

    @staticmethod
    def extract(file_path: str, file_type: str) -> str:
        """
        Dispatch method to pick the correct extraction logic based on file type.
        file_type can be 'pdf', 'docx', 'txt', etc.
        """
        file_type = file_type.lower()

        if file_type == 'pdf':
            return TextExtractor._extract_from_pdf(file_path)
        elif file_type in ['doc', 'docx']:
            return TextExtractor._extract_from_docx(file_path)
        elif file_type == 'txt':
            return TextExtractor._extract_from_txt(file_path)
        else:
            return ""

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """
        Extracts text from a PDF file using PyPDF2.
        """
        text_content = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text_content.append(page.extract_text() or "")
            return "\n".join(text_content).strip()
        except Exception as e:
            # Log or handle the error as needed
            print(f"Error extracting PDF text: {e}")
        return "\n".join(text_content)

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        """
        Extracts text from a Word (docx) file using python-docx.
        """
        text_content = []
        try:
            doc = docx.Document(file_path)
            text_content = [para.text for para in doc.paragraphs]
        except Exception as e:
            # Log or handle the error as needed
            print(f"Error extracting DOCX text: {e}")
        return "\n".join(text_content)

    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """
        Extracts text from a plain text file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            # Log or handle the error as needed
            print(f"Error extracting TXT text: {e}")
            return ""
