import pytest
from app.models import User, UserRole

def get_instructor_token(client, db, email="instructor@test.com"):
    from tests.conftest import register, login
    register(client, email)
    # Promote to instructor
    user = db.query(User).filter(User.email == email).first()
    user.role = UserRole.instructor
    db.commit()
    r = login(client, email)
    return r.json()["access_token"]

def get_learner_token(client, db, email="learner@test.com"):
    from tests.conftest import register, login
    register(client, email)
    r = login(client, email)
    return r.json()["access_token"]


def test_instructor_can_create_quiz_and_questions(client, db):
    token = get_instructor_token(client, db)
    headers = {"Authorization": f"Bearer {token}"}
    
    r = client.post("/quizzes", json={
        "title": "Math Quiz",
        "time_limit_minutes": 15,
        "passing_threshold": 50,
        "max_attempts": 2
    }, headers=headers)
    assert r.status_code == 201
    quiz_id = r.json()["id"]
    
    r = client.post(f"/quizzes/{quiz_id}/questions", json={
        "question_text": "2+2=?",
        "question_type": "MCQ",
        "options": {"A": "3", "B": "4"},
        "correct_option_id": "B"
    }, headers=headers)
    assert r.status_code == 201
    assert "correct_option_id" not in r.json()


def test_learner_cannot_create_quiz(client, db):
    token = get_learner_token(client, db)
    headers = {"Authorization": f"Bearer {token}"}
    
    r = client.post("/quizzes", json={"title": "Math Quiz"}, headers=headers)
    assert r.status_code == 403


def test_fetch_quiz_does_not_leak_answers(client, db):
    i_token = get_instructor_token(client, db)
    i_headers = {"Authorization": f"Bearer {i_token}"}
    
    r = client.post("/quizzes", json={"title": "Q"}, headers=i_headers)
    quiz_id = r.json()["id"]
    
    client.post(f"/quizzes/{quiz_id}/questions", json={
        "question_text": "True?",
        "question_type": "TRUE_FALSE",
        "is_true": True
    }, headers=i_headers)
    
    l_token = get_learner_token(client, db)
    l_headers = {"Authorization": f"Bearer {l_token}"}
    
    r = client.get(f"/quizzes/{quiz_id}", headers=l_headers)
    assert r.status_code == 200
    quiz = r.json()
    q = quiz["questions"][0]
    assert "is_true" not in q
    assert "correct_option_id" not in q


def test_scoring_and_threshold(client, db):
    i_token = get_instructor_token(client, db)
    i_headers = {"Authorization": f"Bearer {i_token}"}
    
    r = client.post("/quizzes", json={"title": "Q", "passing_threshold": 80}, headers=i_headers)
    quiz_id = r.json()["id"]
    
    r = client.post(f"/quizzes/{quiz_id}/questions", json={"question_text": "Q1", "question_type": "TRUE_FALSE", "is_true": True}, headers=i_headers)
    q1_id = r.json()["id"]
    r = client.post(f"/quizzes/{quiz_id}/questions", json={"question_text": "Q2", "question_type": "MCQ", "options": {"A":"1","B":"2"}, "correct_option_id": "A"}, headers=i_headers)
    q2_id = r.json()["id"]
    r = client.post(f"/quizzes/{quiz_id}/questions", json={"question_text": "Q3", "question_type": "TRUE_FALSE", "is_true": False}, headers=i_headers)
    q3_id = r.json()["id"]
    r = client.post(f"/quizzes/{quiz_id}/questions", json={"question_text": "Q4", "question_type": "TRUE_FALSE", "is_true": False}, headers=i_headers)
    q4_id = r.json()["id"]
    r = client.post(f"/quizzes/{quiz_id}/questions", json={"question_text": "Q5", "question_type": "TRUE_FALSE", "is_true": False}, headers=i_headers)
    q5_id = r.json()["id"]

    l_token = get_learner_token(client, db)
    l_headers = {"Authorization": f"Bearer {l_token}"}
    
    r = client.post(f"/quizzes/{quiz_id}/attempts", headers=l_headers)
    attempt_id = r.json()["id"]
    
    r = client.post(f"/quizzes/{quiz_id}/attempts/{attempt_id}/submit", json={
        "answers": {
            q1_id: True,
            q2_id: "A",
            q3_id: False,
            q4_id: False,
            q5_id: True # wrong
        }
    }, headers=l_headers)
    assert r.status_code == 200
    res = r.json()
    assert res["score"] == 80.0
    assert res["pass_status"] is True


