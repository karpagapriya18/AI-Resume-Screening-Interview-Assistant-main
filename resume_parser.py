import re
from pathlib import Path

import fitz
from docx import Document


COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "node.js", "express", "fastapi", "flask", "django", "sql", "mysql",
    "postgresql", "mongodb", "html", "css", "tailwind", "bootstrap",
    "git", "github", "docker", "kubernetes", "aws", "azure", "gcp",
    "machine learning", "deep learning", "nlp", "data analysis",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "rest api", "api", "linux", "excel", "power bi", "tableau"
]


def extract_text_from_pdf(file_path: str) -> str:
    text = ""

    document = fitz.open(file_path)

    for page in document:
        text += page.get_text()

    document.close()
    return text.strip()


def extract_text_from_docx(file_path: str) -> str:
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text.strip())

    return "\n".join(paragraphs)


def extract_resume_text(file_path: str) -> str:
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if extension == ".docx":
        return extract_text_from_docx(file_path)

    raise ValueError("Unsupported file format. Only PDF and DOCX are allowed.")


def extract_email(text: str) -> str | None:
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return None


def extract_phone(text: str) -> str | None:
    pattern = r"(\+?\d[\d\s\-()]{8,}\d)"
    matches = re.findall(pattern, text)

    if matches:
        phone = matches[0].strip()
        return phone

    return None


def extract_name(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines[:10]:
        lower_line = line.lower()

        if "resume" in lower_line:
            continue

        if "curriculum vitae" in lower_line:
            continue

        if "@" in line:
            continue

        if re.search(r"\d", line):
            continue

        if len(line.split()) <= 5:
            return line

    return None


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found_skills = []

    for skill in COMMON_SKILLS:
        if skill.lower() in text_lower:
            found_skills.append(skill.title())

    return sorted(list(set(found_skills)))


def extract_experience(text: str) -> str | None:
    patterns = [
        r"(\d+)\+?\s*years?\s+of\s+experience",
        r"experience\s*[:\-]?\s*(\d+)\+?\s*years?",
        r"(\d+)\+?\s*yrs?\s+experience",
        r"(\d+)\+?\s*years?"
    ]

    text_lower = text.lower()

    for pattern in patterns:
        match = re.search(pattern, text_lower)

        if match:
            return f"{match.group(1)} years"

    return None


def extract_education(text: str) -> str | None:
    education_keywords = [
        "b.tech", "bachelor", "master", "m.tech", "mba", "bca", "mca",
        "degree", "university", "college", "engineering", "diploma"
    ]

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    education_lines = []

    for line in lines:
        line_lower = line.lower()

        if any(keyword in line_lower for keyword in education_keywords):
            education_lines.append(line)

    if education_lines:
        return "\n".join(education_lines[:5])

    return None


def parse_resume(file_path: str) -> dict:
    text = extract_resume_text(file_path)

    return {
        "resume_text": text,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "total_experience": extract_experience(text),
        "education": extract_education(text)
    }