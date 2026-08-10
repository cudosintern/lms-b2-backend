# Student Quiz routes - student-facing endpoints for My Quiz feature
# These wrap the existing manage-quiz student endpoints into a dedicated student prefix.
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess, returnException
from datetime import datetime
from typing import Optional, Any
from .student_quiz_schema import StudentQuizSubmitRequest

router = APIRouter(tags=["Student Quiz"])


# ── My Quizzes: list all quizzes shared to this student ──────────────────────
@router.get("/my-quizzes")
def get_student_quizzes(
    student_id: int = Query(..., description="student_id of the logged-in student"),
    academic_batch_id: Optional[int] = Query(default=None),
    semester_id: Optional[int] = Query(default=None),
    crs_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    filters = "WHERE qs.ssd_id = :student_id"
    params: dict[str, Any] = {"student_id": student_id}

    if academic_batch_id is not None:
        filters += " AND q.academic_batch_id = :academic_batch_id"
        params["academic_batch_id"] = academic_batch_id
    if semester_id is not None:
        filters += " AND q.semester_id = :semester_id"
        params["semester_id"] = semester_id
    if crs_id is not None:
        filters += " AND q.crs_id = :crs_id"
        params["crs_id"] = crs_id

    query = f"""
        SELECT
            qs.qs_map_id,
            qs.quiz_id,
            qs.ssd_id,
            qs.student_usn,
            qs.q_secured_marks,
            qs.secured_marks,
            qs.is_submitted,
            qs.accept_rework_flag,
            qs.rework_comment,
            qs.remarks,
            q.quiz_title,
            q.quiz_description,
            q.quiz_instruction,
            q.quiz_date,
            q.quiz_time,
            q.duration,
            q.marks_flag,
            q.practice_quiz,
            q.file_name,
            q.file_path,
            COALESCE(c.crs_code, '') AS crs_code,
            COALESCE(c.crs_title, '') AS crs_title,
            (SELECT COUNT(*) FROM lms_quiz_questions qq WHERE qq.quiz_id = q.quiz_id) AS question_count,
            (SELECT COUNT(*) FROM lms_quiz_student_answer qa
             WHERE qa.quiz_id = q.quiz_id AND qa.ssd_id = qs.ssd_id) AS answered_count
        FROM lms_quiz_student_mapping qs
        JOIN lms_manage_quiz q ON q.quiz_id = qs.quiz_id
        LEFT JOIN iems_courses c ON c.crs_id = q.crs_id
        {filters}
        ORDER BY qs.quiz_id DESC
    """
    rows = db.execute(text(query), params).mappings().all()
    return returnSuccess({"items": [dict(r) for r in rows], "total": len(rows)})


# ── Start Quiz: log start and return questions ────────────────────────────────
@router.post("/{quiz_id}/start")
def start_student_quiz(
    quiz_id: int,
    ssd_id: int = Query(...),
    student_usn: str = Query(...),
    db: Session = Depends(get_db),
):
    quiz = db.execute(
        text("SELECT * FROM lms_manage_quiz WHERE quiz_id = :quiz_id"),
        {"quiz_id": quiz_id},
    ).mappings().first()
    if not quiz:
        return returnException("Quiz not found")

    mapping = db.execute(
        text("SELECT * FROM lms_quiz_student_mapping WHERE quiz_id = :quiz_id AND ssd_id = :ssd_id"),
        {"quiz_id": quiz_id, "ssd_id": ssd_id},
    ).mappings().first()
    if not mapping:
        return returnException("You are not enrolled in this quiz")

    # Log start (non-fatal)
    try:
        existing_log = db.execute(
            text("SELECT quiz_log_id FROM lms_quiz_start_log WHERE quiz_id = :quiz_id AND ssd_id = :ssd_id LIMIT 1"),
            {"quiz_id": quiz_id, "ssd_id": ssd_id},
        ).first()
        if not existing_log:
            db.execute(
                text("""
                    INSERT INTO lms_quiz_start_log
                        (quiz_id, ssd_id, student_usn, quiz_from_web, quiz_start_datetime, created_datetime)
                    VALUES (:quiz_id, :ssd_id, :student_usn, 1, :start_dt, :start_dt)
                """),
                {
                    "quiz_id": quiz_id,
                    "ssd_id": ssd_id,
                    "student_usn": student_usn,
                    "start_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
            db.commit()
    except Exception:
        pass

    # Fetch questions with options and previously given answers
    questions_rows = db.execute(
        text("""
            SELECT qq.qq_id, qq.question, qq.question_type, qq.marks
            FROM lms_quiz_questions qq
            WHERE qq.quiz_id = :quiz_id
            ORDER BY qq.qq_id ASC
        """),
        {"quiz_id": quiz_id},
    ).mappings().all()

    result = []
    for q in questions_rows:
        q_dict = dict(q)
        options = db.execute(
            text("""
                SELECT qq_option_id, option_value, option_explanation
                FROM lms_quiz_que_options
                WHERE qq_id = :qq_id
                ORDER BY qq_option_id ASC
            """),
            {"qq_id": q_dict["qq_id"]},
        ).mappings().all()
        q_dict["options"] = [dict(o) for o in options]

        # Pre-fill already answered option
        answered = db.execute(
            text("""
                SELECT qq_option_id FROM lms_quiz_student_answer
                WHERE quiz_id = :quiz_id AND ssd_id = :ssd_id AND qq_id = :qq_id
                LIMIT 1
            """),
            {"quiz_id": quiz_id, "ssd_id": ssd_id, "qq_id": q_dict["qq_id"]},
        ).first()
        q_dict["selected_option_id"] = answered[0] if answered else None
        result.append(q_dict)

    return returnSuccess({
        "quiz": dict(quiz),
        "questions": result,
    })


# ── Submit Quiz: save answers and mark as submitted ───────────────────────────
@router.post("/{quiz_id}/submit")
def submit_student_quiz(quiz_id: int, payload: StudentQuizSubmitRequest, db: Session = Depends(get_db)):
    mapping = db.execute(
        text("SELECT * FROM lms_quiz_student_mapping WHERE quiz_id = :quiz_id AND ssd_id = :ssd_id"),
        {"quiz_id": quiz_id, "ssd_id": payload.ssd_id},
    ).mappings().first()
    if not mapping:
        return returnException("You are not enrolled in this quiz")

    try:
        for ans in payload.answers:
            # Skip unanswered questions (qq_option_id is None)
            if ans.qq_option_id is None:
                continue

            # Upsert: delete existing answer for this question then insert fresh
            db.execute(
                text("DELETE FROM lms_quiz_student_answer WHERE quiz_id=:qid AND ssd_id=:sid AND qq_id=:qqid"),
                {"qid": quiz_id, "sid": payload.ssd_id, "qqid": ans.qq_id},
            )
            db.execute(
                text("""
                    INSERT INTO lms_quiz_student_answer
                        (quiz_id, ssd_id, student_usn, qq_id, qq_option_id, created_by, created_date)
                    VALUES (:quiz_id, :ssd_id, :student_usn, :qq_id, :qq_option_id, 0, :now)
                """),
                {
                    "quiz_id": quiz_id,
                    "ssd_id": payload.ssd_id,
                    "student_usn": payload.student_usn or "",
                    "qq_id": ans.qq_id,
                    "qq_option_id": ans.qq_option_id,
                    "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

        # Mark as submitted regardless of how many questions were answered
        db.execute(
            text("UPDATE lms_quiz_student_mapping SET is_submitted=1 WHERE quiz_id=:qid AND ssd_id=:sid"),
            {"qid": quiz_id, "sid": payload.ssd_id},
        )

        # ── Auto-calculate score ──────────────────────────────────────────────
        # Count marks for each correct answer the student selected
        score_rows = db.execute(
            text("""
                SELECT COALESCE(SUM(qq.marks), 0) AS total_score
                FROM lms_quiz_student_answer sa
                JOIN lms_quiz_questions_options opt
                    ON opt.qq_option_id = sa.qq_option_id
                JOIN lms_quiz_questions qq
                    ON qq.qq_id = sa.qq_id
                WHERE sa.quiz_id = :quiz_id
                  AND sa.ssd_id  = :ssd_id
                  AND opt.is_answer = 1
            """),
            {"quiz_id": quiz_id, "ssd_id": payload.ssd_id},
        ).mappings().first()

        total_score = float(score_rows["total_score"]) if score_rows else 0.0

        db.execute(
            text("""
                UPDATE lms_quiz_student_mapping
                SET secured_marks = :score
                WHERE quiz_id = :quiz_id AND ssd_id = :ssd_id
            """),
            {"score": total_score, "quiz_id": quiz_id, "ssd_id": payload.ssd_id},
        )

        db.commit()
        return returnSuccess({"quiz_id": quiz_id, "ssd_id": payload.ssd_id, "score": total_score}, "Quiz submitted successfully")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to submit quiz: {str(exc)}")


# ── Download quiz file ────────────────────────────────────────────────────────
@router.get("/{quiz_id}/file")
def download_quiz_file(quiz_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    quiz = db.execute(
        text("SELECT file_name, file_path FROM lms_manage_quiz WHERE quiz_id = :quiz_id"),
        {"quiz_id": quiz_id},
    ).mappings().first()
    if not quiz or not quiz["file_path"]:
        return returnException("File not found")
    import os
    if not os.path.exists(quiz["file_path"]):
        return returnException("File not found on server")
    return FileResponse(path=quiz["file_path"], filename=quiz["file_name"])
