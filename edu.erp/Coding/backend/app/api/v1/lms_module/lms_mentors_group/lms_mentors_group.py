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
    LMSGroupMentees
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
    mentors_group_id: int
):

    return returnException(
        "Group deletion not allowed"
    )

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

    # 1. Get all groups under academic batch
    groups = db.query(LMSMentorsGroup).filter(
        LMSMentorsGroup.academic_batch_id == academic_batch_id
    ).all()

    if not groups:
        return returnException("No groups found for this academic batch")

    result = []

    for group in groups:

        # 2. Get terms
        terms = db.query(LMSMentorsGroupTerms).filter(
            LMSMentorsGroupTerms.mentors_group_id == group.mentors_group_id
        ).all()

        term_ids = [t.mentors_group_terms_id for t in terms]

        # 3. Get mentors mapped to terms
        group_mentors = db.query(LMSGroupMentors).filter(
            LMSGroupMentors.mentors_group_terms_id.in_(term_ids)
        ).all()

        mentor_ids = [m.group_mentor_id for m in group_mentors]

        # 4. Get mentees
        mentees = []
        if mentor_ids:
            mentees = db.query(LMSGroupMentees).filter(
                LMSGroupMentees.group_mentor_id.in_(mentor_ids)
            ).all()

        # 5. Map mentees to mentor
        mentee_map = {}
        for m in mentees:
            mentee_map.setdefault(m.group_mentor_id, []).append({
                "group_mentee_id": m.group_mentee_id,
                "student_id": m.student_id
            })

        # 6. Build mentors list
        mentors_list = []
        for gm in group_mentors:
            mentors_list.append({
                "group_mentor_id": gm.group_mentor_id,
                "mentor_id": gm.mentor_id,
                "mentors_group_terms_id": gm.mentors_group_terms_id,
                "mentees": mentee_map.get(gm.group_mentor_id, [])
            })

        # 7. Final group structure
        result.append({
            "mentors_group_id": group.mentors_group_id,
            "academic_batch_id": group.academic_batch_id,
            "mentors_pgm_title": group.mentors_pgm_title,
            "config_type_id": group.config_type_id,
            "questionnaire_id": group.questionnaire_id,
            "mentors": mentors_list
        })

    return returnSuccess(result)