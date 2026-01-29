"""
Generate downloadable study reports for a subject using prediction analytics.

This script generates:
1. CSV file with question predictions
2. TXT summary file with statistics and top questions

Usage:
    python generate_reports.py <subject_id> <scheme_id>
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(message)s')
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


def get_subject_info(supabase: Client, subject_id: str, scheme_id: str) -> Optional[Dict]:
    """Fetch subject information from the subjects table."""
    try:
        resp = (
            supabase.table("subjects")
            .select("id, name, code, scheme_id")
            .eq("id", subject_id)
            .eq("scheme_id", scheme_id)
            .execute()
        )
        
        if resp.data:
            return resp.data[0]
        return None
    except Exception as e:
        logger.error(f"❌ Failed to fetch subject info: {e}")
        return None


def get_predictions(supabase: Client, subject_id: str, scheme_id: str) -> List[Dict]:
    """Fetch question predictions from the analytics view."""
    try:
        resp = (
            supabase.table("question_predictions")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("scheme_id", scheme_id)
            .order("prediction_score", desc=True)
            .execute()
        )
        
        return resp.data or []
    except Exception as e:
        logger.error(f"❌ Failed to fetch predictions: {e}")
        return []


def generate_csv(predictions: List[Dict], output_path: Path):
    """Generate CSV file with question predictions."""
    if not predictions:
        logger.warning("⚠️ No predictions to write to CSV")
        return
    
    # Prepare data for CSV
    csv_data = []
    for pred in predictions:
        csv_data.append({
            "question_text": pred.get("question_text", ""),
            "marks": pred.get("marks"),
            "appearance_count": pred.get("appearance_count", 0),
            "last_appeared_year": pred.get("last_appeared_year"),
            "prediction_score": pred.get("prediction_score"),
            "study_priority": pred.get("study_priority", ""),
        })
    
    df = pd.DataFrame(csv_data)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"✅ CSV generated: {output_path}")


def generate_summary(
    subject: Dict,
    scheme_id: str,
    predictions: List[Dict],
    output_path: Path,
    timestamp: str
):
    """Generate TXT summary file with statistics and top questions."""
    with open(output_path, "w", encoding="utf-8") as f:
        # Header
        f.write("=" * 70 + "\n")
        f.write("STUDY REPORT SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        
        # Subject info
        f.write(f"Subject: {subject['name']}\n")
        f.write(f"Code: {subject['code']}\n")
        f.write(f"Scheme: {scheme_id}\n")
        f.write(f"Generated: {timestamp}\n\n")
        
        # Statistics
        f.write("-" * 70 + "\n")
        f.write("STATISTICS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total questions: {len(predictions)}\n\n")
        
        # Count by study priority
        priority_counts = {
            "must_study": 0,
            "should_study": 0,
            "optional": 0,
        }
        
        for pred in predictions:
            priority = pred.get("study_priority", "").lower()
            if priority in priority_counts:
                priority_counts[priority] += 1
            elif not priority:
                # Count empty/null as optional
                priority_counts["optional"] += 1
        
        f.write("Study Priority Breakdown:\n")
        f.write(f"  - Must Study: {priority_counts['must_study']}\n")
        f.write(f"  - Should Study: {priority_counts['should_study']}\n")
        f.write(f"  - Optional: {priority_counts['optional']}\n\n")
        
        # Top 15 questions
        f.write("-" * 70 + "\n")
        f.write("TOP 15 QUESTIONS BY PREDICTION SCORE\n")
        f.write("-" * 70 + "\n\n")
        
        top_15 = predictions[:15]
        for idx, pred in enumerate(top_15, 1):
            f.write(f"{idx}. {pred.get('question_text', '')[:100]}...\n")
            f.write(f"   Marks: {pred.get('marks')} | ")
            f.write(f"Appearances: {pred.get('appearance_count', 0)} | ")
            
            last_year = pred.get("last_appeared_year")
            if last_year:
                f.write(f"Last Year: {last_year} | ")
            
            f.write(f"Score: {pred.get('prediction_score', 0):.2f}\n\n")
        
        f.write("=" * 70 + "\n")
    
    logger.info(f"✅ Summary generated: {output_path}")


def main():
    """Main function to generate reports."""
    parser = argparse.ArgumentParser(
        description="Generate study reports for a subject using prediction analytics"
    )
    parser.add_argument(
        "subject_id",
        type=str,
        help="Subject ID (UUID)"
    )
    parser.add_argument(
        "scheme_id",
        type=str,
        help="Scheme ID (e.g., '2019' or '2024')"
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting report generation")
    logger.info(f"Subject ID: {args.subject_id}")
    logger.info(f"Scheme ID: {args.scheme_id}")
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Fetch subject info
    logger.info("📋 Fetching subject information...")
    subject = get_subject_info(supabase, args.subject_id, args.scheme_id)
    
    if not subject:
        logger.error(f"❌ Subject not found for subject_id={args.subject_id} and scheme_id={args.scheme_id}")
        sys.exit(1)
    
    logger.info(f"✅ Subject found: {subject['name']} ({subject['code']})")
    
    # Fetch predictions
    logger.info("📊 Fetching question predictions...")
    predictions = get_predictions(supabase, args.subject_id, args.scheme_id)
    
    if not predictions:
        logger.error(f"❌ No predictions found for subject_id={args.subject_id} and scheme_id={args.scheme_id}")
        sys.exit(1)
    
    logger.info(f"✅ Found {len(predictions)} predictions")
    
    # Create reports directory
    reports_dir = ROOT_DIR / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subject_code = subject["code"]
    
    # Generate CSV
    csv_filename = f"{subject_code}_study_guide_{timestamp}.csv"
    csv_path = reports_dir / csv_filename
    generate_csv(predictions, csv_path)
    
    # Generate summary
    summary_filename = f"{subject_code}_summary_{timestamp}.txt"
    summary_path = reports_dir / summary_filename
    generate_summary(
        subject,
        args.scheme_id,
        predictions,
        summary_path,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ Report generation complete!")
    logger.info("=" * 70)
    logger.info(f"📄 CSV: {csv_path}")
    logger.info(f"📄 Summary: {summary_path}")


if __name__ == "__main__":
    main()
