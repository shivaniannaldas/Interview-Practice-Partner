import os
import uuid
from typing import Dict, List, Any

import requests

# -------- Groq config --------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Use a valid Groq model name you have access to:
GROQ_MODEL = "llama-3.3-70b-versatile"

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable not set")

# In-memory interview store
INTERVIEWS: Dict[str, Dict[str, Any]] = {}


def call_groq(messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
    """
    Simple wrapper to call Groq chat completions.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # Expect standard OpenAI/Groq style response
    return data["choices"][0]["message"]["content"].strip()


def _build_role_name(role: str, custom_role: str | None) -> str:
    if role == "Custom" and custom_role:
        return custom_role.strip()
    return role


def _system_prompt(
    role: str,
    experience: str,
    style: str,
    resume_summary: str | None = None,
) -> str:
    extra = ""
    if resume_summary:
        extra = (
            "\n\nHere is a summary of the candidate's resume and key skills:\n"
            f"{resume_summary}\n\n"
            "Use this to ask questions about their projects, responsibilities, tools and achievements."
        )

    return f"""
You are an intelligent but HUMAN-LIKE job interviewer for the role: {role}.
The candidate experience level is: {experience}.

Interviewer style: {style}.
- If style is 'Supportive', be friendly, encouraging, and add short positive reactions ("that's great", "nice example") before questions.
- If style is 'Strict', be concise, firm, and professional but not rude.

{extra}

Question strategy:
- Ask ONE question at a time.
- Keep each turn at most 2–3 sentences.
- Mix questions from three sources:
  1) The candidate's introduction and previous answers,
  2) Their resume and past projects (if available),
  3) Role-specific technical/behavioral questions for {role}.
- You can briefly acknowledge their last answer first (1 short sentence), then ask the next question.
- Do NOT give overall feedback during the interview. Feedback is only at the end.
""".strip()


def _history_text(qa: List[Dict[str, str]]) -> str:
    """
    Convert Q/A pairs to readable history.
    """
    out = []
    for i, pair in enumerate(qa, start=1):
        out.append(f"Q{i}: {pair['question']}\nA{i}: {pair['answer']}")
    return "\n\n".join(out)


def _needs_followup(answer: str) -> bool:
    """
    Heuristic to decide if we should ask a follow-up instead of moving on.
    """
    ans = answer.lower()
    if len(answer.split()) < 15:
        return True
    for phrase in ["don't know", "not sure", "no idea", "can't say"]:
        if phrase in ans:
            return True
    return False


def start_interview(
    role: str,
    custom_role: str | None,
    experience: str,
    style: str,
    max_questions: int | None,            # <-- allow None
    resume_text: str | None = None,
) -> Dict[str, str]:
    """
    Create new interview state and return interview_id + FIRST QUESTION.
    """
    role_name = _build_role_name(role, custom_role)

    # Optional: summarize resume once
    resume_summary = None
    if resume_text and resume_text.strip():
        messages = [
            {
                "role": "system",
                "content": "You are an expert career coach. Summarize resumes and extract key skills."
            },
            {
                "role": "user",
                "content": f"Here is the candidate's resume:\n\n{resume_text}\n\n"
                           "Summarize their profile in 4–6 bullet points and list their main skills."
            },
        ]
        resume_summary = call_groq(messages, temperature=0.3)

    # Build system prompt (used later in next_step)
    system_prompt = _system_prompt(role_name, experience, style, resume_summary)

    # First question: self-introduction (human style)
    intro_question = (
        "To begin, can you briefly introduce yourself and walk me through your background "
        "and the experiences you feel are most relevant to this role?"
    )

    # Interpret 0 or None as unlimited
    if max_questions is None or max_questions == 0:
        effective_max = 10**9   # very large = effectively unlimited
    else:
        effective_max = int(max_questions)

    interview_id = str(uuid.uuid4())
    INTERVIEWS[interview_id] = {
        "role": role_name,
        "experience": experience,
        "style": style,
        "max_questions": effective_max,   # <-- use effective_max here
        "qa": [],
        "current_question": intro_question,
        "done": False,
        "resume_summary": resume_summary,
        "candidate_name": None,    # <<-- ADD THIS LINE
    }

    return {"interview_id": interview_id, "question": intro_question}



def next_step(interview_id: str, answer: str | None, end: bool = False) -> Dict[str, Any]:
    """
    Process an answer and either return next question or final feedback.
    If end=True, finish early and generate feedback from current QA.
    """
    if interview_id not in INTERVIEWS:
        raise KeyError("Interview not found")

    state = INTERVIEWS[interview_id]
    if state["done"]:
        return {
            "done": True,
            "nextQuestion": None,
            "feedbackMarkdown": "Interview already finished.",
        }

    qa: List[Dict[str, str]] = state["qa"]
    current_q = state["current_question"]

    # Store answer
    if answer is not None and answer.strip() and current_q:
        qa.append({"question": current_q, "answer": answer.strip()})

    # Decide if we should end now
    if end or len(qa) >= state["max_questions"]:
    # Generate feedback (wrap in try to avoid exceptions bubbling up)
        try:
            feedback = _generate_feedback(state)
            if feedback is None:
                feedback = "No feedback available."
        except Exception as e:
            # If the feedback generator fails, return a safe message and log for debugging
            feedback = f"Feedback generation failed: {str(e)}"

        # Try to include candidate name if available for a friendlier closing
        candidate_name = state.get("candidate_name", "") or ""
        closing_msg = f"Thank you for your time{', ' + candidate_name if candidate_name else ''}. This concludes the interview."

        # mark interview done and clear current question
        state["done"] = True
        state["current_question"] = None

        # Return both the closing message (so UI can show it) and the feedback
        return {
            "done": True,
            "nextQuestion": closing_msg,
            "feedbackMarkdown": feedback,
        }


    # Build context for next question
    history = _history_text(qa)
    role_name = state["role"]
    experience = state["experience"]
    style = state["style"]
    resume_summary = state.get("resume_summary")
    system_prompt = _system_prompt(role_name, experience, style, resume_summary)

    last_answer = qa[-1]["answer"] if qa else ""
    followup = _needs_followup(last_answer)

    # User message to Groq
    if len(qa) == 1:
        # Just finished intro answer — force resume-based follow-ups when resume is present
        user_msg = f"""
