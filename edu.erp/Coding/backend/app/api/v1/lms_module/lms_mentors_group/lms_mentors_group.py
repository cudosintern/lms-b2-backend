from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import (
    returnSuccess,
    returnException
)

from app.db.models import (
    LMSMentorsGroup,
    LMSMentorsGroupTerms,
    LMSMapMentor,
    LMSGroupMentors,
    LMSGroupMentees,
    IEMSAcademicBatch,
    IEMSemester,
    IEMStudents,
    IEMSUsers,
    LMSMentoringSchedule,
    LMSMentoringSubGroup,
    LMSMentoringSubGrpDate,
    IEMSDepartment,
    LMSCrossDeptUsers,
    LMSCrossDeptUsersCrclms,
    LMSConfigType
)

from .lms_mentors_group_schema import (
    MentorsGroupCreate,
    MentorMapRequest,
    MenteeMapRequest
)

router = APIRouter()


@router.post("/save_mentors_group")
def save_mentors_group(
    mentors_group_data: MentorsGroupCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user_id = current_user.get("user_id")

    # ADD
    if mentors_group_data.mentors_group_id is None:

        mentors_group = LMSMentorsGroup(
            academic_batch_id=
            mentors_group_data.academic_batch_id,

            config_type_id=
            mentors_group_data.config_type_id,

            questionnaire_id=
            mentors_group_data.questionnaire_id,

            mentors_pgm_title=
            mentors_group_data.mentors_pgm_title,

            created_by=user_id,
            created_date=datetime.now()
        )

        db.add(mentors_group)
        db.commit()
        db.refresh(mentors_group)

        # Save Terms
        for semester_id in mentors_group_data.semester_ids:

            group_term = LMSMentorsGroupTerms(
                mentors_group_id=
                mentors_group.mentors_group_id,

                academic_batch_id=
                mentors_group_data.academic_batch_id,

                semester_id=
                semester_id,

                created_by=user_id,
                created_date=datetime.now()
            )

            db.add(group_term)

        db.commit()

    # EDIT
    else:

        mentors_group = db.query(
            LMSMentorsGroup
        ).filter(
            LMSMentorsGroup.mentors_group_id ==
            mentors_group_data.mentors_group_id
        ).first()

        if not mentors_group:
            return returnException(
                "Mentors Group not found"
            )

        # ONLY GROUP TITLE CAN BE EDITED
        mentors_group.mentors_pgm_title = (
            mentors_group_data.mentors_pgm_title
        )

        mentors_group.modified_by = user_id
        mentors_group.modified_date = datetime.now()

        db.commit()

    return returnSuccess({
        "mentors_group_id":
        mentors_group.mentors_group_id
    })


@router.get("/get_mentors_group_list")
def get_mentors_group_list(
    db: Session = Depends(get_db)
):

    data = db.query(
        LMSMentorsGroup
    ).order_by(
        LMSMentorsGroup.mentors_group_id.desc()
    ).all()

    result = []

    for row in data:

        term_count = db.query(
            LMSMentorsGroupTerms
        ).filter(
            LMSMentorsGroupTerms.mentors_group_id ==
            row.mentors_group_id
        ).count()

        result.append({

            "mentors_group_id":
            row.mentors_group_id,

            "academic_batch_id":
            row.academic_batch_id,

            "config_type_id":
            row.config_type_id,

            "questionnaire_id":
            row.questionnaire_id,

            "mentors_pgm_title":
            row.mentors_pgm_title,

            "term_count":
            term_count
        })

    return returnSuccess(result)


@router.get(
    "/get_mentors_group/{mentors_group_id}"
)
def get_mentors_group(
    mentors_group_id: int,
    db: Session = Depends(get_db)
):

    data = db.query(
        LMSMentorsGroup
    ).filter(
        LMSMentorsGroup.mentors_group_id ==
        mentors_group_id
    ).first()

    if not data:
        return returnException(
            "Record not found"
        )

    terms = db.query(
        LMSMentorsGroupTerms
    ).filter(
        LMSMentorsGroupTerms.mentors_group_id ==
        mentors_group_id
    ).all()

    semester_ids = [
        row.semester_id
        for row in terms
    ]

    return returnSuccess({

        "mentors_group_id":
        data.mentors_group_id,

        "academic_batch_id":
        data.academic_batch_id,

        "config_type_id":
        data.config_type_id,

        "questionnaire_id":
        data.questionnaire_id,

        "mentors_pgm_title":
        data.mentors_pgm_title,

        "semester_ids":
        semester_ids
    })


@router.get(
    "/get_group_complete/{mentors_group_id}"
)
def get_group_complete(
    mentors_group_id: int,
    db: Session = Depends(get_db)
):

    group = db.query(
        LMSMentorsGroup
    ).filter(
        LMSMentorsGroup.mentors_group_id ==
        mentors_group_id
    ).first()

    if not group:
        return returnException(
            "Group not found"
        )

    terms = db.query(
        LMSMentorsGroupTerms
    ).filter(
        LMSMentorsGroupTerms.mentors_group_id ==
        mentors_group_id
    ).all()

    return returnSuccess({

        "group": {

            "mentors_group_id":
            group.mentors_group_id,

            "academic_batch_id":
            group.academic_batch_id,

            "config_type_id":
            group.config_type_id,

            "questionnaire_id":
            group.questionnaire_id,

            "mentors_pgm_title":
            group.mentors_pgm_title
        },

        "semester_ids": [
            row.semester_id
            for row in terms
        ]
    })


@router.delete(
    "/delete_mentors_group/{mentors_group_id}"
)
def delete_mentors_group(
    mentors_group_id: int,
    db: Session = Depends(get_db)
):
    try:
        group = db.query(LMSMentorsGroup).filter(
            LMSMentorsGroup.mentors_group_id == mentors_group_id
        ).first()

        if not group:
            return returnException("Group not found")

        terms = db.query(LMSMentorsGroupTerms).filter(
            LMSMentorsGroupTerms.mentors_group_id == mentors_group_id
        ).all()
        term_ids = [t.mentors_group_terms_id for t in terms]

        if term_ids:
            group_mentors = db.query(LMSGroupMentors).filter(
                LMSGroupMentors.mentors_group_terms_id.in_(term_ids)
            ).all()
            group_mentor_ids = [gm.group_mentor_id for gm in group_mentors]

            if group_mentor_ids:
                db.query(LMSGroupMentees).filter(
                    LMSGroupMentees.group_mentor_id.in_(group_mentor_ids)
                ).delete(synchronize_session=False)

            db.query(LMSGroupMentees).filter(
                LMSGroupMentees.mentors_group_terms_id.in_(term_ids)
            ).delete(synchronize_session=False)

            db.query(LMSGroupMentors).filter(
                LMSGroupMentors.mentors_group_terms_id.in_(term_ids)
            ).delete(synchronize_session=False)

            db.query(LMSMentorsGroupTerms).filter(
                LMSMentorsGroupTerms.mentors_group_id == mentors_group_id
            ).delete(synchronize_session=False)

        db.query(LMSMapMentor).filter(
            LMSMapMentor.mentors_group_id == mentors_group_id
        ).delete(synchronize_session=False)

        db.delete(group)
        db.commit()

        return returnSuccess("Mentoring group deleted successfully.")

    except Exception as e:
        db.rollback()
        return returnException(str(e))

@router.post("/map_mentors")
def map_mentors(
    request: MentorMapRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user_id = current_user.get("user_id")

    group = db.query(
        LMSMentorsGroup
    ).filter(
        LMSMentorsGroup.mentors_group_id ==
        request.mentors_group_id
    ).first()

    if not group:
        return returnException(
            "Mentors Group not found"
        )

    terms = db.query(
        LMSMentorsGroupTerms
    ).filter(
        LMSMentorsGroupTerms.mentors_group_id ==
        request.mentors_group_id
    ).all()

    if not terms:
        return returnException(
            "No terms mapped to this group"
        )

    records_created = 0

    for mentor_id in request.mentor_ids:

        # Save group ↔ mentor mapping
        mentor_exists = db.query(
            LMSMapMentor
        ).filter(
            LMSMapMentor.mentors_group_id ==
            request.mentors_group_id,

            LMSMapMentor.mentor_id ==
            mentor_id
        ).first()

        if not mentor_exists:

            mentor_map = LMSMapMentor(
                mentors_group_id=
                request.mentors_group_id,

                mentor_id=
                mentor_id,

                created_by=user_id
            )

            db.add(mentor_map)

        # Save term ↔ mentor mapping
        for term in terms:
            exists = db.query(
                LMSGroupMentors
            ).filter(
                LMSGroupMentors.mentors_group_terms_id ==
                term.mentors_group_terms_id,

                LMSGroupMentors.mentor_id ==
                mentor_id
            ).first()

            if exists:
                continue
          
            group_mentor = LMSGroupMentors(
                mentors_group_terms_id=
                term.mentors_group_terms_id,

                mentor_id=
                mentor_id,

                created_by=user_id,
                created_date=datetime.now()
            )

            db.add(group_mentor)

            records_created += 1

    db.commit()

    return returnSuccess({
        "records_created": records_created
    })

@router.get(
    "/get_group_mentors/{mentors_group_id}"
)
def get_group_mentors(
    mentors_group_id: int,
    db: Session = Depends(get_db)
):

    mentors = db.query(
        LMSMapMentor
    ).filter(
        LMSMapMentor.mentors_group_id ==
        mentors_group_id
    ).all()

    result = []

    for row in mentors:

        result.append({
            "map_mentor_id":
            row.map_mentor_id,

            "mentor_id":
            row.mentor_id,

            "mentors_group_id":
            row.mentors_group_id
        })

    return returnSuccess(result)

@router.delete(
    "/delete_mentor/{map_mentor_id}"
)
def delete_mentor(
    map_mentor_id: int,
    db: Session = Depends(get_db)
):

    mentor = db.query(
        LMSMapMentor
    ).filter(
        LMSMapMentor.map_mentor_id ==
        map_mentor_id
    ).first()

    if not mentor:
        return returnException(
            "Mentor mapping not found"
        )

    db.delete(mentor)
    db.commit()

    return returnSuccess(
        "Mentor deleted successfully"
    )

# @router.post("/map_mentees")
# def map_mentees(
#     request: MenteeMapRequest,
#     current_user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):

#     user_id = current_user.get("user_id")

#     records_created = 0

#     for mentor_id in request.mentor_ids:

#         mentor_rows = db.query(
#             LMSGroupMentors
#         ).filter(
#             LMSGroupMentors.mentor_id == mentor_id
#         ).all()

#         if not mentor_rows:
#             continue

#         for mentor_row in mentor_rows:

#             for mentee_id in request.mentee_ids:

#                 exists = db.query(
#                     LMSGroupMentees
#                 ).filter(
#                     LMSGroupMentees.group_mentor_id ==
#                     mentor_row.group_mentor_id,

#                     LMSGroupMentees.student_id ==
#                     mentee_id
#                 ).first()

#                 if exists:
#                     continue

#                 mentee = LMSGroupMentees(

#                     mentors_group_terms_id=
#                     mentor_row.mentors_group_terms_id,

#                     group_mentor_id=
#                     mentor_row.group_mentor_id,

#                     student_id=
#                     mentee_id,

#                     created_by=
#                     user_id,

#                     created_date=
#                     datetime.now()
#                 )

#                 db.add(mentee)

#                 records_created += 1

#     db.commit()

#     return returnSuccess({
#         "records_created": records_created
#     })

@router.post("/map_mentees")
def map_mentees(
    request: MenteeMapRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user_id = current_user.get("user_id")

    # 1. Get all mentor rows in one go
    mentor_rows = db.query(LMSGroupMentors).filter(
        LMSGroupMentors.mentor_id.in_(request.mentor_ids)
    ).all()

    if not mentor_rows:
        return returnException("No mentors found for given mentor_ids")

    records_created = 0

    # 2. Preload existing mentee mappings (avoid repeated queries)
    existing = db.query(LMSGroupMentees).filter(
        LMSGroupMentees.group_mentor_id.in_(
            [m.group_mentor_id for m in mentor_rows]
        ),
        LMSGroupMentees.student_id.in_(request.mentee_ids)
    ).all()

    existing_set = {
        (e.group_mentor_id, e.student_id)
        for e in existing
    }

    # 3. Insert new mappings
    for mentor_row in mentor_rows:

        for mentee_id in request.mentee_ids:

            key = (mentor_row.group_mentor_id, mentee_id)

            if key in existing_set:
                continue

            mentee = LMSGroupMentees(
                mentors_group_terms_id=mentor_row.mentors_group_terms_id,
                group_mentor_id=mentor_row.group_mentor_id,
                student_id=mentee_id,
                created_by=user_id,
                created_date=datetime.now()
            )

            db.add(mentee)
            records_created += 1

    db.commit()

    return returnSuccess({
        "records_created": records_created
    })

@router.get(
    "/get_group_mentees/{mentors_group_id}"
)
def get_group_mentees(
    mentors_group_id: int,
    db: Session = Depends(get_db)
):

    terms = db.query(
        LMSMentorsGroupTerms
    ).filter(
        LMSMentorsGroupTerms.mentors_group_id ==
        mentors_group_id
    ).all()

    term_ids = [
        row.mentors_group_terms_id
        for row in terms
    ]

    mentors = db.query(
        LMSGroupMentors
    ).filter(
        LMSGroupMentors.mentors_group_terms_id.in_(
            term_ids
        )
    ).all()

    mentor_ids = [
        row.group_mentor_id
        for row in mentors
    ]

    mentees = db.query(
        LMSGroupMentees
    ).filter(
        LMSGroupMentees.group_mentor_id.in_(
            mentor_ids
        )
    ).all()

    result = []

    for row in mentees:

        result.append({
            "group_mentee_id":
            row.group_mentee_id,

            "student_id":
            row.student_id,

            "group_mentor_id":
            row.group_mentor_id
        })

    return returnSuccess(result)

@router.delete(
    "/delete_mentee/{group_mentee_id}"
)
def delete_mentee(
    group_mentee_id: int,
    db: Session = Depends(get_db)
):

    mentee = db.query(
        LMSGroupMentees
    ).filter(
        LMSGroupMentees.group_mentee_id ==
        group_mentee_id
    ).first()

    if not mentee:
        return returnException(
            "Mentee mapping not found"
        )

    db.delete(mentee)
    db.commit()

    return returnSuccess(
        "Mentee deleted successfully"
    )

@router.get("/get_groups_by_academic_batch/{academic_batch_id}")
def get_groups_by_academic_batch(
    academic_batch_id: int,
    db: Session = Depends(get_db)
):
    try:

        # groups = db.query(
        #     LMSMentorsGroup
        # ).filter(
        #     LMSMentorsGroup.academic_batch_id == academic_batch_id
        # ).all()

        groups = (
            db.query(
                LMSMentorsGroup,
                LMSConfigType
            )
            .outerjoin(
                LMSConfigType,
                LMSConfigType.config_type_id ==
                LMSMentorsGroup.config_type_id
            )
            .filter(
                LMSMentorsGroup.academic_batch_id == academic_batch_id
            )
            .all()
        )

        if not groups:
            return returnException(
                "No groups found for this academic batch"
            )

        result = []

        for group, config in groups:

            # Get all terms of this group
            terms = db.query(
                LMSMentorsGroupTerms
            ).filter(
                LMSMentorsGroupTerms.mentors_group_id ==
                group.mentors_group_id
            ).all()

            term_ids = [
                t.mentors_group_terms_id
                for t in terms
            ]

            if not term_ids:

                result.append({
                    "mentors_group_id": group.mentors_group_id,
                    "academic_batch_id": group.academic_batch_id,
                    "mentors_pgm_title": group.mentors_pgm_title,
                    "config_type": {
                        "config_type_id": config.config_type_id if config else None,
                        "config_type_name": config.config_type_name if config else None,
                        "min_mentees": config.min_mentees if config else None,
                        "max_mentees": config.max_mentees if config else None,
                        "allow_mentee_rating": config.allow_mentee_rating if config else None
                    },
                    "questionnaire_id": group.questionnaire_id,
                    "mentors": []
                })

                continue

            # Get mentors with names
            mentor_rows = (
                db.query(
                    LMSGroupMentors,
                    IEMSUsers.first_name,
                    IEMSUsers.last_name
                )
                .join(
                    IEMSUsers,
                    IEMSUsers.id ==
                    LMSGroupMentors.mentor_id
                )
                .filter(
                    LMSGroupMentors.mentors_group_terms_id.in_(term_ids)
                )
                .all()
            )

            mentor_group_ids = [
                row.group_mentor.group_mentor_id
                if hasattr(row, "group_mentor")
                else row[0].group_mentor_id
                for row in mentor_rows
            ]

            # Get mentees with details
            mentee_rows = []

            if mentor_group_ids:

                mentee_rows = (
                    db.query(
                        LMSGroupMentees,
                        IEMStudents.usno,
                        IEMStudents.name,
                        IEMStudents.email
                    )
                    .join(
                        IEMStudents,
                        IEMStudents.student_id ==
                        LMSGroupMentees.student_id
                    )
                    .filter(
                        LMSGroupMentees.group_mentor_id.in_(mentor_group_ids)
                    )
                    .all()
                )

            # Build mentee map
            mentee_map = {}

            for gm, usn, name, email in mentee_rows:

                mentee_map.setdefault(
                    gm.group_mentor_id,
                    []
                ).append({

                    "group_mentee_id": gm.group_mentee_id,

                    "student_id": gm.student_id,

                    "usn": usn,

                    "student_name": name,

                    "email": email

                })

            mentors = []

            for mentor_row in mentor_rows:

                gm = mentor_row[0]
                first_name = mentor_row[1]
                last_name = mentor_row[2]

                term = next(
                    (
                        t for t in terms
                        if t.mentors_group_terms_id ==
                        gm.mentors_group_terms_id
                    ),
                    None
                )

                mentors.append({

                    "group_mentor_id":
                        gm.group_mentor_id,

                    "mentor_id":
                        gm.mentor_id,

                    "mentor_name":
                        f"{first_name or ''} {last_name or ''}".strip(),

                    "mentors_group_terms_id":
                        gm.mentors_group_terms_id,

                    "semester_id":
                        term.semester_id if term else None,

                    "mentees":
                        mentee_map.get(
                            gm.group_mentor_id,
                            []
                        )

                })

            # 7. Get mentoring mentoring_sessions for this group
            mentoring_sessions = db.query(LMSMentoringSchedule).join(
                LMSMentorsGroupTerms,
                LMSMentorsGroupTerms.mentors_group_terms_id ==
                LMSMentoringSchedule.mentors_group_terms_id
            ).filter(
                LMSMentorsGroupTerms.mentors_group_id ==
                group.mentors_group_id
            ).all()

            mentoring_session_list = []

            for mentor_session in mentoring_sessions:

                sub_groups = db.query(LMSMentoringSubGroup).filter(
                    LMSMentoringSubGroup.schedule_id ==
                    mentor_session.schedule_id
                ).all()

                subgroup_data = []

                for sg in sub_groups:

                    dates = db.query(
                        LMSMentoringSubGrpDate
                    ).filter(
                        LMSMentoringSubGrpDate.sub_group_id ==
                        sg.sub_group_id
                    ).all()

                    subgroup_data.append({
                        "sub_group_id": sg.sub_group_id,
                        "sub_group_name": sg.sub_group_name,
                        "location": sg.location,
                        "dates": [
                            {
                                "sub_group_date_id": d.sub_group_date_id,
                                "start_date": d.start_date,
                                "end_date": d.end_date,
                                "start_time": d.start_time,
                                "end_time": d.end_time,
                                "status": d.status
                            }
                            for d in dates
                        ]
                    })

                mentoring_session_list.append({
                    "schedule_id": mentor_session.schedule_id,
                    "session_agenda": mentor_session.session_agenda,
                    "sub_groups": subgroup_data
                })

            result.append({
                "mentors_group_id": group.mentors_group_id,
                "academic_batch_id": group.academic_batch_id,
                "mentors_pgm_title": group.mentors_pgm_title,
                "config_type_id": group.config_type_id,
                "questionnaire_id": group.questionnaire_id,
                "mentors": mentors,
                "mentoring_sessions": mentoring_session_list
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))

@router.get("/get_academic_batch_list")
def get_academic_batch_list(
    db: Session = Depends(get_db)
):

    academic_batches = db.query(
        IEMSAcademicBatch
    ).filter(
        IEMSAcademicBatch.status == 1
    ).order_by(
        IEMSAcademicBatch.academic_batch_desc.asc()
    ).all()

    result = []

    for row in academic_batches:

        result.append({

            "academic_batch_id":
            row.academic_batch_id,

            "academic_batch_code":
            row.academic_batch_code,

            "academic_batch_desc":
            row.academic_batch_desc,

            "academic_year":
            row.academic_year,

            "total_terms":
            row.total_terms
        })

    return returnSuccess(result)

@router.get(
    "/get_semesters_by_academic_batch/{academic_batch_id}"
)
def get_semesters_by_academic_batch(
    academic_batch_id: int,
    db: Session = Depends(get_db)
):

    academic_batch = db.query(
        IEMSAcademicBatch
    ).filter(
        IEMSAcademicBatch.academic_batch_id ==
        academic_batch_id
    ).first()

    if not academic_batch:
        return returnException(
            "Academic Batch not found"
        )

    semesters = db.query(
        IEMSemester
    ).filter(
        IEMSemester.academic_batch_id ==
        academic_batch_id
    ).order_by(
        IEMSemester.semester.asc()
    ).all()

    result = []

    for row in semesters:

        result.append({

            "semester_id":
            row.semester_id,

            "semester":
            row.semester,

            "semester_code":
            row.semester_code,

            "semester_desc":
            row.semester_desc,

            "term_name":
            row.term_name,

            "program_year":
            row.program_year,

            "academic_start_year":
            row.academic_start_year,

            "academic_end_year":
            row.academic_end_year
        })

    return returnSuccess(result)

@router.get("/get_all_mentors/{academic_batch_id}")
def get_all_mentors(
    academic_batch_id: int,
    db: Session = Depends(get_db)
):
    try:

        # -------------------------------------------------
        # Get department of selected academic batch
        # -------------------------------------------------

        batch = db.query(
            IEMSAcademicBatch
        ).filter(
            IEMSAcademicBatch.academic_batch_id == academic_batch_id
        ).first()

        if not batch:
            return returnException("Academic batch not found")

        dept_id = batch.dept_id      # or batch.base_dept_id

        # -------------------------------------------------
        # Native department faculty
        # -------------------------------------------------

        native = db.query(
            IEMSUsers.id.label("mentor_id"),
            IEMSUsers.title,
            IEMSUsers.first_name,
            IEMSUsers.last_name,
            IEMSUsers.email,
            IEMSUsers.mobile,
            IEMSDepartment.dept_name.label("department_name")
        ).join(
            IEMSDepartment,
            IEMSDepartment.dept_id == IEMSUsers.base_dept_id
        ).filter(
            IEMSUsers.active == 1,
            IEMSUsers.base_dept_id == dept_id
        ).order_by(
            IEMSUsers.first_name
        ).all()

        # -------------------------------------------------
        # Imported faculty
        # -------------------------------------------------

        imported = db.query(
            IEMSUsers.id.label("mentor_id"),
            IEMSUsers.title,
            IEMSUsers.first_name,
            IEMSUsers.last_name,
            IEMSUsers.email,
            IEMSUsers.mobile,

            IEMSDepartment.dept_name.label("department_name"),

            LMSCrossDeptUsers.from_dept_id,
            LMSCrossDeptUsers.to_dept_id

        ).join(
            LMSCrossDeptUsers,
            LMSCrossDeptUsers.faculty_user_id ==
            IEMSUsers.id
        ).join(
            LMSCrossDeptUsersCrclms,
            LMSCrossDeptUsersCrclms.cross_dept_id ==
            LMSCrossDeptUsers.cross_dept_id
        ).join(
            IEMSDepartment,
            IEMSDepartment.dept_id ==
            LMSCrossDeptUsers.from_dept_id
        ).filter(

            LMSCrossDeptUsers.to_dept_id == dept_id,

            LMSCrossDeptUsersCrclms.academic_batch_id ==
            academic_batch_id,

            IEMSUsers.active == 1

        ).order_by(
            IEMSUsers.first_name
        ).all()

        # -------------------------------------------------
        # Already mapped groups
        # -------------------------------------------------

        mentor_groups = db.query(

            LMSGroupMentors.mentor_id,

            LMSMentorsGroup.mentors_group_id,

            LMSMentorsGroup.mentors_pgm_title

        ).join(

            LMSMentorsGroupTerms,
            LMSMentorsGroupTerms.mentors_group_terms_id ==
            LMSGroupMentors.mentors_group_terms_id

        ).join(

            LMSMentorsGroup,
            LMSMentorsGroup.mentors_group_id ==
            LMSMentorsGroupTerms.mentors_group_id

        ).filter(

            LMSMentorsGroup.academic_batch_id ==
            academic_batch_id

        ).all()

        mentor_map = {}

        for row in mentor_groups:

            mentor_map.setdefault(
                row.mentor_id,
                []
            ).append({
                "mentor_group_id":
                    row.mentors_group_id,

                "mentor_group_name":
                    row.mentors_pgm_title
            })

        result = []

        # ---------------- Native faculty ----------------

        for m in native:

            result.append({

                "mentor_id":
                    m.mentor_id,

                "title":
                    m.title,

                "mentor_name":
                    f"{m.first_name} {m.last_name or ''}".strip(),

                "email":
                    m.email,

                "mobile":
                    m.mobile,

                "department":
                    m.department_name,

                "is_cross_department":
                    False,

                "mapped_groups":
                    mentor_map.get(
                        m.mentor_id,
                        []
                    )

            })

        # ---------------- Imported faculty ----------------

        for m in imported:

            result.append({

                "mentor_id":
                    m.mentor_id,

                "title":
                    m.title,

                "mentor_name":
                    f"{m.first_name} {m.last_name or ''}".strip(),

                "email":
                    m.email,

                "mobile":
                    m.mobile,

                "department":
                    m.department_name,

                "is_cross_department":
                    True,

                "mapped_groups":
                    mentor_map.get(
                        m.mentor_id,
                        []
                    )

            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))

@router.get("/get_all_mentees")
def get_all_mentees(
    academic_batch_id: int,
    db: Session = Depends(get_db)
):
    try:

        students = (
            db.query(
                IEMStudents.student_id,
                IEMStudents.usno,
                IEMStudents.name,
                IEMStudents.email
            )
            .filter(
                IEMStudents.academic_batch_id == academic_batch_id,
                IEMStudents.status == 1
            )
            .order_by(IEMStudents.name)
            .all()
        )

        result = []

        for student in students:
            result.append({
                "student_id": student.student_id,
                "usn": student.usno,
                "name": student.name,
                "email": student.email
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))
    
@router.get("/get_config_types")
def get_config_types(
    db: Session = Depends(get_db)
):
    try:

        config_types = (
            db.query(LMSConfigType)
            .order_by(LMSConfigType.config_type)
            .all()
        )

        result = []

        for config in config_types:

            result.append({
                "config_type_id": config.config_type_id,
                "config_type_name": config.config_type_name,
                "min_mentees": config.min_mentees,
                "max_mentees": config.max_mentees,
                "allow_mentee_rating": bool(config.allow_mentee_rating),
                "rating_type_id": config.rating_type_id
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))