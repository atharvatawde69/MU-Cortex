"""
Mumbai University (MU) Answer Prompt Generator.

This module provides prompt templates for generating MU-style exam answers
that match examiner expectations. MU answers follow strict formatting rules
based on marks (5 vs 10 marks) and must be clear, structured, and student-friendly.

Key MU Answer Style Rules:
- 10 marks: 250-300 words, structured with Introduction, Main Content, Diagram, Example, Conclusion
- 5 marks: 100-150 words, structured with Definition, Key Points, Example/Diagram
- Simple, clear English suitable for undergraduate level
- Technical terms should be bolded
- Formulas and diagrams are mandatory for 10-mark questions
- No fluff, no emojis, direct and concise
"""


def generate_10_mark_answer_prompt(question: str, context: str = "") -> str:
    """
    Generate a prompt for a 10-mark MU-style answer.

    Args:
        question: The exam question text.
        context: Optional context (e.g., from video transcripts).

    Returns:
        A complete prompt string that enforces MU 10-mark answer structure.
    """
    context_section = ""
    if context:
        context_section = f"\n\nAdditional Context:\n{context}\n"
    
    prompt = f"""Answer the following Mumbai University 10-mark exam question in the EXACT format specified below.

Question:
{question}
{context_section}
REQUIREMENTS (STRICT):

1. WORD COUNT: 250-300 words exactly.

2. STRUCTURE (MANDATORY ORDER):
   
   a) INTRODUCTION (2-3 lines)
      - Define the main concept
      - State its importance/application
   
   b) MAIN CONTENT (10-15 bullet points, 2-3 lines each)
      - Use bullet points (• or -)
      - Bold important technical terms using **term**
      - Include formulas if applicable (use LaTeX notation: $formula$)
      - Cover all aspects of the question
      - Each bullet should be substantial (2-3 lines)
   
   c) DIAGRAM (MANDATORY)
      - Use format: [DIAGRAM: description]
      - Describe what the diagram shows
      - Example: [DIAGRAM: Shows the architecture with three layers: input, processing, output]
   
   d) EXAMPLE (MANDATORY)
      - For concepts/algorithms: provide step-by-step example
      - For numerical: show calculation with values
      - For code: provide simple code snippet or pseudocode
      - Make it practical and easy to understand
   
   e) CONCLUSION (2-3 lines)
      - Summarize key points
      - Mention real-world application or importance

3. LANGUAGE RULES:
   - Simple, clear English
   - Student-friendly (undergraduate level)
   - No fluff or unnecessary words
   - No emojis or symbols
   - Direct and concise
   - Use active voice where possible

4. FORMATTING:
   - Use **bold** for technical terms
   - Use $...$ for formulas
   - Use bullet points for main content
   - Use clear section headers

Generate the answer now, following ALL requirements above strictly."""

    return prompt


def generate_5_mark_answer_prompt(question: str, context: str = "") -> str:
    """
    Generate a prompt for a 5-mark MU-style answer.

    Args:
        question: The exam question text.
        context: Optional context (e.g., from video transcripts).

    Returns:
        A complete prompt string that enforces MU 5-mark answer structure.
    """
    context_section = ""
    if context:
        context_section = f"\n\nAdditional Context:\n{context}\n"
    
    prompt = f"""Answer the following Mumbai University 5-mark exam question in the EXACT format specified below.

Question:
{question}
{context_section}
REQUIREMENTS (STRICT):

1. WORD COUNT: 100-150 words exactly.

2. STRUCTURE (MANDATORY ORDER):
   
   a) DEFINITION (1-2 lines)
      - Clear, concise definition of the main concept
      - Bold key technical terms using **term**
   
   b) KEY POINTS (5-7 bullet points, 1-2 lines each)
      - Use bullet points (• or -)
      - Each point should be brief but informative
      - Cover essential aspects only
      - Bold important terms using **term**
   
   c) EXAMPLE OR DIAGRAM (choose ONE only)
      - Either provide a simple example (2-3 lines)
      - OR use format: [DIAGRAM: description]
      - Do NOT include both

3. LANGUAGE RULES:
   - Simple, clear English
   - Student-friendly (undergraduate level)
   - No fluff or unnecessary words
   - No emojis or symbols
   - Direct and concise
   - Use active voice where possible

4. FORMATTING:
   - Use **bold** for technical terms
   - Use bullet points for key points
   - Keep it brief and focused

Generate the answer now, following ALL requirements above strictly."""

    return prompt


def extract_context_from_transcript(transcript: str, question: str) -> str:
    """
    MVP keyword-based context extraction from video transcripts.

    Extracts relevant paragraphs from a transcript based on keyword matching
    with the question. Uses simple text matching (no ML/embeddings).

    Args:
        transcript: Full video transcript text.
        question: The exam question text.

    Returns:
        Extracted context string (at most 3 relevant paragraphs).
    """
    if not transcript or not question:
        return ""
    
    # Extract keywords from question (words >= 4 characters)
    question_words = question.lower().split()
    keywords = [word.strip('.,!?;:()[]{}"\'-') for word in question_words 
                if len(word.strip('.,!?;:()[]{}"\'-')) >= 4]
    
    if not keywords:
        return ""
    
    # Split transcript into paragraphs
    paragraphs = [p.strip() for p in transcript.split('\n\n') if p.strip()]
    
    # Score each paragraph by keyword matches
    scored_paragraphs = []
    for para in paragraphs:
        para_lower = para.lower()
        # Count keyword matches (case-insensitive)
        match_count = sum(1 for keyword in keywords if keyword in para_lower)
        if match_count > 0:
            scored_paragraphs.append((match_count, para))
    
    # Sort by match count (descending) and take top 3
    scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
    top_paragraphs = [para for _, para in scored_paragraphs[:3]]
    
    # Join paragraphs with double newline
    return '\n\n'.join(top_paragraphs) if top_paragraphs else ""
