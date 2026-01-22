"""
Ingest parsed PYQ questions into Supabase database.

This script reads all JSON files from pyq_parsed/ and inserts questions
into the Supabase questions and question_appearances tables.

The script is idempotent - safe to re-run multiple times.
"""
import os
import sys
import json
import re
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / ".env"
load_dotenv(env_path)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("❌ SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in root .env file")

# Manual configuration - update these values as needed
SUBJECT_ID = os.getenv("SUBJECT_ID")  # UUID of the subject
SCHEME_ID = os.getenv("SCHEME_ID")     # TEXT scheme identifier (e.g. "2019")

if not SUBJECT_ID or not SCHEME_ID:
    raise ValueError("❌ SUBJECT_ID and SCHEME_ID must be set in root .env file or script config")


def normalize_text(text: str) -> str:
    """
    Normalize question text for deduplication.
    - Convert to lowercase
    - Remove punctuation
    - Collapse whitespace to single spaces
    """
    if not text:
        return ""
    
    # Convert to lowercase
    normalized = text.lower()
    
    # Remove punctuation (keep alphanumeric and spaces)
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Collapse whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip()


def hash_text(text: str) -> str:
    """Generate SHA256 hash from normalized text."""
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def extract_year(appeared_in: str) -> int:
    """
    Extract year from appeared_in field.
    Examples:
    - "Dec 2022, 2019 Scheme" → 2022
    - "May 2023" → 2023
    - "2022" → 2022
    
    Returns current year if no year found (year is NOT NULL in schema).
    """
    if not appeared_in:
        return datetime.now().year
    
    # Look for 4-digit year patterns (19xx or 20xx)
    year_pattern = r'\b(19|20)\d{2}\b'
    matches = re.finditer(year_pattern, appeared_in)
    
    years = []
    for match in matches:
        full_year_str = match.group(0)
        try:
            year = int(full_year_str)
            if 1900 <= year <= 2100:  # Sanity check
                years.append(year)
        except ValueError:
            continue
    
    if years:
        # Return the most recent year found (prefer exam year over scheme year)
        return max(years)
    
    # Fallback to current year if no valid year found
    return datetime.now().year


def load_questions_from_json(json_path: Path) -> List[Dict]:
    """Load questions from a single JSON file."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.warning(f"⚠️ {json_path.name} does not contain a JSON array")
            return []
        
        return data
    except Exception as e:
        logger.error(f"❌ Failed to load {json_path.name}: {e}")
        return []


def ingest_questions(supabase: Client, questions: List[Dict], stats: Dict):
    """
    Ingest questions into Supabase.
    
    For each question:
    1. Normalize and hash the question text
    2. Check if question exists (by normalized_hash)
    3. Insert into questions if new (with topic_id if available)
    4. Always insert into question_appearances (with subject_id, scheme_id, confidence)
    """
    for q in questions:
        question_text = q.get("question_text", "").strip()
        if not question_text:
            logger.warning("⚠️ Skipping question with empty question_text")
            continue
        
        stats["total_questions_read"] += 1
        
        # Normalize and hash
        normalized_hash = hash_text(question_text)
        
        # Check if question already exists
        existing = supabase.table("questions").select("id").eq("normalized_hash", normalized_hash).execute()
        
        if existing.data:
            # Question exists - use existing ID
            question_id = existing.data[0]["id"]
            stats["duplicates_skipped"] += 1
            logger.debug(f"Found existing question: {normalized_hash[:8]}...")
        else:
            # New question - insert it
            try:
                new_question = {
                    "question_text": question_text,
                    "marks": q.get("marks"),
                    "normalized_hash": normalized_hash,
                    "topic_id": None  # topic_id is nullable, can be set later if topic mapping exists
                }
                
                result = supabase.table("questions").insert(new_question).execute()
                question_id = result.data[0]["id"]
                stats["new_questions"] += 1
                logger.debug(f"Inserted new question: {normalized_hash[:8]}...")
            except Exception as e:
                logger.error(f"❌ Failed to insert question: {e}")
                continue
        
        # Always insert appearance (even if question was duplicate)
        appeared_in = q.get("appeared_in", "")
        year = extract_year(appeared_in)
        confidence = q.get("confidence")
        
        # Convert confidence to float if present, ensure it's within NUMERIC(3,2) range
        if confidence is not None:
            try:
                confidence = float(confidence)
                if confidence < 0:
                    confidence = 0.0
                elif confidence > 1.0:
                    confidence = 1.0
            except (ValueError, TypeError):
                confidence = None
        
        try:
            appearance = {
                "question_id": question_id,
                "appeared_in": appeared_in,
                "year": year,
                "subject_id": SUBJECT_ID,
                "scheme_id": SCHEME_ID,  # TEXT, not UUID (e.g. "2019")
                "confidence": confidence
            }
            
            logger.info(f"Inserting appearance with scheme_id={SCHEME_ID} (TEXT)")
            supabase.table("question_appearances").insert(appearance).execute()
            stats["appearances_inserted"] += 1
        except Exception as e:
            logger.error(f"❌ Failed to insert appearance: {e}")


def main():
    """Main ingestion function."""
    logger.info("🚀 Starting question ingestion process")
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Find all JSON files in pyq_parsed/
    parsed_dir = ROOT_DIR / "pyq_parsed"
    if not parsed_dir.exists():
        logger.error(f"❌ Directory not found: {parsed_dir}")
        sys.exit(1)
    
    json_files = list(parsed_dir.glob("*.json"))
    if not json_files:
        logger.warning("⚠️ No JSON files found in pyq_parsed/")
        sys.exit(0)
    
    logger.info(f"📂 Found {len(json_files)} JSON file(s) to process")
    
    # Statistics tracking
    stats = {
        "files_processed": 0,
        "total_questions_read": 0,
        "new_questions": 0,
        "appearances_inserted": 0,
        "duplicates_skipped": 0
    }
    
    # Process each JSON file
    for json_file in json_files:
        logger.info(f"📄 Processing: {json_file.name}")
        
        questions = load_questions_from_json(json_file)
        if not questions:
            logger.warning(f"⚠️ No questions found in {json_file.name}")
            continue
        
        logger.info(f"   Found {len(questions)} question(s)")
        
        ingest_questions(supabase, questions, stats)
        stats["files_processed"] += 1
    
    # Print summary
    print("\n" + "="*60)
    print("📊 INGESTION SUMMARY")
    print("="*60)
    print(f"Total JSON files processed: {stats['files_processed']}")
    print(f"Total questions read: {stats['total_questions_read']}")
    print(f"New questions inserted: {stats['new_questions']}")
    print(f"Duplicates skipped: {stats['duplicates_skipped']}")
    print(f"Question appearances inserted: {stats['appearances_inserted']}")
    print("="*60)
    print("✅ Ingestion complete")


if __name__ == "__main__":
    main()
