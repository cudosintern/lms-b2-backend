from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnException, returnSuccess

from app.db.models import (
    IEMSCourses,
    IEMSection,
    CudosTopic,
    IEMSAcademicBatch,
    IEMSemester,
    LMSMapInstructorTopic,
    TopicLessonSchedule,
    LMSMapPortionLS,
    IEMSUsers,
    LMSLessonSchedule,  # Added for section filtering
    CudosMapCoursetoCourseInstructor,  # Added back for the Instructor/Handled By column
    MasterTypeDetails,
    MasterType
)

router = APIRouter(tags=["Manage Quiz"])


# Carries option data for quiz questions.
class QuizQuestionOptionItem(BaseModel):
    option_value: Optional[str] = None
    is_answer: int = 0
    explanation: Optional[str] = None


# Carries payload for creating a quiz.
class QuizCreateRequest(BaseModel):
    quiz_title: str = Field(..., min_length=1)
    quiz_instruction: Optional[str] = None
    quiz_description: Optional[str] = None
    academic_batch_id: Optional[int] = None
    semester_id: Optional[int] = None
    crs_id: Optional[int] = None
    quiz_date: Optional[str] = None
    quiz_time: Optional[str] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    marks_flag: int = 0
    co_map_flag: int = 0
    bl_map_flag: int = 0
    practice_quiz: int = 0
    shuffle_questions: int = 0
    shuffle_options: int = 0
    answer_key_share_flag: int = 0
    status: int = 1
    created_by: int
    section_ids: list[int] = Field(default_factory=list)
    topic_ids: list[int] = Field(default_factory=list)
    show_date: Optional[str] = None
    show_time: Optional[str] = None


# Carries payload for updating an existing quiz.
class QuizUpdateRequest(BaseModel):
    quiz_title: Optional[str] = None
    quiz_instruction: Optional[str] = None
    quiz_description: Optional[str] = None
    academic_batch_id: Optional[int] = None
    semester_id: Optional[int] = None
    crs_id: Optional[int] = None
    quiz_date: Optional[str] = None
    quiz_time: Optional[str] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    marks_flag: Optional[int] = None
    co_map_flag: Optional[int] = None
    bl_map_flag: Optional[int] = None
    practice_quiz: Optional[int] = None
    shuffle_questions: Optional[int] = None
    shuffle_options: Optional[int] = None
    answer_key_share_flag: Optional[int] = None
    status: Optional[int] = None
    modified_by: int
    section_ids: Optional[list[int]] = None
    topic_ids: Optional[list[int]] = None
    show_date: Optional[str] = None
    show_time: Optional[str] = None


# Carries payload for creating a quiz question.
class QuizQuestionCreateRequest(BaseModel):
    main_que_code: Optional[str] = None
    sub_que_code: Optional[str] = None
    question: str = Field(..., min_length=1)
    question_type: int
    marks: Optional[int] = None
    created_by: int
    options: list[QuizQuestionOptionItem] = Field(default_factory=list)
    clo_ids: list[int] = Field(default_factory=list)
    bloom_ids: list[int] = Field(default_factory=list)


# Carries payload for updating a quiz question.
class QuizQuestionUpdateRequest(BaseModel):
    main_que_code: Optional[str] = None
    sub_que_code: Optional[str] = None
    question: Optional[str] = None
    question_type: Optional[int] = None
    marks: Optional[int] = None
    modified_by: int
    options: Optional[list[QuizQuestionOptionItem]] = None
    clo_ids: Optional[list[int]] = None
    bloom_ids: Optional[list[int]] = None


# Carries payload for sharing a quiz with students.
class QuizShareRequest(BaseModel):
    created_by: int


# Returns available columns for a given table.
def _get_table_columns(db: Session, table_name: str) -> set[str]:
    rows = db.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    ).fetchall()
    return {row[0] for row in rows}


