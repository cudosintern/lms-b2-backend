from urllib import request
print("🔥 Topic Router Loaded")

import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import distinct, text
from datetime import date, datetime
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.core.database import get_db
# Strictly using ONLY the allowed tables from your models.py
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
    CudosMapCourseToCourseInstructor  # Added back for the Instructor/Handled By column
)
# Using only your pre-existing schemas
from .topic_schema import (
    CourseListRequest,
    TopicCreateRequest,
    TopicListRequest,
    UpdateInstructorRequest,
    ImportCudosTopicsRequest,
    ImportTopicRequest,
    AddScheduleRequest
)

router = APIRouter(
    tags=["Topic Management"]
)

# Helper function to return success response
def success_response(data, message="Success"):
    return {
        "success": True,
        "message": message,
        "data": data
    }

# Helper function to return error response
def error_response(message, data=None):
    return {
        "success": False,
        "message": message,
        "data": data
    }

# =========================================================
# ✅ DROPDOWN APIs
# =========================================================

@router.post("/curriculum_list")
def get_curriculum_list_post(db: Session = Depends(get_db)):
    try:
        data = db.query(IEMSAcademicBatch).all()
        result = [
            {
                "value": row.academic_batch_id,
                "label": f"{row.academic_batch_desc} ({row.academic_year})",
            }
            for row in data
        ]
        return success_response(result)
    except Exception as e:
        print(f"ERROR in curriculum_list: {e}")
        return error_response(str(e))


@router.post("/semester_list")
def get_semester_list_post(db: Session = Depends(get_db)):
    try:
        data = db.query(IEMSemester).all()
        result = [
            {
                "value": row.semester_id,
                "label": f"Semester {row.semester}" if row.semester else row.semester_desc,
            }
            for row in data
        ]
        return success_response(result)
    except Exception as e:
        print(f"ERROR in semester_list: {e}")
        return error_response(str(e))


@router.post("/course_list")
def get_course_list(request: CourseListRequest, db: Session = Depends(get_db)):
    """Get all courses - returns courses for selected curriculum"""
    try:
        query = db.query(IEMSCourses)
        
        # Filter by curriculum only
        if request.curriculum_id:
            query = query.filter(IEMSCourses.academic_batch_id == request.curriculum_id)
        
        courses = query.all()
        
        if not courses:
            return success_response([])
            
        result = [
            {
                "value": row.crs_id,
                "label": row.crs_title or f"Course {row.crs_id}",
                "crs_id": row.crs_id,
                "crs_code": row.crs_code,
                "crs_title": row.crs_title,
                "semester": row.semester,
            }
            for row in courses
        ]
        return success_response(result)
    except Exception as e:
        print(f"ERROR in course_list: {e}")
        return error_response(str(e))


@router.post("/section_list_post")
def get_section_list(
    course_id: Optional[int] = Body(None),
    semester_id: Optional[int] = Body(None),
    academic_batch_id: Optional[int] = Body(None),
    db: Session = Depends(get_db)
):
    """Get sections strictly from the allowed IEMSection table (No extra BaseModel required)"""
    try:
        query = db.query(IEMSection)

        if academic_batch_id:
            query = query.filter(IEMSection.academic_batch_id == academic_batch_id)
        if semester_id:
            query = query.filter(IEMSection.semester_id == semester_id)

        sections = query.all()

        if sections:
            return [
                {
                    "value": s.id,
                    "label": s.section or f"Section {s.id}",
                }
                for s in sections
            ]

        # Fallback: return default sections and add them to IEMSection if they don't exist
        default_sections = ["A", "B", "C", "D"]
        result = []
        for section_name in default_sections:
            existing_section = db.query(IEMSection).filter(
                IEMSection.section == section_name
            ).first()

            if existing_section:
                result.append({
                    "value": existing_section.id,
                    "label": existing_section.section
                })
            else:
                new_section = IEMSection(
                    section=section_name,
                    academic_batch_id=academic_batch_id,
                    semester_id=semester_id,
                    status=1
                )
                db.add(new_section)
                db.flush()
                result.append({
                    "value": new_section.id,
                    "label": section_name
                })

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



# =========================================================
# ✅ IMPORT & LISTING
# =========================================================

