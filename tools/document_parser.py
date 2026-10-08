import io
from pathlib import Path
from pypdf import PdfReader

def extract_text(uploaded):
    name=uploaded.name.lower()
    data=uploaded.getvalue()
    if name.endswith('.pdf'):
        reader=PdfReader(io.BytesIO(data))
        return '\n'.join((p.extract_text() or '') for p in reader.pages).strip()
    if name.endswith('.docx'):
        try:
            from docx import Document
        except ImportError:
            raise RuntimeError('python-docx is required for Word files. Install requirements.txt.')
        doc=Document(io.BytesIO(data))
        return '\n'.join(p.text for p in doc.paragraphs).strip()
    return data.decode('utf-8',errors='ignore').strip()
