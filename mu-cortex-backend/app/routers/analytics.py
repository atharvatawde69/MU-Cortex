import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Response models
class QuestionPrediction(BaseModel):
    question_id: str
    question_text: str
    marks: int
    appearance_count: int
    last_appeared_year: Optional[int]
    prediction_score: float
    study_priority: Optional[str]


class SubjectStats(BaseModel):
    subject_id: str
    subject_name: str
    total_questions: int
    high_freq_questions: int
    high_freq_percentage: float


class StudyPlanQuestion(BaseModel):
    question_id: str
    question_text: str
    marks: int
    appearance_count: int
    last_appeared_year: Optional[int]
    prediction_score: float
    study_priority: str
    estimated_hours: float


class StudyPlanResponse(BaseModel):
    total_questions: int
    estimated_hours: float
    hours_available: float
    questions: List[StudyPlanQuestion]
    strategy: str
    coverage_estimate: str


@router.get("/predictions/subject/{subject_id}")
def get_predictions_by_subject(
    subject_id: str,
    scheme_id: str = Query(..., description="Scheme id (e.g. 2019 or 2024)"),
    min_score: float = Query(0.0, ge=0, description="Minimum prediction score"),
    study_priority: Optional[str] = Query(None, description="Filter by study priority"),
):
    """
    Get question predictions for a subject.
    
    Returns predictions sorted by prediction_score DESC.
    """
    try:
        supabase = get_supabase_client()
        
        query = (
            supabase.table("question_predictions")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("scheme_id", scheme_id)
            .order("prediction_score", desc=True)
        )
        
        if study_priority:
            query = query.eq("study_priority", study_priority)
        
        resp = query.execute()
        
        if not resp.data:
            raise HTTPException(
                status_code=404,
                detail=f"No predictions found for subject_id={subject_id} and scheme_id={scheme_id}"
            )
        
        # Filter by min_score in Python
        filtered_data = [
            row for row in resp.data
            if row.get("prediction_score") is not None and float(row["prediction_score"]) >= min_score
        ]
        
        if not filtered_data:
            raise HTTPException(
                status_code=404,
                detail=f"No predictions found for subject_id={subject_id} and scheme_id={scheme_id} with min_score={min_score}"
            )
        
        predictions = []
        for row in filtered_data:
            predictions.append(
                QuestionPrediction(
                    question_id=row["question_id"],
                    question_text=row["question_text"],
                    marks=row["marks"],
                    appearance_count=row["appearance_count"],
                    last_appeared_year=row.get("last_appeared_year"),
                    prediction_score=row["prediction_score"],
                    study_priority=row.get("study_priority"),
                )
            )
        
        return predictions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch predictions for subject {subject_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch predictions: {str(e)}"
        ) from e


@router.get("/stats/subject/{subject_id}")
def get_subject_stats(
    subject_id: str,
    scheme_id: str = Query(..., description="Scheme id (e.g. 2019 or 2024)"),
):
    """
    Get statistics for a subject.
    
    Returns aggregated stats from subject_question_stats view.
    """
    try:
        supabase = get_supabase_client()
        
        resp = (
            supabase.table("subject_question_stats")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("scheme_id", scheme_id)
            .execute()
        )
        
        if not resp.data:
            raise HTTPException(
                status_code=404,
                detail=f"No stats found for subject_id={subject_id} and scheme_id={scheme_id}"
            )
        
        row = resp.data[0]
        return SubjectStats(
            subject_id=row["subject_id"],
            subject_name=row["subject_name"],
            total_questions=row["total_questions"],
            high_freq_questions=row["high_freq_questions"],
            high_freq_percentage=row["high_freq_percentage"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch stats for subject {subject_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        ) from e


@router.get("/study-plan/survival/{subject_id}")
def get_survival_study_plan(
    subject_id: str,
    scheme_id: str = Query(..., description="Scheme id (e.g. 2019 or 2024)"),
    hours_available: float = Query(6, ge=0, description="Available study hours"),
):
    """
    Generate a survival study plan for a subject.
    
    Strategy:
    - Only includes questions with study_priority = 'must_study'
    - Orders by prediction_score DESC
    - Selects questions until hours_available is exhausted
    - Time per question: 10M → 0.75 hr, 5M → 0.4 hr, 2M → 0.15 hr
    """
    try:
        supabase = get_supabase_client()
        
        # Fetch must_study questions ordered by prediction_score DESC
        resp = (
            supabase.table("question_predictions")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("scheme_id", scheme_id)
            .eq("study_priority", "must_study")
            .order("prediction_score", desc=True)
            .execute()
        )
        
        if not resp.data:
            raise HTTPException(
                status_code=404,
                detail=f"No must_study questions found for subject_id={subject_id} and scheme_id={scheme_id}"
            )
        
        # Time mapping per marks
        time_per_marks = {
            10: 0.75,
            5: 0.4,
            2: 0.15,
        }
        
        selected_questions = []
        total_hours = 0.0
        
        for row in resp.data:
            marks = row["marks"]
            if marks not in time_per_marks:
                logger.warning(f"Unknown marks value: {marks} for question {row['question_id']}")
                continue
            
            question_hours = time_per_marks[marks]
            
            # Check if adding this question would exceed available hours
            if total_hours + question_hours > hours_available:
                break
            
            total_hours += question_hours
            selected_questions.append(
                StudyPlanQuestion(
                    question_id=row["question_id"],
                    question_text=row["question_text"],
                    marks=marks,
                    appearance_count=row["appearance_count"],
                    last_appeared_year=row.get("last_appeared_year"),
                    prediction_score=row["prediction_score"],
                    study_priority=row["study_priority"],
                    estimated_hours=question_hours,
                )
            )
        
        return StudyPlanResponse(
            total_questions=len(selected_questions),
            estimated_hours=round(total_hours, 2),
            hours_available=hours_available,
            questions=selected_questions,
            strategy="Survival mode: Focus on highest-scoring must-study questions",
            coverage_estimate="60-70%",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate study plan for subject {subject_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate study plan: {str(e)}"
        ) from e
