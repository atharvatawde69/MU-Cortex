from pathlib import Path
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

# --- ENV LOADING (CRITICAL) ---
ROOT_DIR = Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / ".env"
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger.info(f"Loaded environment variables from: {env_path}")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found. Check root .env file.")

import json
import re
import sys
from typing import List, Dict
import google.generativeai as genai


def clean_extracted_text(text: str) -> str:
    """
    Remove excessive single-character noise lines from extracted text.
    Preserves all real content while cleaning OCR artifacts.
    """
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if len(stripped) <= 1:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def infer_marks(text: str) -> int:
    """Infer marks from question text based on wording and length."""
    text_lower = text.lower()

    if 'define' in text_lower or 'what is' in text_lower:
        return 2
    if 'explain' in text_lower or 'describe' in text_lower:
        return 10
    if len(text) < 120:
        return 5
    return 10


def extract_question_blocks(text: str) -> List[Dict]:
    """
    Phase 1 (NO LLM):
    Deterministically extract MU question blocks using regex heuristics.
    
    Handles:
    - Main questions: Q.1, Q.2, Q.3, ...
    - Sub-questions: a), b), c), d)
    - OR blocks: split into separate questions
    - Marks: inferred from wording or defaults
    """
    blocks = []

    if not text:
        return blocks

    # Normalize text
    text = re.sub(r'\r', '', text)
    text = re.sub(r'[ \t]+', ' ', text)

    # Split by main questions: Q.1, Q.2, Q.3
    main_q_pattern = re.compile(r'(Q\.\s*\d+)', re.IGNORECASE)
    parts = main_q_pattern.split(text)

    for i in range(1, len(parts), 2):
        q_number = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""

        # Split OR blocks first
        or_parts = re.split(r'\bOR\b', body, flags=re.IGNORECASE)

        for or_index, or_part in enumerate(or_parts):
            # Split sub-questions: a), b), c)
            sub_parts = re.split(r'\n\s*([a-f])\)', or_part, flags=re.IGNORECASE)

            if len(sub_parts) == 1:
                # No sub-parts
                raw = sub_parts[0].strip()
                if len(raw) < 30:
                    continue

                blocks.append({
                    "q_number": q_number,
                    "sub_part": None,
                    "raw_text": raw,
                    "marks": infer_marks(raw)
                })
            else:
                for j in range(1, len(sub_parts), 2):
                    sub = sub_parts[j].lower() if j < len(sub_parts) else None
                    raw = sub_parts[j + 1].strip() if j + 1 < len(sub_parts) else ""
                    if len(raw) < 20:
                        continue

                    blocks.append({
                        "q_number": q_number,
                        "sub_part": sub,
                        "raw_text": raw,
                        "marks": infer_marks(raw)
                    })

    return blocks


def extract_json_object(text: str) -> Dict:
    """
    Extract a JSON object from a potentially noisy/truncated response.
    Used for Phase 2 per-sub-question normalization.
    """
    if not text:
        return {}

    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return {}
    candidate = text[first : last + 1]
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def extract_json_array(text: str) -> List[Dict]:
    """
    Extract JSON array from potentially truncated Gemini response.
    Safely recovers valid question objects even if the response was cut off mid-array.
    
    Args:
        text: Response text that may contain partial JSON
        
    Returns:
        List of question dictionaries, empty list if extraction fails
    """
    if not text:
        return []
    
    # Find the first '[' that starts the JSON array
    first_bracket = text.find('[')
    if first_bracket == -1:
        logger.warning("No opening bracket '[' found in response")
        return []
    
    # Find the last '}' character (marks end of last complete object)
    last_brace = text.rfind('}')
    if last_brace == -1 or last_brace < first_bracket:
        logger.warning("No closing brace '}' found or it appears before opening bracket")
        return []
    
    # Extract the partial JSON: from '[' to the last complete '}'
    repaired_json = text[first_bracket : last_brace + 1]
    
    # Check if closing bracket is missing (truncation indicator)
    if not repaired_json.rstrip().endswith(']'):
        repaired_json += ']'
        logger.info("⚠️ JSON response appears truncated - attempting recovery")
    
    try:
        questions = json.loads(repaired_json)
        if isinstance(questions, list):
            logger.info(f"Successfully recovered {len(questions)} questions from response")
            return questions
        else:
            logger.warning("Parsed JSON is not a list")
            return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse repaired JSON: {e}")
        return []


