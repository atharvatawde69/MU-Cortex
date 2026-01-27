"""
Mumbai University (MU) Answer Prompt Generator.

This module provides prompt templates for generating MU-style exam answers
that match examiner expectations. MU answers follow strict formatting rules
based on marks (5 vs 10 marks) and must be clear, structured, and student-friendly.

Key MU Answer Style Rules:
- 10 marks: 280-350 words, structured with Introduction, Main Content, Diagram, Example, Conclusion
- 5 marks: 130-180 words, structured with Definition, Key Points, Example/Diagram
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
Write like a Mumbai University topper would—using standard textbook terminology, examiner-visible keywords, and formal academic phrasing.

Question:
{question}
{context_section}
REQUIREMENTS (STRICT):

1. WORD COUNT: 280-350 words exactly.

2. STRUCTURE (MANDATORY ORDER):
   
   a) INTRODUCTION (2-3 lines)
      - Define the main concept using standard academic terminology
      - State its importance/application with formal phrasing
      - Use examiner-visible keywords naturally
   
   b) MAIN CONTENT (10-15 bullet points, 3-4 lines each)
      - Use bullet points (• or -)
      - Each bullet must be substantial (3-4 lines, not 2)
      - Write bullets so that each bullet can be independently memorized
      - Keep bullets concise (2-4 lines)—do NOT turn bullets into paragraphs
      - Each bullet should contain:
        • core definition
        • 1-2 alternate keywords/phrases (use synonyms or alternate academic terms in parentheses when appropriate)
        • formal textbook wording
      - To reach word count target: expand INSIDE existing bullets only
      - Each bullet may be expanded by one additional explanatory line or one additional examiner keyword phrase
      - Do NOT add new sections, new bullets, or long paragraphs to meet word count
      - Prefer clarification, definition reinforcement, or short examples within bullets
      - Use clear subheadings for each major point when applicable
      - Bold important technical terms using **term**
      - Include formulas if applicable (use LaTeX notation: $formula$)
      - Cover all aspects of the question comprehensively
      - For algorithms: include explicit step-wise explanation with cause-effect relationships
      - Use explicit cause-effect phrasing (e.g., "This occurs because...", "As a result of...", "Due to this...")
      - Repeat core keywords naturally throughout (2-3 times per major section)
   
   c) DIAGRAM (MANDATORY)
      - Use format: [DIAGRAM: description]
      - Describe what the diagram shows using formal terminology
      - Example: [DIAGRAM: Shows the architecture with three layers: input, processing, output]
   
   d) EXAMPLE (MANDATORY)
      - For concepts/algorithms: provide detailed step-by-step example with clear explanations
      - For numerical: show calculation with values and explain each step
      - For code: provide simple code snippet or pseudocode with comments
      - Make it practical and easy to understand while using formal language
   
   e) CONCLUSION (2-3 lines)
      - Summarize key points using standard terminology
      - Mention real-world application or importance with formal phrasing

   f) REAL-WORLD EXAMPLE (MANDATORY where applicable)
      - Include one simple real-world example if the concept allows
      - Examples must be intuitive and everyday (rain, traffic, exams, machines, medical diagnosis, etc.)
      - Use clear IF–THEN or step-wise reasoning
      - Label clearly as: "Real-World Example:"
      - These examples are ADDITIONAL and do NOT count toward the main word limit (280-350 words)
      - Keep examples concise, step-based, and easy to remember
      - Examples should help students understand the concept intuitively

3. COMPARISON QUESTION FORMATTING:
   - If the question contains: "Compare", "Differentiate", "Distinguish between", or similar comparison terms
   - Then present the core answer in a TABLE format
   - Table must have:
     Column 1: Basis (or "Aspect" or "Feature")
     Column 2: Concept A (name the first concept)
     Column 3: Concept B (name the second concept)
   - After the table, add a short real-world example (if applicable) labeled as "Real-World Example:"
   - Table should be clear, well-structured, and easy to scan
   - Use bullet-point format for non-comparison questions; tables ONLY for comparison-type questions

4. KEYWORD EXPANSION RULE:
   - Include multiple examiner-accepted keywords per concept
   - Use synonyms or alternate academic terms in parentheses (e.g., "synchronization (also known as coordination)")
   - Add short keyword phrases that students can selectively memorize
   - Each major concept should have 2-3 related keywords or alternate phrasings
   - Use examiner-oriented phrasing:
     • "also known as" (e.g., "deadlock, also known as circular wait")
     • "commonly referred to as" (e.g., "commonly referred to as mutual exclusion")
     • "formally defined as" (e.g., "formally defined as a critical section")
     • "in academic literature" (e.g., "in academic literature, this is termed...")
   - Avoid casual or conversational tone completely—maintain formal academic tone throughout

5. KNOWLEDGE BASE REPRESENTATION RULE:
   - When explaining inference, reasoning, or knowledge bases:
     • Avoid LaTeX symbols like $, ∧, → unless absolutely necessary
     • Prefer plain English IF–THEN statements
     • Use readable variable names or explanations
   - Rewrite logic examples:
     • Replace formats like "$P ∧ Q → S$" with "IF P and Q are true, THEN S is true"
     • Replace "Facts: $P$, $Q$" with "Facts: P is true, Q is true"
   - Symbols are allowed ONLY when:
     • Explaining mathematical formulas explicitly
     • The question demands formal notation
   - Otherwise: Always prefer natural language logic
   - Example guidance:
     • BAD: Facts: $P$, $Q$ | Rule: $P ∧ Q → S$
     • GOOD: Facts: P is true, Q is true | Rule: IF P and Q are true, THEN S becomes true

6. REAL-WORLD EXAMPLE RULES:
   - Wherever the concept allows, include one simple real-world example
   - Examples must be intuitive and everyday (rain, traffic, exams, machines, medical diagnosis, etc.)
   - Use clear IF–THEN or step-wise reasoning
   - Label clearly as: "Real-World Example:"
   - These examples are ADDITIONAL and do NOT count toward the main word limit (280-350 words)
   - Examples should help students understand the concept intuitively
   - Do NOT add fluff stories—keep examples concise and relevant
   - Example guidance:
     • Forward/Backward chaining → rain, wet ground, grass growth
     • Search algorithms → route planning / maps
     • Heuristics → choosing shortest queue
     • Agents → robot vacuum / self-driving car

7. EXAMINER KEYWORD RULES:
   - Use commonly accepted academic terms from standard textbooks
   - Repeat core keywords naturally (2-3 times per major section) without sounding repetitive
   - Avoid casual or conversational language—maintain formal academic tone
   - Prefer definitions and formal phrasing over casual explanations
   - Use standard MU exam terminology (e.g., "process", "mechanism", "principle", "algorithm", "technique")
   - Include examiner-visible phrases like "fundamental concept", "key characteristic", "primary advantage", "essential component"

8. LANGUAGE RULES:
   - Simple, clear English suitable for undergraduate level
   - Write like a Mumbai University topper—formal, precise, keyword-rich
   - No fluff or unnecessary words—avoid repetition for the sake of length
   - No emojis or symbols
   - Direct and concise but with adequate depth
   - Use active voice where possible, but maintain formal tone
   - Avoid contractions (use "does not" instead of "doesn't")
   - Extra words must add value: prefer clarification, definition reinforcement, or short examples over filler sentences

9. FORMATTING:
   - Use **bold** for technical terms
   - Use $...$ for formulas (mathematical formulas only—avoid for logic/knowledge base representation)
   - Use bullet points for main content (primary format)
   - Use tables ONLY for comparison-type questions (see section 3)
   - Use clear section headers and subheadings for major points
   - Ensure each major point has a clear subheading when introducing new concepts
   - Do NOT introduce long paragraphs—maintain bullet-point format as primary

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
Write like a Mumbai University topper would—using standard textbook terminology, examiner-visible keywords, and formal academic phrasing.

Question:
{question}
{context_section}
REQUIREMENTS (STRICT):

1. WORD COUNT: 130-180 words exactly.

2. STRUCTURE (MANDATORY ORDER):
   
   a) DEFINITION (1-2 lines)
      - Clear, concise definition of the main concept using standard academic terminology
      - Bold key technical terms using **term**
      - Use formal phrasing and examiner-visible keywords
   
   b) KEY POINTS (5-7 bullet points, 1-2 lines each)
      - Use bullet points (• or -)
      - Write bullets so that each bullet can be independently memorized
      - Keep bullets concise (1-2 lines)—do NOT turn bullets into paragraphs
      - Each bullet should contain:
        • core definition
        • 1 alternate keyword/phrase (use synonyms or alternate academic terms in parentheses when appropriate)
        • formal textbook wording
      - To reach word count target: expand INSIDE existing bullets only
      - Each bullet may be expanded by one additional explanatory line or one additional examiner keyword phrase
      - Do NOT add new sections, new bullets, or long paragraphs to meet word count
      - Prefer clarification, definition reinforcement, or short examples within bullets
      - Each point should be brief but informative with adequate depth
      - Cover essential aspects only
      - Bold important terms using **term**
      - Use clear subheadings for each major point when introducing new concepts
      - Include explicit cause-effect phrasing where applicable
      - For algorithms: include step-wise explanation
   
   c) EXAMPLE OR DIAGRAM (choose ONE only)
      - Either provide a simple example (2-3 lines) using formal language
      - OR use format: [DIAGRAM: description] with formal terminology
      - Do NOT include both

   d) REAL-WORLD EXAMPLE (MANDATORY where applicable)
      - Include one simple real-world example if the concept allows
      - Examples must be intuitive and everyday (rain, traffic, exams, machines, medical diagnosis, etc.)
      - Use clear IF–THEN or step-wise reasoning
      - Label clearly as: "Real-World Example:"
      - These examples are ADDITIONAL and do NOT count toward the main word limit (130-180 words)
      - Keep examples concise, step-based, and easy to remember
      - Examples should help students understand the concept intuitively

3. COMPARISON QUESTION FORMATTING:
   - If the question contains: "Compare", "Differentiate", "Distinguish between", or similar comparison terms
   - Then present the core answer in a TABLE format
   - Table must have:
     Column 1: Basis (or "Aspect" or "Feature")
     Column 2: Concept A (name the first concept)
     Column 3: Concept B (name the second concept)
   - After the table, add a short real-world example (if applicable) labeled as "Real-World Example:"
   - Table should be clear, well-structured, and easy to scan
   - Use bullet-point format for non-comparison questions; tables ONLY for comparison-type questions

4. KEYWORD EXPANSION RULE:
   - Include multiple examiner-accepted keywords per concept
   - Use synonyms or alternate academic terms in parentheses (e.g., "synchronization (also known as coordination)")
   - Add short keyword phrases that students can selectively memorize
   - Each major concept should have 1-2 related keywords or alternate phrasings
   - Use examiner-oriented phrasing:
     • "also known as" (e.g., "deadlock, also known as circular wait")
     • "commonly referred to as" (e.g., "commonly referred to as mutual exclusion")
     • "formally defined as" (e.g., "formally defined as a critical section")
     • "in academic literature" (e.g., "in academic literature, this is termed...")
   - Avoid casual or conversational tone completely—maintain formal academic tone throughout

5. KNOWLEDGE BASE REPRESENTATION RULE:
   - When explaining inference, reasoning, or knowledge bases:
     • Avoid LaTeX symbols like $, ∧, → unless absolutely necessary
     • Prefer plain English IF–THEN statements
     • Use readable variable names or explanations
   - Rewrite logic examples:
     • Replace formats like "$P ∧ Q → S$" with "IF P and Q are true, THEN S is true"
     • Replace "Facts: $P$, $Q$" with "Facts: P is true, Q is true"
   - Symbols are allowed ONLY when:
     • Explaining mathematical formulas explicitly
     • The question demands formal notation
   - Otherwise: Always prefer natural language logic
   - Example guidance:
     • BAD: Facts: $P$, $Q$ | Rule: $P ∧ Q → S$
     • GOOD: Facts: P is true, Q is true | Rule: IF P and Q are true, THEN S becomes true

6. REAL-WORLD EXAMPLE RULES:
   - Wherever the concept allows, include one simple real-world example
   - Examples must be intuitive and everyday (rain, traffic, exams, machines, medical diagnosis, etc.)
   - Use clear IF–THEN or step-wise reasoning
   - Label clearly as: "Real-World Example:"
   - These examples are ADDITIONAL and do NOT count toward the main word limit (130-180 words)
   - Examples should help students understand the concept intuitively
   - Do NOT add fluff stories—keep examples concise and relevant
   - Example guidance:
     • Forward/Backward chaining → rain, wet ground, grass growth
     • Search algorithms → route planning / maps
     • Heuristics → choosing shortest queue
     • Agents → robot vacuum / self-driving car

7. EXAMINER KEYWORD RULES:
   - Use commonly accepted academic terms from standard textbooks
   - Repeat core keywords naturally (1-2 times) without sounding repetitive
   - Avoid casual or conversational language—maintain formal academic tone
   - Prefer definitions and formal phrasing over casual explanations
   - Use standard MU exam terminology (e.g., "process", "mechanism", "principle", "technique")
   - Include examiner-visible phrases like "key characteristic", "primary advantage", "essential component"

8. LANGUAGE RULES:
   - Simple, clear English suitable for undergraduate level
   - Write like a Mumbai University topper—formal, precise, keyword-rich
   - No fluff or unnecessary words—avoid repetition for the sake of length
   - No emojis or symbols
   - Direct and concise but with adequate depth
   - Use active voice where possible, but maintain formal tone
   - Avoid contractions (use "does not" instead of "doesn't")
   - Extra words must add value: prefer clarification, definition reinforcement, or short examples over filler sentences

9. FORMATTING:
   - Use **bold** for technical terms
   - Use bullet points for key points (primary format)
   - Use tables ONLY for comparison-type questions (see section 3)
   - Use clear subheadings for major points when applicable
   - Keep it brief and focused while maintaining depth
   - Do NOT introduce long paragraphs—maintain bullet-point format as primary

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