# Checks if a database routine exists in the active schema.
def _routine_exists(db: Session, routine_name: str) -> bool:
    exists = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.routines
            WHERE routine_schema = DATABASE() AND routine_name = :routine_name
            """
        ),
        {"routine_name": routine_name},
    ).scalar()
    return bool(exists)


# Selects the first matching value from a row using fallback column names.
def _pick_value(row: dict[str, Any], candidates: list[str]) -> Any:
    for key in candidates:
        if key in row and row[key] is not None:
            return row[key]
    return None


# Builds an insert query using only columns that exist in the target table.
def _dynamic_insert(db: Session, table_name: str, payload: dict[str, Any]) -> int:
    columns = _get_table_columns(db, table_name)
    data = {key: value for key, value in payload.items() if key in columns and value is not None}
    if not data:
        raise ValueError(f"No matching insert columns found for {table_name}")

    sql = f"INSERT INTO {table_name} ({', '.join(data.keys())}) VALUES ({', '.join(f':{key}' for key in data.keys())})"
    result = db.execute(text(sql), data)
    return int(result.lastrowid or 0)


# Builds an update query using only columns that exist in the target table.
def _dynamic_update(db: Session, table_name: str, key_column: str, key_value: int, payload: dict[str, Any]) -> None:
    columns = _get_table_columns(db, table_name)
    data = {key: value for key, value in payload.items() if key in columns and value is not None}
    if not data:
        return

    set_clause = ", ".join(f"{key} = :{key}" for key in data.keys())
    data[key_column] = key_value
    db.execute(text(f"UPDATE {table_name} SET {set_clause} WHERE {key_column} = :{key_column}"), data)


# Checks whether a quiz has any start log entries.
def _quiz_has_started(db: Session, quiz_id: int) -> bool:
    return bool(
        db.execute(
            text("SELECT COUNT(*) FROM lms_quiz_start_log WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id},
        ).scalar()
        or 0
    )


# Fetches section mapping ids for a quiz.
def _fetch_quiz_section_ids(db: Session, quiz_id: int) -> list[int]:
    rows = db.execute(
        text("SELECT * FROM lms_quiz_section_mapping WHERE quiz_id = :quiz_id"),
        {"quiz_id": quiz_id},
    ).mappings().all()
    result = []
    for row in rows:
        section_id = _pick_value(dict(row), ["section_id", "sec_id", "id"])
        if section_id is not None:
            result.append(int(section_id))
    return result


# Fetches topic mapping ids for a quiz.
def _fetch_quiz_topic_ids(db: Session, quiz_id: int) -> list[int]:
    rows = db.execute(
        text("SELECT * FROM lms_quiz_topic_mapping WHERE quiz_id = :quiz_id"),
        {"quiz_id": quiz_id},
    ).mappings().all()
    result = []
    for row in rows:
        topic_id = _pick_value(dict(row), ["topic_id"])
        if topic_id is not None:
            result.append(int(topic_id))
    return result


# Fetches options for a quiz question with function fallback support.
def _fetch_question_options(db: Session, quiz_id: int, qq_id: int) -> list[dict[str, Any]]:
    if _routine_exists(db, "lms_fetch_quiz_que_options_explanations"):
        rows = db.execute(
            text("SELECT * FROM lms_fetch_quiz_que_options_explanations(:quiz_id, :qq_id)"),
            {"quiz_id": quiz_id, "qq_id": qq_id},
        ).mappings().all()
        return [dict(row) for row in rows]

    rows = db.execute(
        text("SELECT * FROM lms_quiz_que_options WHERE quiz_id = :quiz_id AND qq_id = :qq_id ORDER BY qq_option_id ASC"),
        {"quiz_id": quiz_id, "qq_id": qq_id},
    ).mappings().all()
    return [dict(row) for row in rows]


# Fetches CLO mapping ids for a quiz question with function fallback support.
def _fetch_question_clo_ids(db: Session, quiz_id: int, qq_id: int) -> list[int]:
    if _routine_exists(db, "lms_fetch_quiz_que_clo_map_ids"):
        rows = db.execute(
            text("SELECT * FROM lms_fetch_quiz_que_clo_map_ids(:quiz_id, :qq_id)"),
            {"quiz_id": quiz_id, "qq_id": qq_id},
        ).fetchall()
        return [int(row[0]) for row in rows]

    rows = db.execute(
        text("SELECT clo_id FROM lms_quiz_que_clo_mapping WHERE quiz_id = :quiz_id AND qq_id = :qq_id"),
        {"quiz_id": quiz_id, "qq_id": qq_id},
    ).fetchall()
    return [int(row[0]) for row in rows]


# Fetches bloom mapping ids for a quiz question with function fallback support.
def _fetch_question_bloom_ids(db: Session, quiz_id: int, qq_id: int) -> list[int]:
    if _routine_exists(db, "lms_fetch_quiz_que_bloom_map_ids"):
        rows = db.execute(
            text("SELECT * FROM lms_fetch_quiz_que_bloom_map_ids(:quiz_id, :qq_id)"),
            {"quiz_id": quiz_id, "qq_id": qq_id},
        ).fetchall()
        return [int(row[0]) for row in rows]

    rows = db.execute(
        text("SELECT bloom_id FROM lms_quiz_que_bloom_mapping WHERE quiz_id = :quiz_id AND qq_id = :qq_id"),
        {"quiz_id": quiz_id, "qq_id": qq_id},
    ).fetchall()
    return [int(row[0]) for row in rows]


# Fetches all questions for a quiz with nested option and mapping details.
def _fetch_quiz_questions(db: Session, quiz_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text("SELECT * FROM lms_quiz_questions WHERE quiz_id = :quiz_id ORDER BY qq_id ASC"),
        {"quiz_id": quiz_id},
    ).mappings().all()
    questions = []
    for row in rows:
        item = dict(row)
        qq_id = int(item["qq_id"])
        item["options"] = _fetch_question_options(db, quiz_id, qq_id)
        item["clo_ids"] = _fetch_question_clo_ids(db, quiz_id, qq_id)
        item["bloom_ids"] = _fetch_question_bloom_ids(db, quiz_id, qq_id)
        questions.append(item)
    return questions


# Fetches academic batch values for the manage quiz curriculum dropdown.
@router.get("/meta/curriculums")
def get_quiz_curriculums(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT academic_batch_id, academic_batch_code, academic_batch_desc, academic_year, regulation_year
            FROM iems_academic_batch
            ORDER BY academic_batch_code ASC
            """
        )
    ).mappings().all()
    return returnSuccess(rows)