class QuestionParser:
    """
    Uses an LLM (Gemini) to extract structured questions
    from messy Mumbai University PYQ text.
    """

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name="models/gemini-2.5-flash",
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 4096
            }
        )

    def parse_pyq_text(
        self,
        text: str,
        subject_name: str,
        exam_info: str = ""
    ) -> List[Dict]:
        """
        Convert extracted PYQ text into structured question objects.
        """
        # Clean OCR noise before any parsing
        text = clean_extracted_text(text)

        # Phase 1: deterministic structure extraction (NO LLM)
        blocks = extract_question_blocks(text)
        if not blocks:
            logger.warning("⚠️ No question blocks found via regex; falling back to single LLM call")
            # Keep legacy behavior as a fallback (still uses truncation-safe array extraction)
            prompt = f"""
You are an expert at parsing **Mumbai University (MU) examination question papers**.

Your task is to extract **ALL questions** from the paper text below.

SUBJECT: {subject_name}  
EXAM INFO: {exam_info if exam_info else "Not specified"}

IMPORTANT STRUCTURE RULES (CRITICAL):
1. MU papers ALWAYS contain Question numbers like:
   - Q.1, Q.2, Q.3, Q.4, Q.5, Q.6
2. Each question MAY contain sub-parts:
   - (a), (b), (c)
3. Instructions like:
   - "Attempt any TWO"
   - "Attempt any THREE"
   MUST be IGNORED, but ALL listed questions must STILL be extracted.
4. OR blocks:
   - "OR" means BOTH sides are valid questions.
   - Extract BOTH as separate questions.
   - Reduce confidence slightly (0.7–0.8).

MANDATORY EXTRACTION RULE:
- You MUST attempt to extract questions from **EVERY Question Number (Q.1 to Q.6)**.
- Do NOT stop early even if some questions are unclear.
- If marks are not explicitly written:
  - Long descriptive questions → 10 marks
  - Medium explanation → 5 marks
  - Short definition/list → 2 marks

WHAT TO SKIP:
- Instructions
- Time / Marks headers
- Page numbers
- University watermarks
- Seat number fields
- Anything that is NOT an actual question

OUTPUT FORMAT (STRICT):
Return ONLY a valid JSON ARRAY.
No markdown.
No explanations.
No extra text.

Each object must be:
{{
  "question_text": "...",
  "marks": 2 | 5 | 10,
  "topic_guess": "...",
  "module_number": 1-6 or null,
  "confidence": 0.0-1.0
}}

EXTRACTED TEXT:
{text}

Now extract ALL questions from this paper.
"""
            try:
                logger.info("Calling Gemini API for question extraction")
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                if not response_text:
                    logger.error("❌ Empty response from Gemini API")
                    return []
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                elif response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                questions = extract_json_array(response_text)
                logger.info(f"Extracted {len(questions)} questions")
                return questions
            except Exception as e:
                logger.error(f"Failed to parse questions: {e}")
                return []

        # Phase 2: LLM normalization (ONE sub-question at a time)
        results: List[Dict] = []
        appeared_in = exam_info if exam_info else ""

        for b in blocks:
            raw_text = (b.get("raw_text") or "").strip()
            if not raw_text:
                continue

            normalize_prompt = f"""
You normalize a single Mumbai University exam sub-question.

Constraints:
- You MUST NOT decide marks.
- You MUST NOT group multiple questions into one.
- You only output ONE JSON object.
- Return ONLY JSON. No markdown. No explanations.

Input metadata:
- q_number: {b.get("q_number")}
- sub_part: {b.get("sub_part") if b.get("sub_part") else ""}
- subject: {subject_name}
- exam_info: {appeared_in if appeared_in else "Not specified"}

Task:
1) Rewrite the question text cleanly (preserve meaning).
2) Provide topic_guess.
3) Provide module_number (1-6) if inferable else null.
4) Provide confidence (0.0-1.0).

Output schema (STRICT):
{{
  "question_text": "...",
  "topic_guess": "...",
  "module_number": 1,
  "confidence": 0.9
}}

RAW SUB-QUESTION TEXT:
{raw_text}
"""

            try:
                response = self.model.generate_content(normalize_prompt)
                response_text = (response.text or "").strip()
                if not response_text:
                    raise ValueError("Empty Gemini response")

                # Strip ```json fences if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                elif response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                norm = extract_json_object(response_text)
                if not norm:
                    raise ValueError("Could not parse JSON object from Gemini output")

                question_text = norm.get("question_text") or raw_text
                topic_guess = norm.get("topic_guess") or ""
                module_number = norm.get("module_number", None)
                confidence = norm.get("confidence", 0.6)

            except Exception as e:
                logger.warning(f"⚠️ Gemini normalization failed for {b.get('q_number')}{b.get('sub_part') or ''}: {e}")
                question_text = raw_text
                topic_guess = ""
                module_number = None
                confidence = 0.6

            results.append(
                {
                    "q_number": b.get("q_number"),
                    "sub_part": b.get("sub_part"),
                    "question_text": question_text,
                    "marks": b.get("marks"),
                    "topic_guess": topic_guess,
                    "module_number": module_number,
                    "confidence": confidence,
                    "appeared_in": appeared_in,
                }
            )

        logger.info(f"Extracted {len(results)} questions (two-phase parsing)")
        return results

    def save_parsed_questions(self, questions: List[Dict], output_path: str):
        Path(output_path).parent.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved parsed questions to {output_path}")


def main():
    if len(sys.argv) < 4:
        print("Usage: python parse_questions.py <text_file> <subject_name> <exam_info>")
        sys.exit(1)

    text_file = sys.argv[1]
    subject_name = sys.argv[2]
    exam_info = sys.argv[3]

    # Resolve path to handle Windows paths, Unicode filenames, and relative paths
    text_path = Path(text_file).resolve()

    if not text_path.exists():
        logger.error(f"❌ File not found: {text_path}")
        parent = text_path.parent
        if parent.exists():
            logger.info("📂 Available files in directory:")
            for f in sorted(parent.glob("*.txt")):
                logger.info(f"   - {f.name}")
        else:
            logger.error(f"❌ Parent directory does not exist: {parent}")
        sys.exit(1)

    # Use pathlib-safe file opening with explicit UTF-8 encoding for Unicode support
    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read()

    parser = QuestionParser()
    questions = parser.parse_pyq_text(text, subject_name, exam_info)

    # Use resolved path for output filename consistency
    output_file = Path("pyq_parsed") / (text_path.stem + "_parsed.json")
    parser.save_parsed_questions(questions, output_file)

    print(f"Parsed {len(questions)} questions")


if __name__ == "__main__":
    main()