Here is the candidate's self-introduction and first answer:

{history}

Resume summary (if provided):
{resume_summary if resume_summary else "No resume provided."}

As a human interviewer:
- Begin with one brief acknowledgement of their introduction (1 short sentence, e.g., "Thanks for sharing that.").
- THEN, if a resume summary is present, ask TWO targeted follow-up questions that explicitly reference items from the resume (project names, certifications, tools, or specific results).
  Example phrasings:
    "Your resume says you worked on <project name> — can you describe your role and the main technical challenge?"
    "I see you used <tool/tech> on that project; which part did you implement and how did you measure success?"
- If NO resume was provided, ask ONE role-relevant follow-up question instead.
Keep each question short (1–2 sentences). Do NOT provide feedback or extra commentary.
""".strip()

    else:
        if followup:
            user_msg = f"""
Here is the interview so far:

{history}

The candidate's last answer seems short or uncertain.

As a human interviewer:
- Start with a very brief reaction to their last answer (1 short sentence).
- Then ask ONE follow-up question that digs deeper into the SAME topic.
- If relevant, tie it to their resume or previous answers.
Total 1–2 sentences. No overall feedback.
""".strip()
        else:
            user_msg = f"""
Here is the interview so far:

{history}

Now, as a human interviewer for {role_name}:
- Start with a very brief acknowledgment of the last answer (1 short sentence).
- Then ask the NEXT interview question.
- Mix focus between:
  1) their resume / past projects (if you have resume summary),
  2) skills needed for {role_name},
  3) general behavioral questions (teamwork, challenges, learning, etc.).