@router.post("/import_topic")
def import_topic(request: ImportTopicRequest, db: Session = Depends(get_db)):
    """Import selected topics from cudos_topic to lms_map_instructor_topic with exact delta checking"""
    try:
        instructor_id = request.instructor_id

        # 1. Fetch current topics from cudos_topic exactly as the frontend sees them
        # Note: The frontend topic_list API only filters by course_id and semester_id
        # This prevents the bug where newly added topics with mismatched or NULL academic_batch_ids are skipped.
        topic_query = db.query(CudosTopic).filter(
            CudosTopic.course_id == request.course_id,
            CudosTopic.semester_id == request.semester_id
        )
        
        # If client explicitly supplies topic_ids, restrict to those
        if request.topic_ids and len(request.topic_ids) > 0:
            topic_query = topic_query.filter(CudosTopic.topic_id.in_(request.topic_ids))
            
        candidate_topics = topic_query.all()
        
        if not candidate_topics:
            return {
                "success": False,
                "message": "No valid topics found to import",
                "importedTopics": 0,
                "skippedTopics": 0
            }

        candidate_ids = [t.topic_id for t in candidate_topics]

        # 2. Query lms_map_instructor_topic to find which ones are already mapped
        already_mapped_query = db.query(LMSMapInstructorTopic.topic_id).filter(
            LMSMapInstructorTopic.crs_id == request.course_id,
            LMSMapInstructorTopic.section_id == request.section_id,
            LMSMapInstructorTopic.topic_id.in_(candidate_ids)
        ).all()
        
        already_mapped_ids = {row[0] for row in already_mapped_query}

        # 3. Compare and identify new topics (Delta Check)
        new_topics_to_insert = [t for t in candidate_topics if t.topic_id not in already_mapped_ids]

        imported_count = 0
        skipped_count = len(already_mapped_ids)

        if not new_topics_to_insert:
            # Subsequent Click (No Changes) behavior
            return {
                "success": False,
                "message": "Topics already imported",
                "importedTopics": 0,
                "skippedTopics": skipped_count
            }

        # 4. Insert only missing records (idempotent delta behavior)
        insert_mappings = []
        for new_topic in new_topics_to_insert:
            new_mapping = LMSMapInstructorTopic(
                academic_batch_id=request.academic_batch_id,
                semester_id=request.semester_id,
                crs_id=request.course_id,
                section_id=request.section_id,
                topic_id=new_topic.topic_id,
                instructor_id=instructor_id,
                created_by=request.created_by
            )
            insert_mappings.append(new_mapping)
            
        db.bulk_save_objects(insert_mappings)
        db.commit()
        
        imported_count = len(insert_mappings)
        
        # 5. Return structured response (avoiding generic "data" shell that stripping Axios interceptors remove)
        return {
            "success": True,
            "message": "Topics imported successfully",
            "importedTopics": imported_count,
            "skippedTopics": skipped_count
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error during import: {e}")
        return {
            "success": False,
            "message": "Database integrity error - possible foreign key violation",
            "importedTopics": 0,
            "skippedTopics": 0
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Import failed: {e}")
        return {
            "success": False,
            "message": f"Import failed: {str(e)}",
            "importedTopics": 0,
            "skippedTopics": 0
        }

@router.post("/import_selected_topics")
def import_selected_topics(request: ImportCudosTopicsRequest, db: Session = Depends(get_db)):
    """Import selected topics from cudos_topic to lms_map_instructor_topic with idempotency"""
    try:
        logger.info(f"Import selected topics - academic_batch_id={request.academic_batch_id}, course_id={request.course_id}, semester_id={request.semester_id}, section_id={request.section_id}, instructor_id={request.instructor_id}, topic_ids={request.topic_ids}")

        if not request.topic_ids:
            return error_response("No topics selected for import")

        # Verify that all selected topics exist in cudos_topic
        existing_topics = db.query(CudosTopic.topic_id).filter(
            CudosTopic.topic_id.in_(request.topic_ids)
        ).all()
        existing_topic_ids = {row.topic_id for row in existing_topics}

        if len(existing_topic_ids) != len(request.topic_ids):
            missing = set(request.topic_ids) - existing_topic_ids
            logger.warning(f"Some topics do not exist in cudos_topic: {list(missing)}")
            return error_response(f"Some topics do not exist in cudos_topic: {list(missing)}")

        imported_count = 0
        skipped_count = 0

        for topic_id in request.topic_ids:
            # STRICT DUPLICATE CHECK: Is this topic already mapped to this section?
            # We check by topic_id and section_id to ensure a topic is only imported once per section.
            exists = db.query(LMSMapInstructorTopic).filter(
                LMSMapInstructorTopic.topic_id == topic_id,
                LMSMapInstructorTopic.section_id == request.section_id,
                LMSMapInstructorTopic.crs_id == request.course_id,
                LMSMapInstructorTopic.academic_batch_id == request.academic_batch_id
            ).first()

            if exists:
                skipped_count += 1
                logger.info(f"Skipped topic {topic_id} - already exists for instructor {request.instructor_id}")
            else:
                new_mapping = LMSMapInstructorTopic(
                    academic_batch_id=request.academic_batch_id,
                    semester_id=request.semester_id,
                    crs_id=request.course_id,
                    section_id=request.section_id,
                    topic_id=topic_id,
                    instructor_id=request.instructor_id,
                    created_by=request.created_by
                )
                db.add(new_mapping)
                imported_count += 1
                logger.info(f"Imported topic {topic_id} for instructor {request.instructor_id}")

        db.commit()

        logger.info(f"Import completed, {imported_count} new topics imported, {skipped_count} skipped")

        return success_response({
            "imported": imported_count,
            "skipped": skipped_count,
            "total_processed": len(request.topic_ids)
        }, f"Successfully processed {len(request.topic_ids)} topics: {imported_count} imported, {skipped_count} skipped")

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error during import: {e}")
        return error_response("Database integrity error - possible foreign key violation")
    except Exception as e:
        db.rollback()
        logger.error(f"Import error: {e}")
        return error_response(f"Import failed: {str(e)}")

@router.post("/topic_list")
def topic_list(request: TopicListRequest, db: Session = Depends(get_db)):
    # List ALL topics for this course/semester from cudos_topic, with import status
    try:
        from sqlalchemy import or_, and_
        # Base query from cudos_topic
        query = db.query(CudosTopic)

        # 1. Filter by Course/Semester/Batch
        query = query.filter(
            CudosTopic.academic_batch_id == request.academic_batch_id,
            CudosTopic.course_id == request.course_id,
            CudosTopic.semester_id == request.semester_id
        )

        # 2. Visibility Filter: Global OR Created By the current user
        if request.user_id:
            query = query.filter(
                or_(
                    CudosTopic.is_global == True,
                    CudosTopic.created_by == request.user_id
                )
            )

        # 3. Handle Mapping Status (if section_id is provided)
        # We restrict the list to topics associated with this section (imported or portion exists)
        if request.section_id:
            query = query.filter(
                or_(
                    CudosTopic.topic_id.in_(
                        db.query(LMSMapInstructorTopic.topic_id).filter(
                            LMSMapInstructorTopic.section_id == request.section_id,
                            LMSMapInstructorTopic.crs_id == request.course_id
                        )
                    ),
                    CudosTopic.topic_id.in_(
                        db.query(LMSMapPortionLS.topic_id).filter(LMSMapPortionLS.section_id == request.section_id)
                    )
                )
            )
        else:
            # If no section selected, don't show any topics (optional, but safer based on requirements)
            # pass
            pass
        
        # Ensure distinct topics
        query = query.distinct(CudosTopic.topic_id)
        
        topics = query.all()

        print(f"DEBUG: Found {len(topics)} topics in cudos_topic for course_id={request.course_id}, semester_id={request.semester_id}")

        if not topics:
            return success_response([])

        # Get imported mappings for this course/section
        mappings = {}
        if request.section_id:
            imported_mappings = db.query(LMSMapInstructorTopic).filter(
                LMSMapInstructorTopic.academic_batch_id == request.academic_batch_id,
                LMSMapInstructorTopic.crs_id == request.course_id,
                LMSMapInstructorTopic.semester_id == request.semester_id,
                LMSMapInstructorTopic.section_id == request.section_id
            ).all()
            mappings = {m.topic_id: m for m in imported_mappings}

        response = []
        for topic in topics:
            mapping = mappings.get(topic.topic_id)
            
            # Get instructor name if imported OR stored in schedule
            instructor_name = "Not Assigned"
            instructor_id = None
            
            # 1. Check mapping (Imported)
            if mapping and mapping.instructor_id:
                instructor_id = mapping.instructor_id
            
            # 2. If not imported, check schedule (Persisted assignment)
            if not instructor_id:
                # We'll fetch the schedule below, but for instructor name we might need it earlier
                # Search for any schedule for this topic to get the persisted instructor
                persisted_schedule = db.query(TopicLessonSchedule).filter(
                    TopicLessonSchedule.topic_id == topic.topic_id,
                    TopicLessonSchedule.section_id == request.section_id
                ).first()
                if persisted_schedule and persisted_schedule.instructor_id:
                    instructor_id = persisted_schedule.instructor_id

            if instructor_id:
                instructor = db.query(IEMSUsers).filter(
                    IEMSUsers.id == instructor_id
                ).first()
                if instructor:
                    first_name = getattr(instructor, 'first_name', '') or ''
                    last_name = getattr(instructor, 'last_name', '') or ''
                    full_name = f"{first_name} {last_name}".strip()
                    if full_name:
                        instructor_name = full_name

            # Get schedule details (imported or persisted)
            schedule = None
            schedule_query = db.query(TopicLessonSchedule).filter(
                TopicLessonSchedule.topic_id == topic.topic_id
            )
            
            # If mapping exists, try to find schedule for this specific section
            if mapping and request.section_id:
                schedule_query = schedule_query.join(
                    LMSLessonSchedule,
                    LMSLessonSchedule.lls_id == TopicLessonSchedule.lesson_schedule_id
                ).filter(
                    LMSLessonSchedule.section_id == request.section_id
                )
            
            schedule = schedule_query.first()
            
            # If still no schedule (and possibly not imported), just get the record for this topic/section
            if not schedule and request.section_id:
                 schedule = db.query(TopicLessonSchedule).filter(
                    TopicLessonSchedule.topic_id == topic.topic_id,
                    TopicLessonSchedule.section_id == request.section_id
                ).first()

            # Get portion details and lesson schedule
            portion_sql = """
                SELECT portion_ref FROM lms_map_portion_ls 
                WHERE topic_id = :topic_id AND portion_ref IS NOT NULL AND portion_ref != ''
            """
            portion_params = {"topic_id": topic.topic_id}
            if request.section_id:
                portion_sql += " AND section_id = :section_id"
                portion_params["section_id"] = request.section_id

            portion_list_query = db.execute(text(portion_sql), portion_params)
            portion_refs = [r[0] for r in portion_list_query.fetchall() if r[0]]
            lesson_schedule = ", ".join(portion_refs) if portion_refs else None

            # Get marks_expt (handle if column doesn't exist)
            try:
                marks_sql = "SELECT marks_expt FROM lms_map_portion_ls WHERE topic_id = :topic_id"
                marks_params = {"topic_id": topic.topic_id}
                if request.section_id:
                    marks_sql += " AND section_id = :section_id"
                    marks_params["section_id"] = request.section_id
                marks_sql += " LIMIT 1"

                portion_query = db.execute(text(marks_sql), marks_params)
                portion_row = portion_query.fetchone()
                marks_expt = portion_row[0] if portion_row else None
            except Exception as e:
                print(f"Warning: Could not get marks_expt for topic {topic.topic_id}: {e}")
                marks_expt = None

            response.append({
                "topic_id": topic.topic_id,
                "mapping_id": mapping.inst_map_id if mapping else None,
                "inst_map_id": mapping.inst_map_id if mapping else None,
                "topic_code": topic.topic_code,
                "topic_title": topic.topic_title,
                "topic_content": topic.topic_content,
                "topic_hrs": topic.topic_hrs,
                "num_of_sessions": topic.num_of_sessions,
                "section_id": request.section_id,
                "instructor_id": instructor_id,
                "instructor_name": instructor_name,
                "lesson_schedule": lesson_schedule,
                "conduction_date": (schedule.conduction_date.isoformat() if hasattr(schedule.conduction_date, 'isoformat') else str(schedule.conduction_date)) if schedule and schedule.conduction_date else None,
                "actual_delivery_date": (schedule.actual_delivery_date.isoformat() if hasattr(schedule.actual_delivery_date, 'isoformat') else str(schedule.actual_delivery_date)) if schedule and schedule.actual_delivery_date else None,
                "marks_expt": marks_expt,
                "is_imported": mapping is not None  # Add flag to indicate import status
            })
        
        print(f"DEBUG: Returning {len(response)} topics")
        return success_response(response)

    except Exception as e:
        print(f"DEBUG: Error in topic_list: {e}")
        return error_response(str(e))

# -----------------------------
# UPDATE — Topic
# -----------------------------
@router.put("/update_topic/{topic_id}")
def update_topic(topic_id: int, request: TopicCreateRequest, db: Session = Depends(get_db)):
    topic = db.query(CudosTopic).filter(
        CudosTopic.topic_id == topic_id
    ).first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    try:
        topic.topic_code = request.topic_code
        topic.topic_title = request.topic_title
        topic.topic_content = request.topic_content
        topic.academic_batch_id = request.academic_batch_id
        topic.semester_id = request.semester_id
        topic.course_id = request.course_id
        topic.modified_by = request.created_by
        topic.modified_date = date.today()

        db.commit()
        db.refresh(topic)
        print(f"✅ Topic {topic_id} updated successfully")

        return {"message": "Topic updated successfully", "topic_id": topic_id}

    except Exception as e:
        db.rollback()
        print(f"❌ update_topic/{topic_id} ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


# -----------------------------
# DELETE — Topic
# -----------------------------
@router.delete("/delete_topic/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):

    topic = db.query(CudosTopic).filter(
        CudosTopic.topic_id == topic_id
    ).first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    try:
        db.delete(topic)
        db.commit()
        return {"message": "Topic deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# ✅ NEW ENDPOINTS FOR MANAGE TOPIC INSTRUCTOR
# =========================================================

# -----------------------------
# GET INSTRUCTOR LIST
# -----------------------------
@router.get("/instructor_list")
def instructor_list(db: Session = Depends(get_db)):
    try:
        # First try to get instructors from CudosMapCourseToCourseInstructor with DISTINCT
        instructors = db.query(
            CudosMapCourseToCourseInstructor.course_instructor_id,
            IEMSUsers.first_name,
            IEMSUsers.last_name
        ).join(
            IEMSUsers,
            IEMSUsers.id == CudosMapCourseToCourseInstructor.course_instructor_id
        ).distinct().all()

        # If no instructors found, fallback to all users from IEMSUsers
        if not instructors:
            users = db.query(IEMSUsers).all()
            return [
                {
                    "value": u.id,
                    "label": f"{u.first_name} {u.last_name}".strip() or u.username
                }
                for u in users
            ]

        # Use a dict to remove duplicates by instructor_id
        seen = {}
        result = []
        for inst in instructors:
            if inst.course_instructor_id not in seen:
                seen[inst.course_instructor_id] = True
                result.append({
                    "value": inst.course_instructor_id,
                    "label": f"{inst.first_name} {inst.last_name}".strip()
                })

        return result

    except Exception as e:
        print("Error in instructor_list:", e)
        # Fallback: get all users from IEMSUsers
        try:
            users = db.query(IEMSUsers).all()
            return [
                {
                    "value": u.id,
                    "label": f"{u.first_name} {u.last_name}".strip() or u.username
                }
                for u in users
            ]
        except Exception as fallback_error:
            print("Fallback error:", fallback_error)
            raise HTTPException(status_code=500, detail=str(e))
# -----------------------------
# UPDATE INSTRUCTOR
# -----------------------------
@router.put("/update_instructor/{mapping_id}")
def update_instructor(
    mapping_id: int,
    request: UpdateInstructorRequest,
    db: Session = Depends(get_db)
):
    course_instructor_id = request.course_instructor_id or request.instructor_id
    if not course_instructor_id:
        raise HTTPException(status_code=422, detail='instructor_id or course_instructor_id required')
    try:

        mapping = db.query(LMSMapInstructorTopic).filter(
            LMSMapInstructorTopic.inst_map_id == mapping_id
        ).first()

        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")

        mapping.instructor_id = request.course_instructor_id

        db.commit()
        db.refresh(mapping)

        return {
            "status": "success",
            "message": "Instructor updated successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
# -----------------------------
# GET CUDOS TOPICS (Not yet imported)
# -----------------------------
@router.post("/cudos_topics")
def get_cudos_topics(
    course_id: int = Body(...),
    semester_id: int = Body(...),
    section_id: int = Body(...),
    db: Session = Depends(get_db)
):
    """Get topics from cudos_topic that are NOT yet imported for this course/section"""
    try:
        # Get all topic IDs already imported for this course and section
        imported_topic_ids = db.query(LMSMapInstructorTopic.topic_id).filter(
            LMSMapInstructorTopic.crs_id == course_id,
            LMSMapInstructorTopic.section_id == section_id
        ).all()
        
        imported_ids = [t.topic_id for t in imported_topic_ids]
        
        # Get topics from cudos_topic that are NOT imported
        query = db.query(CudosTopic).filter(
            CudosTopic.course_id == course_id,
            CudosTopic.semester_id == semester_id
        )
        
        if imported_ids:
            query = query.filter(~CudosTopic.topic_id.in_(imported_ids))
        
        topics = query.all()
        
        return [
            {
                "topic_id": t.topic_id,
                "topic_code": t.topic_code,
                "topic_title": t.topic_title,
                "topic_hrs": t.topic_hrs,
                "num_of_sessions": t.num_of_sessions
            }
            for t in topics
        ]
    except Exception as e:
        print(f"DEBUG: Error in cudos_topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# IMPORT SELECTED CUDOS TOPICS WITH INSTRUCTOR
# -----------------------------
@router.post("/import_cudos_topics")
def import_cudos_topics(
    course_id: int = Body(...),
    semester_id: int = Body(...),
    section_id: int = Body(...),
    topic_ids: list = Body(...),
    instructor_id: int = Body(...),
    academic_batch_id: int = Body(...),
    created_by: int = Body(1),
    db: Session = Depends(get_db)
):
    """Import selected topics from cudos_topic with instructor assignment"""
    try:
        imported_count = 0
        imported_mappings = []
        
        for topic_id in topic_ids:
            # Check if already imported
            exists = db.query(LMSMapInstructorTopic).filter(
                LMSMapInstructorTopic.topic_id == topic_id,
                LMSMapInstructorTopic.crs_id == course_id,
                LMSMapInstructorTopic.section_id == section_id
            ).first()
            
            if not exists:
                new_mapping = LMSMapInstructorTopic(
                    academic_batch_id=academic_batch_id,
                    semester_id=semester_id,
                    crs_id=course_id,
                    section_id=section_id,
                    topic_id=topic_id,
                    instructor_id=instructor_id,
                    created_by=created_by
                )
                db.add(new_mapping)
                db.flush()  # Get the ID before commit
                imported_mappings.append({
                    "topic_id": topic_id,
                    "mapping_id": new_mapping.inst_map_id
                })
                imported_count += 1
        
        db.commit()
        
        if imported_count == 0:
            return {"status": "success", "message": "All selected topics already imported", "data": []}
        
        return {
            "status": "success", 
            "message": f"Successfully imported {imported_count} topics",
            "data": imported_mappings
        }
    
    except Exception as e:
        db.rollback()
        print(f"DEBUG: Error in import_cudos_topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# GET TOPIC SCHEDULES
# -----------------------------
@router.post("/topic_schedules")
def get_topic_schedules(
    mapping_id: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Get lesson schedules for a specific topic mapping"""
    try:
        # Get the mapping to find the topic_id
        mapping = db.query(LMSMapInstructorTopic).filter(
            LMSMapInstructorTopic.inst_map_id == mapping_id
        ).first()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Topic mapping not found")
        
        # Get schedules for this topic (from topic_lesson_schedule + lms_map_portion_ls for portion_ref)
        from sqlalchemy import text
        schedules = db.query(TopicLessonSchedule).filter(
            TopicLessonSchedule.topic_id == mapping.topic_id
        ).order_by(TopicLessonSchedule.lesson_schedule_id).all()

        # Get all portions for this topic (portion_ref) - match by index with schedules
        portion_refs = []
        try:
            portion_rows = db.execute(text("""
                SELECT portion_ref FROM lms_map_portion_ls 
                WHERE topic_id = :topic_id AND portion_ref IS NOT NULL AND portion_ref != ''
                ORDER BY portion_id
            """), {"topic_id": mapping.topic_id}).fetchall()
            portion_refs = [r[0] for r in portion_rows if r[0]]
        except Exception:
            pass

        result = []
        for idx, s in enumerate(schedules):
            portion_ref = portion_refs[idx] if idx < len(portion_refs) else None
            result.append({
                "schedule_id": s.lesson_schedule_id,
                "topic_id": s.topic_id,
                "session_number": idx + 1,
                "portion_to_be_covered": portion_ref,
                "conduction_date": s.conduction_date.isoformat() if s.conduction_date else None,
                "actual_delivery_date": s.actual_delivery_date.isoformat() if s.actual_delivery_date else None,
            })
        return result
    except Exception as e:
        print(f"DEBUG: Error in topic_schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# UPDATE SCHEDULE
# -----------------------------
@router.put("/update_schedule/{schedule_id}")
def update_schedule(
    schedule_id: int,
    conduction_date: str = Body(None),
    actual_delivery_date: str = Body(None),
    db: Session = Depends(get_db)
):
    """Update a lesson schedule"""
    try:
        schedule = db.query(TopicLessonSchedule).filter(
            TopicLessonSchedule.lesson_schedule_id == schedule_id
        ).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if conduction_date:
            schedule.conduction_date = datetime.strptime(conduction_date, '%Y-%m-%d').date()
        if actual_delivery_date:
            schedule.actual_delivery_date = datetime.strptime(actual_delivery_date, '%Y-%m-%d').date()
        
        db.commit()
        db.refresh(schedule)
        
        return {"status": "success", "message": "Schedule updated successfully"}
    except Exception as e:
        db.rollback()
        print(f"DEBUG: Error in update_schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# UPDATE PORTION
# -----------------------------
@router.put("/update_portion/{portion_id}")
def update_portion(
    portion_id: int,
    portion_ref: Optional[str] = Body(None),
    marks_expt: Optional[float] = Body(None),
    planned_date: str = Body(None),
    db: Session = Depends(get_db)
):
    """Update a portion schedule"""
    try:
        portion = db.query(LMSMapPortionLS).filter(
            LMSMapPortionLS.portion_id == portion_id
        ).first()
        
        if not portion:
            raise HTTPException(status_code=404, detail="Portion not found")
        
        if portion_ref is not None:
            portion.portion_ref = portion_ref
        if planned_date:
            portion.planned_date = datetime.strptime(planned_date, '%Y-%m-%d').date()
        
        db.commit()
        db.refresh(portion)
        
        return {"status": "success", "message": "Portion updated successfully"}
    except Exception as e:
        db.rollback()
        print(f"DEBUG: Error in update_portion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# ADD NEW SCHEDULE
# -----------------------------
@router.post("/add_schedule")
def add_schedule(
    request: AddScheduleRequest,
    db: Session = Depends(get_db)
):
    """Add a new lesson schedule for a topic mapping"""
    try:
        # Get the mapping to find the topic_id and academic_batch_id
        mapping = db.query(LMSMapInstructorTopic).filter(
            LMSMapInstructorTopic.inst_map_id == request.mapping_id
        ).first()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Topic mapping not found")
        
        # Determine academic_batch_id: use request one if provided, else use the one from mapping
        academic_batch_id = request.academic_batch_id or mapping.academic_batch_id
        
        if not academic_batch_id:
            # Should not happen as LMSMapInstructorTopic usually has it, but good to have a check
            raise HTTPException(
                status_code=400, 
                detail="academic_batch_id is required but not provided in request and missing in mapping"
            )

        new_schedule = TopicLessonSchedule(
            topic_id=mapping.topic_id,
            academic_batch_id=academic_batch_id,
            course_id=mapping.crs_id,
            conduction_date=request.conduction_date,
            created_by=request.created_by
        )
        
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)
        
        return {
            "status": "success", 
            "message": "Schedule added successfully",
            "schedule_id": new_schedule.lesson_schedule_id
        }
    except Exception as e:
        db.rollback()
        print(f"DEBUG: Error in add_schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# ADD EXTRA CLASS
# -----------------------------
@router.post("/add_extra_class")
def add_extra_class(
    mapping_id: int = Body(...),
    class_date: str = Body(...),
    start_time: Optional[str] = Body(None),
    end_time: Optional[str] = Body(None),
    notes: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """Add an extra class to topic lesson schedule"""
    try:
        # Get the mapping to find topic_id
        mapping = db.query(LMSMapInstructorTopic).filter(
            LMSMapInstructorTopic.inst_map_id == mapping_id
        ).first()

        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")

        # Create new lesson schedule for extra class
        lesson = TopicLessonSchedule(
            topic_id=mapping.topic_id,
            academic_batch_id=mapping.academic_batch_id,
            course_id=mapping.crs_id,
            conduction_date=datetime.strptime(class_date, "%Y-%m-%d").date() if class_date else None,
            created_by=mapping.created_by
        )

        db.add(lesson)
        db.flush()

        # Add corresponding portion
        portion = LMSMapPortionLS(
            topic_id=mapping.topic_id,
            section_id=mapping.section_id,
            lesson_schedule_id=lesson.lesson_schedule_id,
            portion_ref="Extra",
            portion_per_hour="0",
            planned_date=lesson.conduction_date,
            created_by=mapping.created_by
        )
        db.add(portion)

        db.commit()

        return {"message": "Extra class added successfully", "schedule_id": lesson.lesson_schedule_id}

    except Exception as e:
        db.rollback()
        print(f"ERROR in add_extra_class: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ==============================
# API 13 – Add New Topic
# ==============================
@router.post("/add_new_topic")
def add_new_topic(
    academic_batch_id: int = Body(...),
    semester_id: int = Body(...),
    course_id: int = Body(...),
    section_id: int = Body(...),
    topic_title: str = Body(...),
    topic_code: str = Body(...),
    topic_content: Optional[str] = Body(None),
    topic_hrs: Optional[str] = Body(None),
    num_of_sessions: int = Body(1),
    instructor_id: int = Body(...),
    created_by: int = Body(1),
    is_global: bool = Body(True),
    delivery_date: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """Add a new topic without auto-importing to LMS mapping"""
    try:
        # Create topic in cudos_topic
        new_topic = CudosTopic(
            topic_code=topic_code,
            topic_title=topic_title,
            topic_content=topic_content or "",
            academic_batch_id=academic_batch_id,
            semester_id=semester_id,
            course_id=course_id,
            topic_hrs=topic_hrs,
            num_of_sessions=num_of_sessions,
            conduction_date=datetime.strptime(delivery_date, '%Y-%m-%d').date() if delivery_date else None,
            actual_delivery_date=datetime.strptime(delivery_date, '%Y-%m-%d').date() if delivery_date else None,
            created_by=created_by,
            is_global=is_global,
            created_date=datetime.now()
        )

        db.add(new_topic)
        db.commit()
        db.refresh(new_topic)

        # Decoupled: NOT auto-importing to LMS mapping. Let user approve via "Import Topics".
        
        # Calculate portion_per_hour = topic_hrs / num_of_sessions
        topic_hrs_float = 0.0
        try:
            if topic_hrs:
                topic_hrs_float = float(topic_hrs)
        except (ValueError, TypeError):
            topic_hrs_float = 0.0
            
        num_sessions = int(num_of_sessions) if num_of_sessions and int(num_of_sessions) > 0 else 1
        portion_per_hour = topic_hrs_float / num_sessions

        # Add default topic lesson schedule
        new_schedule = TopicLessonSchedule(
            topic_id=new_topic.topic_id,
            academic_batch_id=academic_batch_id,
            course_id=course_id,
            section_id=section_id,
            portion_per_hour=portion_per_hour,
            conduction_date=new_topic.conduction_date,
            actual_delivery_date=new_topic.actual_delivery_date,
            instructor_id=instructor_id,
            created_by=created_by,
            created_date=datetime.now()
        )
        db.add(new_schedule)
        db.flush()

        # Add default portion
        new_portion = LMSMapPortionLS(
            topic_id=new_topic.topic_id,
            section_id=section_id,
            lesson_schedule_id=new_schedule.lesson_schedule_id,
            portion_ref="",
            portion_per_hour=str(portion_per_hour),
            created_by=created_by,
            created_date=datetime.now()
        )
        db.add(new_portion)

        db.commit()

        return {
            "message": "Topic added successfully (Needs Import)",
            "topic_id": new_topic.topic_id,
            "mapping_id": None
        }

    except Exception as e:
        db.rollback()
        print(f"ERROR in add_new_topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================
# API – Update Mapping (Assign Instructor)
# ==============================
@router.put("/update_mapping/{mapping_id}")
def update_mapping(
    mapping_id: int,
    request: UpdateInstructorRequest,
    db: Session = Depends(get_db)
):
    """Update mapping to assign instructor"""
    instructor_id = request.instructor_id or request.course_instructor_id
    if not instructor_id:
        raise HTTPException(status_code=422, detail="instructor_id or course_instructor_id required")
        
    try:
        mapping = db.query(LMSMapInstructorTopic).filter(
            LMSMapInstructorTopic.inst_map_id == mapping_id
        ).first()
 
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")
 
        mapping.instructor_id = instructor_id
        db.commit()
 
        return {"status": "success", "message": "Instructor assigned successfully"}
 
    except Exception as e:
        db.rollback()
        print(f"ERROR in update_mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))