def test_exceeding_max_attempts(client, db):
    i_token = get_instructor_token(client, db)
    i_headers = {"Authorization": f"Bearer {i_token}"}
    r = client.post("/quizzes", json={"title": "Q", "max_attempts": 1}, headers=i_headers)
    quiz_id = r.json()["id"]

    l_token = get_learner_token(client, db)
    l_headers = {"Authorization": f"Bearer {l_token}"}
    
    r = client.post(f"/quizzes/{quiz_id}/attempts", headers=l_headers)
    assert r.status_code == 201
    
    r = client.post(f"/quizzes/{quiz_id}/attempts", headers=l_headers)
    assert r.status_code == 403


def test_partial_grading(client, db):
    i_token = get_instructor_token(client, db)
    i_headers = {"Authorization": f"Bearer {i_token}"}
    r = client.post("/quizzes", json={"title": "Q", "passing_threshold": 50}, headers=i_headers)
    quiz_id = r.json()["id"]
    
    r = client.post(f"/quizzes/{quiz_id}/questions", json={"question_text": "Q1", "question_type": "TRUE_FALSE", "is_true": True}, headers=i_headers)
    q1_id = r.json()["id"]
    r = client.post(f"/quizzes/{quiz_id}/questions", json={"question_text": "Q2", "question_type": "TRUE_FALSE", "is_true": True}, headers=i_headers)
    q2_id = r.json()["id"]

    l_token = get_learner_token(client, db)
    l_headers = {"Authorization": f"Bearer {l_token}"}
    r = client.post(f"/quizzes/{quiz_id}/attempts", headers=l_headers)
    attempt_id = r.json()["id"]
    
    r = client.post(f"/quizzes/{quiz_id}/attempts/{attempt_id}/submit", json={
        "answers": {
            q1_id: True
        }
    }, headers=l_headers)
    assert r.status_code == 200
    res = r.json()
    assert res["score"] == 50.0
    assert res["pass_status"] is True


def test_timed_out_submission(client, db):
    from datetime import timedelta
    from app.models import Attempt, utcnow
    
    i_token = get_instructor_token(client, db)
    i_headers = {"Authorization": f"Bearer {i_token}"}
    r = client.post("/quizzes", json={"title": "Timed Q", "time_limit_minutes": 5, "passing_threshold": 100}, headers=i_headers)
    quiz_id = r.json()["id"]
    
    r = client.post(f"/quizzes/{quiz_id}/questions", json={"question_text": "Q1", "question_type": "TRUE_FALSE", "is_true": True}, headers=i_headers)
    q1_id = r.json()["id"]

    l_token = get_learner_token(client, db)
    l_headers = {"Authorization": f"Bearer {l_token}"}
    r = client.post(f"/quizzes/{quiz_id}/attempts", headers=l_headers)
    attempt_id = r.json()["id"]
    
    # Backdate the attempt start_time to 6 minutes ago (past the 5min limit + 30s buffer)
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    attempt.start_time = utcnow() - timedelta(minutes=6)
    db.commit()
    
    r = client.post(f"/quizzes/{quiz_id}/attempts/{attempt_id}/submit", json={
        "answers": {
            q1_id: True
        }
    }, headers=l_headers)
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "TIMED_OUT"
    assert res["score"] == 100.0  # Graded successfully
    assert res["pass_status"] is True
