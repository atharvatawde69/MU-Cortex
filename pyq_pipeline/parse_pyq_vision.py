import os
import sys
import json
import re
import logging
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env from project root
ROOT_DIR = Path(__file__).resolve().parents[1]
env_path = ROOT_DIR / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in root .env")

genai.configure(api_key=API_KEY)

MODEL_NAME = "models/gemini-2.5-flash"

PROMPT_TEMPLATE = """
You are an expert Mumbai University examiner.

TASK:
Extract ALL exam questions from the provided question paper PDF.

RULES:
- Extract EVERY main question and sub-question separately
- Handle OR blocks as separate questions
- Ignore instructions, headers, footers, watermarks
- Preserve original wording
- Infer marks (2 / 5 / 10) using MU conventions
- Guess module_number if possible, else null

OUTPUT:
Return ONLY a JSON array like this:

[
  {
    "question_text": "...",
    "marks": 10,
    "topic_guess": "...",
    "module_number": 3,
    "appeared_in": "Dec 2022, 2019 Scheme",
    "confidence": 0.9
  }
]
"""

def extract_text_from_gemini_response(response) -> str:
    if not response.candidates:
        return ""

    candidate = response.candidates[0]

    if not candidate.content or not candidate.content.parts:
        return ""

    text_parts = []
    for part in candidate.content.parts:
        if hasattr(part, "text") and part.text:
            text_parts.append(part.text)

    return "\n".join(text_parts).strip()


def recover_json_array(raw: str):
    import json, re
    # Remove code fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```json|```$", "", raw, flags=re.MULTILINE).strip()

    # Try full parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Recover partial JSON array
    start = raw.find("[")
    if start == -1:
        return []

    recovered = []
    buffer = ""
    depth = 0
    for ch in raw[start:]:
        buffer += ch
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    recovered.append(json.loads(buffer.strip().rstrip(",")))
                except Exception:
                    pass
                buffer = ""

    return recovered


def parse_pdf(pdf_path: Path, subject: str, exam_info: str):
    logger.info("📄 Sending PDF to Gemini Vision model")

    model = genai.GenerativeModel(MODEL_NAME)

    pdf_bytes = pdf_path.read_bytes()

    response = model.generate_content(
        [
            PROMPT_TEMPLATE + f"\nSUBJECT: {subject}\nEXAM: {exam_info}",
            {
                "mime_type": "application/pdf",
                "data": pdf_bytes
            }
        ],
        generation_config={"temperature": 0.1}
    )

    raw = extract_text_from_gemini_response(response)

    if not raw:
        raise RuntimeError("❌ Gemini Vision returned no readable text (possibly safety-blocked).")

    questions = recover_json_array(raw)

    if len(questions) > 0:
        logger.info(f"✅ Recovered {len(questions)} questions from Gemini Vision response")
        return questions
    else:
        logger.error("❌ No valid questions recovered from Gemini Vision output")
        logger.error(f"Raw response preview: {raw[:1000]}")
        raise RuntimeError("No valid questions recovered from Gemini Vision output")


def main():
    if len(sys.argv) < 4:
        print("Usage:")
        print("python parse_pyq_vision.py <pdf_path> <subject> <exam_info>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    subject = sys.argv[2]
    exam_info = sys.argv[3]

    questions = parse_pdf(pdf_path, subject, exam_info)

    out_dir = ROOT_DIR / "pyq_parsed"
    out_dir.mkdir(exist_ok=True)

    out_file = out_dir / f"{pdf_path.stem}_vision.json"
    out_file.write_text(json.dumps(questions, indent=2), encoding="utf-8")

    logger.info(f"✅ Extracted {len(questions)} questions")
    logger.info(f"💾 Saved to {out_file}")


if __name__ == "__main__":
    main()