# Fetches term values for the selected academic batch.
@router.get("/meta/terms")
def get_quiz_terms(academic_batch_id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    query = """
        SELECT semester_id, semester, academic_batch_id
        FROM iems_semester
        WHERE 1=1
    """
    params: dict[str, Any] = {}
    if academic_batch_id is not None:
        query += " AND academic_batch_id = :academic_batch_id"
        params["academic_batch_id"] = academic_batch_id
    query += " ORDER BY semester_id ASC"
    rows = db.execute(text(query), params).mappings().all()
    return returnSuccess(rows)


# Fetches course values for the selected batch and term.
@router.get("/meta/courses")
def get_quiz_courses(
    academic_batch_id: Optional[int] = Query(default=None),
    semester_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = """
        SELECT crs_id, crs_code, crs_title, academic_batch_id, semester
        FROM iems_courses
        WHERE 1=1
    """
    params: dict[str, Any] = {}
    if academic_batch_id is not None:
        query += " AND academic_batch_id = :academic_batch_id"
        params["academic_batch_id"] = academic_batch_id
    if semester_id is not None:
        query += " AND semester = (SELECT semester FROM iems_semester WHERE semester_id = :semester_id)"
        params["semester_id"] = semester_id
    query += " ORDER BY crs_id DESC"
    rows = db.execute(text(query), params).mappings().all()
    return returnSuccess(rows)


# Fetches section values for the selected batch and term.
@router.get("/meta/sections")
def get_quiz_sections(
    academic_batch_id: Optional[int] = Query(default=None),
    semester_id: Optional[int] = Query(default=None),
    course_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        # Validate required parameters
        if None in [academic_batch_id, semester_id, course_id]:
            return {
                "success": False,
                "message": "academic_batch_id, semester_id, and course_id are required",
                "data": []
            }

        # Fetch sections from cudos_map_courseto_course_instructor
        sections = (
            db.query(
                CudosMapCoursetoCourseInstructor.section_id,
                MasterTypeDetails.mt_details_name,
            )
            .join(
                MasterTypeDetails,
                MasterTypeDetails.mt_details_id == CudosMapCoursetoCourseInstructor.section_id,
            )
            .filter(
                CudosMapCoursetoCourseInstructor.academic_batch_id == academic_batch_id
            )
            .filter(
                CudosMapCoursetoCourseInstructor.semester_id == semester_id
            )
            .filter(
                CudosMapCoursetoCourseInstructor.crs_id == course_id
            )
            .filter(
                CudosMapCoursetoCourseInstructor.section_id.isnot(None)
            )
            .distinct()
            .order_by(
                MasterTypeDetails.mt_details_name
            )
            .all()
        )

        # Return in same format as your section_list endpoint
        result = [
            {
                "value": section_id,
                "label": section_name,
            }
            for section_id, section_name in sections
        ]

        return {
            "success": True,
            "message": "Sections fetched successfully",
            "data": result
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": []
        }


# Fetches topic values for the selected course context.
# @router.get("/meta/topics")
# def get_quiz_topics(academic_batch_id: int, semester_id: int, crs_id: int, db: Session = Depends(get_db)):
#     rows = db.execute(
#         text(
#             """
#             SELECT topic_id, topic_code, topic_title, course_id, semester_id, academic_batch_id
#             FROM cudos_topic
#             WHERE academic_batch_id = :academic_batch_id
#               AND semester_id = :semester_id
#               AND course_id = :crs_id
#             ORDER BY topic_id DESC
#             """
#         ),
#         {"academic_batch_id": academic_batch_id, "semester_id": semester_id, "crs_id": crs_id},
#     ).mappings().all()
#     return returnSuccess(rows)

@router.get("/meta/topics")
def get_quiz_topics(
    academic_batch_id: int, 
    semester_id: int, 
    crs_id: int,
    section_id: Optional[int] = Query(default=None),
    instructor_id: Optional[int] = Query(default=None),
    include_unassigned: bool = Query(default=True),
    db: Session = Depends(get_db)
):
    """
    Fetch topics with instructor mapping information.
    If include_unassigned is True, includes topics without instructor mapping.
    """
    try:
        # Build the query with LEFT JOIN to include topics without instructor mapping
        query = """
            SELECT 
                t.topic_id,
                t.topic_code,
                t.topic_title,
                t.topic_content,
                lit.inst_map_id,
                CONCAT_WS(' ', u.title, u.first_name, u.last_name) as instructor_name,
                u.id as instructor_id,
                lit.status,
                lit.section_id
            FROM cudos_topic t
            LEFT JOIN lms_map_instructor_topic lit 
                ON lit.topic_id = t.topic_id 
                AND lit.academic_batch_id = t.academic_batch_id
                AND lit.semester_id = t.semester_id
                AND lit.crs_id = t.course_id
            LEFT JOIN iems_users u ON u.id = lit.instructor_id
            WHERE t.academic_batch_id = :academic_batch_id
                AND t.semester_id = :semester_id
                AND t.course_id = :crs_id
        """
        
        params = {
            "academic_batch_id": academic_batch_id,
            "semester_id": semester_id,
            "crs_id": crs_id
        }
        
        # Add section filter if provided
        if section_id is not None:
            query += " AND (lit.section_id = :section_id OR lit.section_id IS NULL)"
            params["section_id"] = section_id
        
        # Add instructor filter if provided
        if instructor_id is not None:
            query += " AND u.id = :instructor_id"
            params["instructor_id"] = instructor_id
        
        # If include_unassigned is False, only show topics with instructor mapping
        if not include_unassigned:
            query += " AND lit.inst_map_id IS NOT NULL"
        
        query += " GROUP BY t.topic_id ORDER BY t.topic_id DESC"
        
        result = db.execute(text(query), params).mappings().all()
        
        # Transform the result
        transformed_result = []
        for row in result:
            transformed_result.append({
                "topic_id": row.get("topic_id"),
                "topic_code": row.get("topic_code"),
                "topic_title": row.get("topic_title"),
                "topic_content": row.get("topic_content"),
                "inst_map_id": row.get("inst_map_id"),
                "instructor_name": row.get("instructor_name") or "Not Assigned",
                "instructor_id": row.get("instructor_id"),
                "status": row.get("status"),
                "section_id": row.get("section_id"),
                "has_instructor": row.get("instructor_id") is not None
            })
        
        return returnSuccess(transformed_result)
        
    except Exception as e:
        return returnException(f"Failed to fetch topics: {str(e)}")


# Fetches CLO values for the selected course.
@router.get("/meta/clo")
def get_quiz_clo(crs_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT clo_id, clo_statement, clo_code, crs_id
            FROM cudos_clo
            WHERE crs_id = :crs_id
            ORDER BY clo_id ASC
            """
        ),
        {"crs_id": crs_id},
    ).mappings().all()
    return returnSuccess(rows)


# Fetches bloom level values for quiz question mapping.
@router.get("/meta/bloom-levels")
def get_quiz_bloom_levels(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT bloom_id, level, learning, description
            FROM cudos_bloom_level
            ORDER BY bloom_id ASC
            """
        )
    ).mappings().all()
    return returnSuccess(rows)


# Creates a quiz and stores its section and topic mappings.
@router.post("/create")
def create_quiz(payload: QuizCreateRequest, db: Session = Depends(get_db)):
    if not payload.quiz_title.strip():
        return returnException("quiz_title is required")

    try:
        # Inserts quiz header values into the LMS quiz master table.
        quiz_id = _dynamic_insert(
            db,
            "lms_manage_quiz",
            {
                "quiz_title": payload.quiz_title.strip(),
                "quiz_instruction": payload.quiz_instruction,
                "quiz_description": payload.quiz_description,
                "academic_batch_id": payload.academic_batch_id,
                "semester_id": payload.semester_id,
                "crs_id": payload.crs_id,
                "quiz_date": payload.quiz_date,
                "quiz_time": payload.quiz_time,
                "start_date": payload.start_date,
                "start_time": payload.start_time,
                "end_date": payload.end_date,
                "end_time": payload.end_time,
                "duration": payload.duration,
                "file_name": payload.file_name,
                "file_path": payload.file_path,
                "marks_flag": payload.marks_flag,
                "co_map_flag": payload.co_map_flag,
                "bl_map_flag": payload.bl_map_flag,
                "practice_quiz": payload.practice_quiz,
                "shuffle_questions": payload.shuffle_questions,
                "shuffle_options": payload.shuffle_options,
                "answer_key_share_flag": payload.answer_key_share_flag,
                "status": payload.status,
                "created_by": payload.created_by,
                "created_date": datetime.now(),
                "show_date": payload.show_date,
                "show_time": payload.show_time
            },
        )

        # Saves section mappings for the newly created quiz.
        for section_id in payload.section_ids:
            _dynamic_insert(
                db,
                "lms_quiz_section_mapping",
                {
                    "quiz_id": quiz_id,
                    "section_id": section_id,
                    "created_by": payload.created_by,
                    "created_date": datetime.now(),
                },
            )

        # Saves topic mappings for the newly created quiz.
        for topic_id in payload.topic_ids:
            _dynamic_insert(
                db,
                "lms_quiz_topic_mapping",
                {
                    "quiz_id": quiz_id,
                    "topic_id": topic_id,
                    "created_by": payload.created_by,
                    "created_date": datetime.now(),
                },
            )

        db.commit()
        return returnSuccess(
            {
                "quiz_id": quiz_id,
                "section_count": len(payload.section_ids),
                "topic_count": len(payload.topic_ids),
            },
            "Quiz created successfully",
        )
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to create quiz: {str(exc)}")


# @router.get("/list")
# def get_quiz_list(
#     academic_batch_id: int = Query(..., description="Curriculum/Batch ID"),
#     semester_id: int = Query(..., description="Semester/Term ID"),
#     crs_id: int = Query(..., description="Course ID"),
#     page: int = Query(default=1, ge=1),
#     page_size: int = Query(default=20, ge=1, le=100),
#     created_by: Optional[int] = Query(default=None, description="Filter by creator"),
#     instructor_id: Optional[int] = Query(default=None, description="Filter by instructor for non-admin users"),
#     db: Session = Depends(get_db),
# ):
#     """
#     Get quiz list with details including quiz status
#     """
#     try:
#         # Build the query
#         query = """
#             SELECT 
#                 mq.*,
#                 DATE_FORMAT(mq.show_date, '%%d-%%m-%%Y') as s_date,
#                 DATE_FORMAT(mq.show_time, '%%h:%%i %%p') as s_time,
#                 -- Total students mapped
#                 (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) AS total_students,
#                 -- Completed students (accept_rework_flag = 2)
#                 (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id AND qsm.accept_rework_flag = 2) AS completed_students,
#                 -- CLO mapping flag
#                 CASE 
#                     WHEN (SELECT COUNT(*) FROM lms_quiz_que_clo_mapping qcm WHERE qcm.quiz_id = mq.quiz_id) > 0 THEN 1 
#                     ELSE 0 
#                 END as clo_map,
#                 -- Bloom mapping flag
#                 CASE 
#                     WHEN (SELECT COUNT(*) FROM lms_quiz_que_bloom_mapping qbm WHERE qbm.quiz_id = mq.quiz_id) > 0 THEN 1 
#                     ELSE 0 
#                 END as bloom_map,
#                 -- Total marks
#                 (SELECT COALESCE(SUM(marks), 0) FROM lms_quiz_questions qq WHERE qq.quiz_id = mq.quiz_id) as total_marks,
#                 GROUP_CONCAT(DISTINCT t.topic_title SEPARATOR '<br/>') as topic,
#                 GROUP_CONCAT(DISTINCT t.topic_id) as topic_id,
#                 GROUP_CONCAT(DISTINCT mtd.mt_details_name SEPARATOR ', ') as section_names,
#                 GROUP_CONCAT(DISTINCT qs.section_id) as section_ids,
#                 CASE WHEN COUNT(sa.sqa_id) > 0 THEN 1 ELSE 0 END AS is_attempted,
#                 (SELECT COUNT(*) FROM lms_quiz_questions qq WHERE qq.quiz_id = mq.quiz_id) AS question_count,
#                 (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) AS student_count,
#                 (SELECT COUNT(*) FROM lms_quiz_start_log qsl WHERE qsl.quiz_id = mq.quiz_id) AS started_count,
#                 (SELECT COUNT(*) FROM lms_quiz_student_answer qsa WHERE qsa.quiz_id = mq.quiz_id) AS answer_count
#             FROM lms_manage_quiz mq
#             LEFT JOIN lms_quiz_section_mapping qs ON mq.quiz_id = qs.quiz_id
#             LEFT JOIN cudos_master_type_details mtd ON qs.section_id = mtd.mt_details_id
#             LEFT JOIN lms_quiz_topic_mapping qt ON mq.quiz_id = qt.quiz_id
#             LEFT JOIN cudos_topic t ON qt.topic_id = t.topic_id
#             LEFT JOIN lms_quiz_student_answer sa ON mq.quiz_id = sa.quiz_id
#         """
        
#         params = {
#             "academic_batch_id": academic_batch_id,
#             "semester_id": semester_id,
#             "crs_id": crs_id
#         }
        
#         # Add WHERE conditions
#         where_conditions = [
#             "mq.academic_batch_id = :academic_batch_id",
#             "mq.semester_id = :semester_id",
#             "mq.crs_id = :crs_id"
#         ]
        
#         if created_by is not None:
#             where_conditions.append("mq.created_by = :created_by")
#             params["created_by"] = created_by
        
#         # Instructor filter for non-admin users
#         if instructor_id is not None:
#             query += """
#                 LEFT JOIN lms_map_instructor_topic o ON t.topic_id = o.topic_id
#             """
#             where_conditions.append("o.instructor_id = :instructor_id")
#             params["instructor_id"] = instructor_id
        
#         query += " WHERE " + " AND ".join(where_conditions)
        
#         # Group by quiz_id
#         query += " GROUP BY mq.quiz_id"
        
#         # Order by
#         query += """
#             ORDER BY 
#                 STR_TO_DATE(mq.quiz_date, '%%d-%%m-%%Y') = CURDATE() DESC,
#                 STR_TO_DATE(CONCAT(mq.quiz_date, ' ', mq.quiz_time), '%%d-%%m-%%Y %%h:%%i %%p') DESC,
#                 mq.quiz_id DESC
#         """
        
#         # Get total count
#         count_query = f"SELECT COUNT(*) FROM ({query}) as subquery"
#         total_result = db.execute(text(count_query), params)
#         total = total_result.scalar() or 0
        
#         # Add pagination
#         offset = (page - 1) * page_size
#         query += " LIMIT :limit OFFSET :offset"
#         params["limit"] = page_size
#         params["offset"] = offset
        
#         # Execute main query
#         rows = db.execute(text(query), params).mappings().all()
        
#         # Convert to list of dicts with quiz status
#         result_items = []
#         for row in rows:
#             item = dict(row)
            
#             # Calculate quiz status (matching the MySQL function logic)
#             total_students = int(item.get('total_students') or 0)
#             completed_students = int(item.get('completed_students') or 0)
            
#             if total_students > 0 and completed_students < total_students:
#                 item['quiz_status'] = 'In Progress'
#                 item['quiz_status_color'] = 'orange'
#                 item['quiz_status_html'] = '<p style="color:orange;">In Progress</p>'
#                 item['quiz_status_value'] = 2
#             elif total_students > 0 and total_students == completed_students:
#                 item['quiz_status'] = 'Completed'
#                 item['quiz_status_color'] = 'green'
#                 item['quiz_status_html'] = '<p style="color:green;">Completed</p>'
#                 item['quiz_status_value'] = 1
#             else:
#                 item['quiz_status'] = 'Not Initiated'
#                 item['quiz_status_color'] = 'red'
#                 item['quiz_status_html'] = '<p style="color:red;">Not Initiated</p>'
#                 item['quiz_status_value'] = 0
            
#             # Convert None values to appropriate defaults
#             item['topic'] = item.get('topic') or ''
#             item['topic_id'] = item.get('topic_id') or ''
#             item['section_names'] = item.get('section_names') or ''
#             item['section_ids'] = item.get('section_ids') or ''
#             item['total_marks'] = float(item.get('total_marks') or 0)
#             item['question_count'] = int(item.get('question_count') or 0)
#             item['student_count'] = int(item.get('student_count') or 0)
#             item['started_count'] = int(item.get('started_count') or 0)
#             item['answer_count'] = int(item.get('answer_count') or 0)
#             item['is_attempted'] = int(item.get('is_attempted') or 0)
#             item['clo_map'] = int(item.get('clo_map') or 0)
#             item['bloom_map'] = int(item.get('bloom_map') or 0)
#             item['total_students'] = total_students
#             item['completed_students'] = completed_students
            
#             result_items.append(item)
        
#         return returnSuccess({
#             "page": page,
#             "page_size": page_size,
#             "total": int(total),
#             "items": result_items
#         })
        
#     except Exception as e:
#         print(f"Error in get_quiz_list: {str(e)}")
#         return returnException(f"Failed to fetch quiz list: {str(e)}")


@router.get("/list")
def get_quiz_list(
    academic_batch_id: int = Query(..., description="Curriculum/Batch ID"),
    semester_id: int = Query(..., description="Semester/Term ID"),
    crs_id: int = Query(..., description="Course ID"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    created_by: Optional[int] = Query(default=None, description="Filter by creator"),
    instructor_id: Optional[int] = Query(default=None, description="Filter by instructor for non-admin users"),
    db: Session = Depends(get_db),
):
    """
    Get quiz list with topics and sections
    """
    try:
        # Build the query with topic and section data
        query = """
            SELECT 
                mq.*,
                -- ✅ Topic names (comma separated)
                GROUP_CONCAT(DISTINCT t.topic_title SEPARATOR ', ') as topic_names,
                -- ✅ Topic IDs (comma separated)
                GROUP_CONCAT(DISTINCT t.topic_id) as topic_ids,
                -- ✅ Topic names with HTML line breaks (for legacy)
                GROUP_CONCAT(DISTINCT t.topic_title SEPARATOR '<br/>') as topic,
                -- ✅ Section names (comma separated)
                GROUP_CONCAT(DISTINCT mtd.mt_details_name SEPARATOR ', ') as section_names,
                -- ✅ Section IDs (comma separated)
                GROUP_CONCAT(DISTINCT qs.section_id) as section_ids,
                -- ✅ Total marks
                (SELECT COALESCE(SUM(marks), 0) FROM lms_quiz_questions qq WHERE qq.quiz_id = mq.quiz_id) as total_marks,
                -- ✅ Question count
                (SELECT COUNT(*) FROM lms_quiz_questions qq WHERE qq.quiz_id = mq.quiz_id) AS question_count,
                -- ✅ Student count
                (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) AS student_count,
                -- ✅ Started count
                (SELECT COUNT(*) FROM lms_quiz_start_log qsl WHERE qsl.quiz_id = mq.quiz_id) AS started_count,
                -- ✅ Answer count
                (SELECT COUNT(*) FROM lms_quiz_student_answer qsa WHERE qsa.quiz_id = mq.quiz_id) AS answer_count,
                -- ✅ Quiz status
                CASE 
                    WHEN (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) > 0 
                    AND (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id AND qsm.accept_rework_flag = 2) 
                        < (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) 
                    THEN 'In Progress'
                    WHEN (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) > 0 
                    AND (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id AND qsm.accept_rework_flag = 2) 
                        = (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) 
                    THEN 'Completed'
                    ELSE 'Not Initiated'
                END as quiz_status,
                -- ✅ Status color
                CASE 
                    WHEN (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) > 0 
                    AND (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id AND qsm.accept_rework_flag = 2) 
                        < (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) 
                    THEN 'orange'
                    WHEN (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) > 0 
                    AND (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id AND qsm.accept_rework_flag = 2) 
                        = (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) 
                    THEN 'green'
                    ELSE 'red'
                END as quiz_status_color,
                -- ✅ Total students
                (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id) AS total_students,
                -- ✅ Completed students
                (SELECT COUNT(*) FROM lms_quiz_student_mapping qsm WHERE qsm.quiz_id = mq.quiz_id AND qsm.accept_rework_flag = 2) AS completed_students,
                -- ✅ CLO mapping flag
                CASE 
                    WHEN (SELECT COUNT(*) FROM lms_quiz_que_clo_mapping qcm WHERE qcm.quiz_id = mq.quiz_id) > 0 THEN 1 
                    ELSE 0 
                END as clo_map,
                -- ✅ Bloom mapping flag
                CASE 
                    WHEN (SELECT COUNT(*) FROM lms_quiz_que_bloom_mapping qbm WHERE qbm.quiz_id = mq.quiz_id) > 0 THEN 1 
                    ELSE 0 
                END as bloom_map
            FROM lms_manage_quiz mq
            LEFT JOIN lms_quiz_section_mapping qs ON mq.quiz_id = qs.quiz_id
            LEFT JOIN cudos_master_type_details mtd ON qs.section_id = mtd.mt_details_id
            LEFT JOIN lms_quiz_topic_mapping qt ON mq.quiz_id = qt.quiz_id
            LEFT JOIN cudos_topic t ON qt.topic_id = t.topic_id
            WHERE mq.academic_batch_id = :academic_batch_id
                AND mq.semester_id = :semester_id
                AND mq.crs_id = :crs_id
        """
        
        params = {
            "academic_batch_id": academic_batch_id,
            "semester_id": semester_id,
            "crs_id": crs_id
        }
        
        # Add created_by filter
        if created_by is not None:
            query += " AND mq.created_by = :created_by"
            params["created_by"] = created_by
        
        # Add instructor filter for non-admin users
        if instructor_id is not None:
            query += """
                AND EXISTS (
                    SELECT 1 FROM lms_map_instructor_topic o 
                    WHERE o.topic_id = t.topic_id 
                    AND o.instructor_id = :instructor_id
                )
            """
            params["instructor_id"] = instructor_id
        
        query += " GROUP BY mq.quiz_id"
        
        # Order by
        query += """
            ORDER BY 
                STR_TO_DATE(mq.quiz_date, '%%d-%%m-%%Y') = CURDATE() DESC,
                STR_TO_DATE(CONCAT(mq.quiz_date, ' ', mq.quiz_time), '%%d-%%m-%%Y %%h:%%i %%p') DESC,
                mq.quiz_id DESC
        """
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as subquery"
        total_result = db.execute(text(count_query), params)
        total = total_result.scalar() or 0
        
        # Add pagination
        offset = (page - 1) * page_size
        query += " LIMIT :limit OFFSET :offset"
        params["limit"] = page_size
        params["offset"] = offset
        
        # Execute main query
        rows = db.execute(text(query), params).mappings().all()
        
        # Convert to list of dicts
        result_items = []
        for row in rows:
            item = dict(row)
            # Ensure fields are not None
            item['topic_names'] = item.get('topic_names') or ''
            item['topic_ids'] = item.get('topic_ids') or ''
            item['topic'] = item.get('topic') or ''
            item['section_names'] = item.get('section_names') or ''
            item['section_ids'] = item.get('section_ids') or ''
            item['total_marks'] = float(item.get('total_marks') or 0)
            item['question_count'] = int(item.get('question_count') or 0)
            item['student_count'] = int(item.get('student_count') or 0)
            item['started_count'] = int(item.get('started_count') or 0)
            item['answer_count'] = int(item.get('answer_count') or 0)
            item['total_students'] = int(item.get('total_students') or 0)
            item['completed_students'] = int(item.get('completed_students') or 0)
            item['clo_map'] = int(item.get('clo_map') or 0)
            item['bloom_map'] = int(item.get('bloom_map') or 0)
            result_items.append(item)
        
        return returnSuccess({
            "page": page,
            "page_size": page_size,
            "total": int(total),
            "items": result_items
        })
        
    except Exception as e:
        print(f"Error in get_quiz_list: {str(e)}")
        return returnException(f"Failed to fetch quiz list: {str(e)}")


# Fetches quiz details with mappings, questions, and share summary.
@router.get("/{quiz_id}")
def get_quiz_details(quiz_id: int, db: Session = Depends(get_db)):
    try:
        quiz = db.execute(
            text("SELECT * FROM lms_manage_quiz WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id},
        ).mappings().first()
        if not quiz:
            return returnException("Quiz not found")

        try:
            students = db.execute(
                text("SELECT * FROM lms_quiz_student_mapping WHERE quiz_id = :quiz_id ORDER BY quiz_student_map_id ASC"),
                {"quiz_id": quiz_id},
            ).mappings().all()
            students_list = [dict(row) for row in students]
        except Exception:
            db.rollback()
            students_list = []

        try:
            start_count = db.execute(
                text("SELECT COUNT(*) FROM lms_quiz_start_log WHERE quiz_id = :quiz_id"),
                {"quiz_id": quiz_id},
            ).scalar() or 0
        except Exception:
            db.rollback()
            start_count = 0

        try:
            answers_count = db.execute(
                text("SELECT COUNT(*) FROM lms_quiz_student_answer WHERE quiz_id = :quiz_id"),
                {"quiz_id": quiz_id},
            ).scalar() or 0
        except Exception:
            db.rollback()
            answers_count = 0

        try:
            questions = _fetch_quiz_questions(db, quiz_id)
        except Exception:
            db.rollback()
            questions = []

        try:
            section_ids = _fetch_quiz_section_ids(db, quiz_id)
        except Exception:
            db.rollback()
            section_ids = []

        try:
            topic_ids = _fetch_quiz_topic_ids(db, quiz_id)
        except Exception:
            db.rollback()
            topic_ids = []

        return returnSuccess(
            {
                "quiz": dict(quiz),
                "section_ids": section_ids,
                "topic_ids": topic_ids,
                "questions": questions,
                "students": students_list,
                "started_count": int(start_count),
                "answers_count": int(answers_count),
                "is_edit_blocked": bool(start_count),
            }
        )
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to fetch quiz details: {str(exc)}")


# Updates quiz details and replaces its section and topic mappings.
@router.put("/{quiz_id}")
def update_quiz(quiz_id: int, payload: QuizUpdateRequest, db: Session = Depends(get_db)):
    exists = db.execute(
        text("SELECT quiz_id FROM lms_manage_quiz WHERE quiz_id = :quiz_id"),
        {"quiz_id": quiz_id},
    ).scalar()
    if not exists:
        return returnException("Quiz not found")

    if _quiz_has_started(db, quiz_id):
        return returnException("Quiz edit is blocked because the quiz has already started")

    try:
        # Updates editable quiz master values before remapping sections and topics.
        _dynamic_update(
            db,
            "lms_manage_quiz",
            "quiz_id",
            quiz_id,
            {
                "quiz_title": payload.quiz_title.strip() if payload.quiz_title else None,
                "quiz_instruction": payload.quiz_instruction,
                "quiz_description": payload.quiz_description,
                "academic_batch_id": payload.academic_batch_id,
                "semester_id": payload.semester_id,
                "crs_id": payload.crs_id,
                "quiz_date": payload.quiz_date,
                "quiz_time": payload.quiz_time,
                "start_date": payload.start_date,
                "start_time": payload.start_time,
                "end_date": payload.end_date,
                "end_time": payload.end_time,
                "duration": payload.duration,
                "file_name": payload.file_name,
                "file_path": payload.file_path,
                "marks_flag": payload.marks_flag,
                "co_map_flag": payload.co_map_flag,
                "bl_map_flag": payload.bl_map_flag,
                "practice_quiz": payload.practice_quiz,
                "shuffle_questions": payload.shuffle_questions,
                "shuffle_options": payload.shuffle_options,
                "answer_key_share_flag": payload.answer_key_share_flag,
                "status": payload.status,
                "modified_by": payload.modified_by,
                "modified_date": datetime.now(),
                "show_date" : payload.show_date,
                "show_time" : payload.show_time
            },
        )

        # Replaces section mappings when section ids are provided.
        if payload.section_ids is not None:
            db.execute(text("DELETE FROM lms_quiz_section_mapping WHERE quiz_id = :quiz_id"), {"quiz_id": quiz_id})
            for section_id in payload.section_ids:
                _dynamic_insert(
                    db,
                    "lms_quiz_section_mapping",
                    {
                        "quiz_id": quiz_id,
                        "section_id": section_id,
                        "created_by": payload.modified_by,
                        "created_date": datetime.now(),
                    },
                )

        # Replaces topic mappings when topic ids are provided.
        if payload.topic_ids is not None:
            db.execute(text("DELETE FROM lms_quiz_topic_mapping WHERE quiz_id = :quiz_id"), {"quiz_id": quiz_id})
            for topic_id in payload.topic_ids:
                _dynamic_insert(
                    db,
                    "lms_quiz_topic_mapping",
                    {
                        "quiz_id": quiz_id,
                        "topic_id": topic_id,
                        "created_by": payload.modified_by,
                        "created_date": datetime.now(),
                    },
                )

        db.commit()
        return returnSuccess({"quiz_id": quiz_id}, "Quiz updated successfully")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to update quiz: {str(exc)}")


# Creates a question with options, CLO mappings, and bloom mappings.
@router.post("/{quiz_id}/question")
def create_quiz_question(quiz_id: int, payload: QuizQuestionCreateRequest, db: Session = Depends(get_db)):
    quiz_exists = db.execute(
        text("SELECT quiz_id FROM lms_manage_quiz WHERE quiz_id = :quiz_id"),
        {"quiz_id": quiz_id},
    ).scalar()
    if not quiz_exists:
        return returnException("Quiz not found")

    if _quiz_has_started(db, quiz_id):
        return returnException("Question create is blocked because the quiz has already started")

    try:
        # Inserts the main quiz question before saving child mappings.
        qq_id = _dynamic_insert(
            db,
            "lms_quiz_questions",
            {
                "quiz_id": quiz_id,
                "main_que_code": payload.main_que_code,
                "sub_que_code": payload.sub_que_code,
                "question": payload.question.strip(),
                "question_type": payload.question_type,
                "marks": payload.marks,
                "created_by": payload.created_by,
                "created_date": datetime.now(),
            },
        )

        # Saves option rows for the created quiz question.
        for option in payload.options:
            _dynamic_insert(
                db,
                "lms_quiz_que_options",
                {
                    "quiz_id": quiz_id,
                    "qq_id": qq_id,
                    "question_type": payload.question_type,
                    "option_value": option.option_value,
                    "is_answer": option.is_answer,
                    "explanation": option.explanation,
                    "created_by": payload.created_by,
                    "created_date": datetime.now(),
                },
            )

        # Saves CLO mappings for the created quiz question.
        for clo_id in payload.clo_ids:
            _dynamic_insert(
                db,
                "lms_quiz_que_clo_mapping",
                {
                    "quiz_id": quiz_id,
                    "qq_id": qq_id,
                    "clo_id": clo_id,
                    "created_by": payload.created_by,
                    "created_date": datetime.now(),
                },
            )

        # Saves bloom mappings for the created quiz question.
        for bloom_id in payload.bloom_ids:
            _dynamic_insert(
                db,
                "lms_quiz_que_bloom_mapping",
                {
                    "quiz_id": quiz_id,
                    "qq_id": qq_id,
                    "bloom_id": bloom_id,
                    "created_by": payload.created_by,
                    "created_date": datetime.now(),
                },
            )

        db.commit()
        return returnSuccess({"quiz_id": quiz_id, "qq_id": qq_id}, "Quiz question created successfully")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to create quiz question: {str(exc)}")


# Updates a question and fully replaces its option and mapping rows.
@router.put("/question/{qq_id}")
def update_quiz_question(qq_id: int, payload: QuizQuestionUpdateRequest, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT quiz_id FROM lms_quiz_questions WHERE qq_id = :qq_id"),
        {"qq_id": qq_id},
    ).mappings().first()
    if not row:
        return returnException("Quiz question not found")

    quiz_id = int(row["quiz_id"])
    if _quiz_has_started(db, quiz_id):
        return returnException("Question edit is blocked because the quiz has already started")

    try:
        # Updates the quiz question master row.
        _dynamic_update(
            db,
            "lms_quiz_questions",
            "qq_id",
            qq_id,
            {
                "main_que_code": payload.main_que_code,
                "sub_que_code": payload.sub_que_code,
                "question": payload.question.strip() if payload.question else None,
                "question_type": payload.question_type,
                "marks": payload.marks,
                "modified_by": payload.modified_by,
                "modified_date": datetime.now(),
            },
        )

        # Replaces question options when option values are supplied.
        if payload.options is not None:
            db.execute(text("DELETE FROM lms_quiz_que_options WHERE qq_id = :qq_id"), {"qq_id": qq_id})
            question_type = payload.question_type
            if question_type is None:
                current_type = db.execute(
                    text("SELECT question_type FROM lms_quiz_questions WHERE qq_id = :qq_id"),
                    {"qq_id": qq_id},
                ).scalar()
                question_type = int(current_type or 0)
            for option in payload.options:
                _dynamic_insert(
                    db,
                    "lms_quiz_que_options",
                    {
                        "quiz_id": quiz_id,
                        "qq_id": qq_id,
                        "question_type": question_type,
                        "option_value": option.option_value,
                        "is_answer": option.is_answer,
                        "explanation": option.explanation,
                        "created_by": payload.modified_by,
                        "created_date": datetime.now(),
                    },
                )

        # Replaces CLO mappings when clo ids are supplied.
        if payload.clo_ids is not None:
            db.execute(text("DELETE FROM lms_quiz_que_clo_mapping WHERE qq_id = :qq_id"), {"qq_id": qq_id})
            for clo_id in payload.clo_ids:
                _dynamic_insert(
                    db,
                    "lms_quiz_que_clo_mapping",
                    {
                        "quiz_id": quiz_id,
                        "qq_id": qq_id,
                        "clo_id": clo_id,
                        "created_by": payload.modified_by,
                        "created_date": datetime.now(),
                    },
                )

        # Replaces bloom mappings when bloom ids are supplied.
        if payload.bloom_ids is not None:
            db.execute(text("DELETE FROM lms_quiz_que_bloom_mapping WHERE qq_id = :qq_id"), {"qq_id": qq_id})
            for bloom_id in payload.bloom_ids:
                _dynamic_insert(
                    db,
                    "lms_quiz_que_bloom_mapping",
                    {
                        "quiz_id": quiz_id,
                        "qq_id": qq_id,
                        "bloom_id": bloom_id,
                        "created_by": payload.modified_by,
                        "created_date": datetime.now(),
                    },
                )

        db.commit()
        return returnSuccess({"qq_id": qq_id}, "Quiz question updated successfully")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to update quiz question: {str(exc)}")


# Deletes a quiz question only when the quiz has not started.
@router.delete("/question/{qq_id}")
def delete_quiz_question(qq_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT quiz_id FROM lms_quiz_questions WHERE qq_id = :qq_id"),
        {"qq_id": qq_id},
    ).mappings().first()
    if not row:
        return returnException("Quiz question not found")

    quiz_id = int(row["quiz_id"])
    if _quiz_has_started(db, quiz_id):
        return returnException("Question delete is blocked because the quiz has already started")

    try:
        # Deletes child option and mapping rows before removing the question.
        db.execute(text("DELETE FROM lms_quiz_que_options WHERE qq_id = :qq_id"), {"qq_id": qq_id})
        db.execute(text("DELETE FROM lms_quiz_que_clo_mapping WHERE qq_id = :qq_id"), {"qq_id": qq_id})
        db.execute(text("DELETE FROM lms_quiz_que_bloom_mapping WHERE qq_id = :qq_id"), {"qq_id": qq_id})
        db.execute(text("DELETE FROM lms_quiz_questions WHERE qq_id = :qq_id"), {"qq_id": qq_id})
        db.commit()
        return returnSuccess({"qq_id": qq_id}, "Quiz question deleted successfully")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to delete quiz question: {str(exc)}")


@router.post("/{quiz_id}/share")
def share_quiz(
    quiz_id: int, 
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Share quiz with selected students only
    """
    try:
        # Check if quiz exists
        quiz = db.execute(
            text("SELECT * FROM lms_manage_quiz WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id},
        ).mappings().first()
        
        if not quiz:
            return returnException("Quiz not found")

        if _quiz_has_started(db, quiz_id):
            return returnException("Quiz share is blocked because the quiz has already started")

        # Get student_ids from payload
        student_ids = payload.get('student_ids', [])
        
        # If no student_ids provided, return error
        if not student_ids:
            return returnException("No students selected for sharing")

        inserted = 0
        skipped = 0

        # Only share with the selected student IDs
        for student_id in student_ids:
            # Check if already mapped
            existing = db.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM lms_quiz_student_mapping 
                    WHERE quiz_id = :quiz_id AND ssd_id = :student_id
                """),
                {"quiz_id": quiz_id, "student_id": student_id},
            ).scalar() or 0
            
            if existing > 0:
                skipped += 1
                continue

            # Get student USN for the mapping
            student_usn = db.execute(
                text("SELECT usno FROM iems_students WHERE student_id = :student_id"),
                {"student_id": student_id}
            ).scalar()

            # ✅ Insert without created_by and created_date (they don't exist in your table)
            db.execute(
                text("""
                    INSERT INTO lms_quiz_student_mapping 
                    (quiz_id, ssd_id, student_usn) 
                    VALUES (:quiz_id, :student_id, :student_usn)
                """),
                {
                    "quiz_id": quiz_id,
                    "student_id": student_id,
                    "student_usn": student_usn
                }
            )
            inserted += 1

        db.commit()
        
        return returnSuccess(
            {
                "quiz_id": quiz_id, 
                "inserted": inserted, 
                "skipped": skipped,
                "total": len(student_ids)
            }, 
            f"Quiz shared with {inserted} student(s)"
        )
        
    except Exception as exc:
        db.rollback()
        print(f"Error in share_quiz: {str(exc)}")
        return returnException(f"Failed to share quiz: {str(exc)}")


@router.get("/{quiz_id}/students")
def get_quiz_students(
    quiz_id: int,
    academic_batch_id: int = Query(..., description="Curriculum/Batch ID"),
    semester_id: int = Query(..., description="Semester/Term ID"),
    crs_id: int = Query(..., description="Course ID"),
    section_id: Optional[int] = Query(default=None, description="Section ID"),
    db: Session = Depends(get_db)
):
    """
    Get all students from the course/section with their quiz status
    """
    try:
        # First check if quiz exists
        quiz = db.execute(
            text("SELECT * FROM lms_manage_quiz WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id}
        ).mappings().first()
        
        if not quiz:
            return returnException("Quiz not found")
        
        # Get total marks for this quiz
        total_marks = db.execute(
            text("SELECT COALESCE(SUM(marks), 0) FROM lms_quiz_questions WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id}
        ).scalar() or 0
        
        # Query using only existing tables and columns
        query = """
            SELECT 
                s.student_id,
                s.usno,
                s.first_name,
                s.last_name,
                s.section,
                -- Check if student is mapped to this quiz
                CASE 
                    WHEN qsm.qs_map_id IS NOT NULL THEN 1 
                    ELSE 0 
                END as is_mapped,
                -- Mapping ID if exists
                qsm.qs_map_id as mapping_id,
                -- Check if student has submitted (using is_submitted flag)
                CASE 
                    WHEN qsm.is_submitted = 1 THEN 1 
                    ELSE 0 
                END as has_submitted,
                -- Submitted answers count (from lms_quiz_student_answer if it exists)
                (
                    SELECT COUNT(*) 
                    FROM lms_quiz_student_answer qsa2 
                    WHERE qsa2.quiz_id = :quiz_id 
                    AND qsa2.ssd_id = s.student_id
                ) as answer_count,
                -- Secured marks
                qsm.secured_marks as secured_marks,
                -- Accept/rework status
                qsm.accept_rework_flag,
                qsm.remarks,
                qsm.viewed_on as shared_date,
                qsm.q_secured_marks as q_secured_marks
            FROM iems_students s
            -- Get course mapping for this student
            INNER JOIN cudos_map_courseto_student cms 
                ON cms.student_id = s.student_id
                AND cms.academic_batch_id = :academic_batch_id
                AND cms.semester_id = :semester_id
                AND cms.crs_id = :crs_id
            -- Left join with quiz mapping
            LEFT JOIN lms_quiz_student_mapping qsm 
                ON qsm.ssd_id = s.student_id 
                AND qsm.quiz_id = :quiz_id
            WHERE 1=1
        """
        
        params = {
            "quiz_id": quiz_id,
            "academic_batch_id": academic_batch_id,
            "semester_id": semester_id,
            "crs_id": crs_id
        }
        
        # Add section filter if provided
        if section_id is not None:
            query += " AND cms.section_id = :section_id"
            params["section_id"] = section_id
        
        query += " GROUP BY s.student_id ORDER BY s.usno ASC"
        
        result = db.execute(text(query), params).mappings().all()
        
        # Transform the result
        students = []
        for row in result:
            student = dict(row)
            
            # Determine status based on available data
            if student.get('is_mapped'):
                if student.get('has_submitted') or student.get('answer_count', 0) > 0:
                    student['status'] = 'Submitted'
                    # Calculate total secured marks from q_secured_marks or secured_marks
                    student['secured_marks'] = student.get('q_secured_marks') or student.get('secured_marks') or 0
                else:
                    student['status'] = 'Not Started'
                    student['secured_marks'] = 0
            else:
                student['status'] = 'Not Shared'
                student['secured_marks'] = 0
            
            # Format name
            student['student_name'] = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip() or student.get('usno', '')
            student['total_marks'] = total_marks
            
            # Ensure secured_marks is not None
            if student.get('secured_marks') is None:
                student['secured_marks'] = 0
            
            students.append(student)
        
        return returnSuccess({
            "quiz_id": quiz_id,
            "total": len(students),
            "items": students
        })
        
    except Exception as e:
        print(f"Error in get_quiz_students: {str(e)}")
        return returnException(f"Failed to fetch quiz students: {str(e)}")

# Deletes a quiz and ALL its related data (including student mappings).
@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)):
    print(f"🔥 DELETE ROUTE HIT for quiz_id: {quiz_id}")
    # Check if the quiz exists
    quiz_exists = db.execute(
        text("SELECT quiz_id FROM lms_manage_quiz WHERE quiz_id = :quiz_id"),
        {"quiz_id": quiz_id},
    ).scalar()
    if not quiz_exists:
        return returnException("Quiz not found")

    try:
        # 1. Delete Student Mappings (IMPORTANT: Must be done before deleting the quiz)
        db.execute(
            text("DELETE FROM lms_quiz_student_mapping WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id},
        )

        # 2. Delete Section Mappings
        db.execute(
            text("DELETE FROM lms_quiz_section_mapping WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id},
        )

        # 3. Delete Topic Mappings
        db.execute(
            text("DELETE FROM lms_quiz_topic_mapping WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id},
        )

        # 4. Delete all question options for questions in this quiz
        db.execute(
            text("""
                DELETE FROM lms_quiz_que_options 
                WHERE qq_id IN (SELECT qq_id FROM lms_quiz_questions WHERE quiz_id = :quiz_id)
            """),
            {"quiz_id": quiz_id},
        )

        # 5. Delete CLO mappings
        # db.execute(
        #     text("""
        #         DELETE FROM lms_quiz_que_clo_mapping 
        #         WHERE qq_id IN (SELECT qq_id FROM lms_quiz_questions WHERE quiz_id = :quiz_id)
        #     """),
        #     {"quiz_id": quiz_id},
        # )

        # # 6. Delete Bloom mappings
        # db.execute(
        #     text("""
        #         DELETE FROM lms_quiz_que_bloom_mapping 
        #         WHERE qq_id IN (SELECT qq_id FROM lms_quiz_questions WHERE quiz_id = :quiz_id)
        #     """),
        #     {"quiz_id": quiz_id},
        # )

        # 7. Delete the questions themselves
        db.execute(
            text("DELETE FROM lms_quiz_questions WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id},
        )

        # 8. Finally, delete the main quiz itself
        db.execute(
            text("DELETE FROM lms_manage_quiz WHERE quiz_id = :quiz_id"),
            {"quiz_id": quiz_id},
        )

        db.commit()
        return returnSuccess({"quiz_id": quiz_id}, "Quiz and all associated records deleted successfully")
    
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to delete quiz: {str(exc)}")