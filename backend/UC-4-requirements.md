# UC-4 — Quiz & Assessment Engine — Requirements

> Generated with Gemini (gemini.google.com) from the one-line brief
> "Let instructors quiz learners and score them automatically," then refined for
> edge cases. Built on LearnFlow's existing JWT auth and `learner`/`instructor` roles.

---

## 1. User Stories

### Instructor (Quiz Creation & Management)
- **US-I1:** As an instructor, I want to create a new quiz module within a course so that I can evaluate learner comprehension.
- **US-I2:** As an instructor, I want to add Multiple Choice (MCQ) and True/False questions to my quiz so that I can build standardized assessments.
- **US-I3:** As an instructor, I want to configure quiz parameters (time limits, passing thresholds, and max attempts) so that I can control the difficulty and pacing of the assessment.
- **US-I4:** As an instructor, I want the system to automatically calculate scores upon learner submission so that I am freed from manual grading.

### Learner (Quiz Execution & Review)
- **US-L1:** As a learner, I want to view the quiz details (total questions, time limit, required passing score, remaining attempts) before starting so that I know what to expect.
- **US-L2:** As a learner, I want to see a persistent countdown timer on the screen during timed quizzes so that I can manage my time effectively.
- **US-L3:** As a learner, I want my score and pass/fail status displayed immediately upon submission so that I get instant feedback on my performance.
- **US-L4:** As a learner, I want to review my previous attempts (if permitted by settings) so that I can track my improvement.

---

## 2. Acceptance Criteria (Given/When/Then)

**Scenario 1: Enforcing the Passing Threshold and Auto-Scoring**
- **Given** an instructor has set the quiz passing threshold to 80%,
- **When** a learner submits the quiz with 4 out of 5 correct answers (80%),
- **Then** the FastAPI backend must calculate the score,
- **And** the React frontend must display a "Passed" status alongside the final score,
- **And** the system must record the attempt as successful in the database.

**Scenario 2: Time Limit Enforcement & Auto-Submission**
- **Given** a learner is taking a quiz with a 15-minute time limit,
- **When** the frontend countdown timer reaches 00:00,
- **Then** the React application must automatically disable all input fields,
- **And** force a POST request to the backend to submit the current state of selected answers,
- **And** the backend must accept and grade the partial submission.

**Scenario 3: Maximum Attempt Limits**
- **Given** a quiz is configured for a maximum of 2 attempts,
- **When** a learner completes their first attempt and fails,
- **Then** the React UI should display a "Retake Quiz" button.
- **But When** the learner completes their second attempt,
- **Then** the backend must reject any further attempt requests (returning `403 Forbidden` or `400 Bad Request`),
- **And** the frontend must hide or disable the "Retake Quiz" button, displaying "Maximum attempts reached."

---

## 3. Business Requirements Document (BRD) Extract

### 3.1 Overview
The Quiz & Assessment Engine allows instructors to create auto-graded assessments. The module relies on the existing JWT authentication for role-based access control (RBAC): only users with the `instructor` role can create/edit quizzes, while users with the `learner` role can execute them.

### 3.2 Question Types
The MVP supports two closed-ended, auto-gradable question types.

| Question Type | Description | Data (FastAPI/JSON context) |
| --- | --- | --- |
| **Multiple Choice (MCQ)** | A question with 2–5 distinct options, exactly **one** correct. | `question_text`, `options` array, `correct_option_id`. |
| **True/False** | A binary choice question. | `question_text`, boolean `is_true` correct answer. |

### 3.3 Quiz Configuration & Rules
- **Scoring:** each question carries equal weight of 1 point (MVP). Total score = `(Correct Answers / Total Questions) * 100`.
- **Passing Threshold:** an integer percentage `0`–`100`. Score `>=` threshold → attempt marked `Passed`.
- **Attempts:** an integer (e.g. 1, 2, 3) or `null`/`0` for unlimited. When multiple attempts are allowed, the **highest score** is the final grade for the module.
- **Timing:** time limit in minutes; `0`/`null` = untimed. *Implementation note:* the frontend timer is UX only — the backend must validate `start_time`/`end_time` of the submission (allow a 30-second network-latency buffer) to prevent client-side timer manipulation.

### 3.4 State Management & API Flow
1. **Start:** client calls the create-attempt endpoint (requires JWT); backend initializes the attempt and returns a timestamp.
2. **Execution:** learner selects answers; state held locally in React (optional periodic auto-save out of MVP scope).
3. **Submission:** client submits the answer payload.
4. **Evaluation:** backend compares the submission against the server-side answer key, computes the percentage, checks the threshold, updates the attempt record, and returns the graded payload.

> **Security rule (house convention):** the questions-fetch response must **never** include the correct-answer fields (`correct_option_id` / `is_true`). The answer key stays server-side; grading happens on the backend only.

---

## 4. Edge Cases (with Acceptance Criteria)

**EC-1: Timer expires mid-attempt**
- **Given** a learner is actively taking a timed quiz with only some answers selected,
- **When** the frontend timer reaches `00:00` OR the backend detects the timestamp exceeds `end_time` plus a 30-second buffer,
- **Then** the frontend disables all inputs and auto-submits the current state,
- **And** the backend accepts the partial payload, grades provided answers, and assigns 0 to unsubmitted/null answers.

**EC-2: Partial answers (blanks left)**
- **Given** a learner leaves one or more questions blank,
- **When** they click Submit,
- **Then** the frontend warns "You have unanswered questions. Are you sure?",
- **And When** they confirm,
- **Then** the backend grades provided answers and assigns 0 to missing `question_id` keys,
- **And** the percentage denominator remains the total number of questions, not just the answered ones.

**EC-3: Re-attempt limit reached (API level)**
- **Given** the attempt limit is 2 and the learner has completed 2 attempts,
- **When** a create-attempt request is sent with the learner's JWT,
- **Then** the backend evaluates attempt history, blocks the new attempt, and returns `403 Forbidden` (or `409 Conflict`) with an error message,
- **And** the frontend catches the error, disables the Start button, and shows "Maximum attempts reached."

**EC-4: Score exactly on the pass threshold**
- **Given** the passing threshold is exactly 80%,
- **When** the backend calculates a final score of exactly 80.00%,
- **Then** the evaluation uses an inclusive `>=` operator,
- **And** marks `pass_status = True`,
- **And** the frontend renders the "Passed" success state.
