"""Simple CV Parser"""

import PyPDF2
from docx import Document
import io

class CVParser:
    @staticmethod
    def extract_text(filename: str, contents: bytes):
        """Extract text from PDF or DOCX"""
        # FIX: Use filename and bytes directly
        if filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        
        elif filename.endswith('.docx'):
            doc = Document(io.BytesIO(contents))
            return "\n".join([para.text for para in doc.paragraphs])
        
        return ""
    @staticmethod
    def parse(text):
        """Extract structured data from CV text"""
        return {
            "raw_text": text,
            "name": CVParser._extract_name(text),
            "email": CVParser._extract_email(text),
            "phone": CVParser._extract_phone(text),
            "skills": CVParser._extract_skills(text),
            "experience_years": CVParser._extract_experience(text),
        }
    
    @staticmethod
    def _extract_name(text):
        lines = text.split('\n')
        return lines[0].strip() if lines else "Unknown"
    
    @staticmethod
    def _extract_email(text):
        import re
        match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        return match.group(0) if match else ""
    
    @staticmethod
    def _extract_phone(text):
        import re
        match = re.search(r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', text)
        return match.group(0) if match else ""
    
    @staticmethod
    def _extract_skills(text):
        # Simple skill extraction
        common_skills = ["python", "java", "javascript", "mongodb", "fastapi", "react", "docker"]
        found_skills = [skill for skill in common_skills if skill.lower() in text.lower()]
        return found_skills
    
    @staticmethod
    def _extract_experience(text):
        import re
        match = re.search(r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?experience', text.lower())
        return int(match.group(1)) if match else 0