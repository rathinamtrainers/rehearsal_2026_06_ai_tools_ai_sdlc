from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import CurrentUser
from app.models import Quiz, Question, Attempt, QuestionType, AttemptStatus, utcnow, ensure_aware
from app.schemas import (
    QuizCreate, QuizResponse, QuestionCreate, QuestionResponse, 
    AttemptResponse, AnswerSubmit
)

router = APIRouter(prefix="/quizzes", tags=["quizzes"])
DbSession = Annotated[Session, Depends(get_db)]

@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(payload: QuizCreate, user: CurrentUser, db: DbSession):
    """Create a new quiz (instructor only)."""
    if user.role != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can create quizzes.")
    
    quiz = Quiz(
        title=payload.title,
        time_limit_minutes=payload.time_limit_minutes,
        passing_threshold=payload.passing_threshold,
        max_attempts=payload.max_attempts,
        created_by=user.id
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


@router.post("/{quiz_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(quiz_id: str, payload: QuestionCreate, user: CurrentUser, db: DbSession):
    """Add a question to a quiz (instructor only)."""
    if user.role != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can add questions.")
        
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    question = Question(
        quiz_id=quiz.id,
        question_text=payload.question_text,
        question_type=QuestionType(payload.question_type),
        options=payload.options,
        correct_option_id=payload.correct_option_id,
        is_true=payload.is_true
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: str, user: CurrentUser, db: DbSession):
    """Fetch quiz details and questions (without correct answers)."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    return quiz


@router.get("/{quiz_id}/attempts", response_model=list[AttemptResponse])
def get_attempts(quiz_id: str, user: CurrentUser, db: DbSession):
    """Fetch all attempts for the current learner for a given quiz."""
    attempts = db.query(Attempt).filter(Attempt.quiz_id == quiz_id, Attempt.user_id == user.id).all()
    return attempts


@router.post("/{quiz_id}/attempts", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
def start_attempt(quiz_id: str, user: CurrentUser, db: DbSession):
    """Start a new attempt for a quiz."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")
        
    if quiz.max_attempts is not None:
        attempts_count = db.query(Attempt).filter(Attempt.quiz_id == quiz_id, Attempt.user_id == user.id).count()
        if attempts_count >= quiz.max_attempts:
            raise HTTPException(status_code=403, detail="Maximum attempts reached.")
            
    attempt = Attempt(
        quiz_id=quiz.id,
        user_id=user.id,
        status=AttemptStatus.IN_PROGRESS
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.post("/{quiz_id}/attempts/{attempt_id}/submit", response_model=AttemptResponse)
def submit_attempt(quiz_id: str, attempt_id: str, payload: AnswerSubmit, user: CurrentUser, db: DbSession):
    """Submit answers for an attempt and grade it."""
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id, Attempt.quiz_id == quiz_id, Attempt.user_id == user.id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found.")
        
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Attempt is already completed.")
        
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")
        
    now = utcnow()
    
    final_status = AttemptStatus.COMPLETED
    if quiz.time_limit_minutes is not None:
        cutoff = ensure_aware(attempt.start_time) + timedelta(minutes=quiz.time_limit_minutes, seconds=30)
        if now > cutoff:
            final_status = AttemptStatus.TIMED_OUT

    # Grade the submission
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    total_questions = len(questions)
    if total_questions == 0:
        score = 100.0
        pass_status = True
    else:
        correct_count = 0
        for q in questions:
            ans = payload.answers.get(q.id)
            if ans is None:
                continue
            if q.question_type == QuestionType.MCQ:
                if str(ans) == str(q.correct_option_id):
                    correct_count += 1
            elif q.question_type == QuestionType.TRUE_FALSE:
                if bool(ans) == bool(q.is_true):
                    correct_count += 1
                    
        score = (correct_count / total_questions) * 100.0
        pass_status = score >= quiz.passing_threshold
        
    attempt.status = final_status
    attempt.end_time = now
    attempt.score = score
    attempt.pass_status = pass_status
    attempt.answers = payload.answers
    
    db.commit()
    db.refresh(attempt)
    return attempt
