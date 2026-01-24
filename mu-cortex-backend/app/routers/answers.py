from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.database import supabase
from app.prompts.answer_generator import (
    generate_10_mark_answer_prompt,
    generate_5_mark_answer_prompt,
)
from app.repositories.questions_repository import get_question_by_id
from app.services.llm.gemini_client import generate_text
from app.services.transcript_service import TranscriptService

router = APIRouter(prefix="/answers", tags=["answers"])


class GenerateAnswerRequest(BaseModel):
    question_id: str


@router.post("/generate")
async def generate_answer(request: GenerateAnswerRequest):
    """
    Generate an answer for a given question using Gemini.
    
    Args:
        request: Request body containing question_id.
    
    Returns:
        JSON with question_id and generated answer.
    
    Raises:
        HTTPException 404: If question not found.
        HTTPException 500: If answer generation fails.
    """
    # Fetch question from database
    question = await get_question_by_id(request.question_id)
    
    if not question:
        raise HTTPException(
            status_code=404,
            detail=f"Question with id {request.question_id} not found"
        )
    
    question_text = question.get("question_text", "")
    marks = question.get("marks")
    topic_id = question.get("topic_id")
    
    # Fetch optional transcript context if topic_id exists
    context = ""
    if topic_id:
        context = await TranscriptService.get_best_context_for_topic(
            topic_id,
            supabase
        )
    
    # Select prompt template based on marks
    if marks == 10:
        prompt = generate_10_mark_answer_prompt(question_text, context)
    elif marks == 5:
        prompt = generate_5_mark_answer_prompt(question_text, context)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported marks type: {marks}. Only 5 and 10 marks are supported."
        )
    
    try:
        # Generate answer using Gemini
        answer = await generate_text(prompt)
        
        return {
            "question_id": request.question_id,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}"
        ) from e
