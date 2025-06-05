
from docx import Document
from pathlib import Path

BASE_CV_PATH = Path("templates/base_cv.docx")

def tailor_cv(job):
    """Replaces placeholder tags in the base CV and saves a tailored copy."""
    doc = Document(str(BASE_CV_PATH))
    for p in doc.paragraphs:
        p.text = p.text.replace("{{job_title}}", job["title"])
        p.text = p.text.replace("{{company}}", job["company"])
    out_path = Path(f"cv_{job['company'].lower().replace(' ', '_')}.docx")
    doc.save(out_path)
    return out_path