Ask only ONE question this turn. Total 1–2 sentences. No overall feedback.
""".strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]
    next_q = call_groq(messages, temperature=0.7)
    state["current_question"] = next_q

    return {"done": False, "nextQuestion": next_q, "feedbackMarkdown": None}


def _generate_feedback(state: Dict[str, Any]) -> str:
    """
    Generate structured feedback from full QA transcript.
    Returns PLAIN TEXT with emoji section headers (no markdown symbols).
    This version safely extracts fields from `state` to avoid NameError and
    wraps model calls so errors return a readable message instead of raising.
    """
    # Safely extract fields from state
    role_name = state.get("role", "")
    experience = state.get("experience", "")
    style = state.get("style", "")
    resume_summary = state.get("resume_summary", "") or ""
    candidate_name = state.get("candidate_name", "") or ""
    qa = state.get("qa", [])

    history = _history_text(qa)

    resume_part = ""
    if resume_summary:
        resume_part = (
            "\n\nHere is a summary of the candidate's resume and key skills:\n"
            f"{resume_summary}\n"
        )

    system_prompt = f"""
You are a REAL human interviewer conducting a professional job interview.
Your tone must be natural, concise, human-like, and role-appropriate.

#############################################
###  HARD BANNED PHRASES (DO NOT USE EVER) ###
#############################################

Under NO circumstances should you use ANY sentences like:

- “This will help me understand…” 
- “This might help me understand…” 
- “This helps us evaluate…” 
- “Let’s explore that together…” 
- “I want to know…” 
- “This will give me insight…” 
- “This might help…” 
- “Let’s break it down…”

If you accidentally produce a sentence that resembles ANY of these patterns,
IMMEDIATELY rewrite the line in a clean, human way WITHOUT explaining anything.

#############################################

CANDIDATE DETAILS:
- Name: {candidate_name}
- Role: {role_name}
- Experience: {experience}
- Style: {style}
- Resume: {resume_summary}

GREETING:
- Start with a simple greeting using the candidate’s name (if available).
- Example: “Hi {candidate_name}, nice to meet you. Let’s begin.”

QUESTION RULES:
- Ask ONE question at a time.
- Keep questions short and human.
- Never justify why you are asking the question.
- Never explain your evaluation process.
- Never use teacher-like, mentor-like, or coach-like phrasing.

FOLLOW-UP LOGIC:
- If the answer is unclear or short → ask a natural follow-up.
- If the candidate says “no”, “I don’t know”, or refuses:
    - Supportive mode → politely move on.
    - Strict mode → warn once, then move on.
- Do NOT repeat questions.

TONE RULES:
Supportive → warm, encouraging, light fillers (Alright, Got it, Sounds good)
Strict → crisp, minimal fillers, professional, firm

ROLE ADAPTATION:
Ask a mix of behavioral + technical questions based on:
- role
- resume (if provided)
- experience level

ENDING:
If this is the LAST question:
Say exactly:
“Thank you for your time, {candidate_name}. This concludes the interview.”

IMPORTANT:
This function must only GENERATE POST-INTERVIEW FEEDBACK.
Return plain text with emoji headers exactly as requested below.
""".strip()

    user_msg = f"""
Here is the full interview transcript (questions and candidate answers):

{history}

{resume_part}

Now provide feedback in plain text with CLEAR emoji section headers.
Follow exactly this structure and DO NOT add extra sections:

🎯 Overall Summary:
(one short paragraph about how the candidate did in general)

🗣️ Communication Skills (rate out of 10):
(one short paragraph, include a rating like "7/10" and why)

💻 Technical / Role Knowledge (rate out of 10):
(one short paragraph, include a rating and mention strengths/weaknesses)

🧩 Structure & Clarity of Answers (rate out of 10):
(one short paragraph on how well they structure answers, include rating)

📌 Use of Resume / Past Experience:
(one short paragraph about how well they connect their background to the role)

🚀 Top Suggestions to Improve:
Write 3–5 bullet points, each starting with "• ".
Each point should be a specific, practical suggestion.

Remember:
- No markdown (#, *, -) and no numbered lists like "1)". 
- Use exactly these emoji section headers.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    # Call the model but guard against exceptions so a readable fallback is returned.
    try:
        feedback_text = call_groq(messages, temperature=0.4)
        # If model returned something falsy, provide fallback
        if not feedback_text or not isinstance(feedback_text, str):
            return "No feedback generated by model."
        return feedback_text
    except Exception as e:
        # Return a clear fallback message (this will be shown in UI)
        return f"Feedback generation failed: {str(e)}"
