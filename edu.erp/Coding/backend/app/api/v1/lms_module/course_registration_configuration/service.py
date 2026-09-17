from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import load_only

from app.db.models import (
    IEMSAcademicBatch as Batch, IEMSemester as Term, IEMSCourses as Course,
    IEMSCourseType as CourseType,
    CudosMapCoursetoStudent as Enrollment, MasterType, MasterTypeDetails,
    LMSAcademicBatchSemesterCrsStructure as Structure, IEMOrgConfigs,
    CudosMapCoursetoCourseInstructor as Instructor,
)
from .validation import validate_configuration, validate_courses


def number(value):
    return float(value or 0)


def combined(day, clock):
    return datetime.combine(day, clock) if day is not None and clock is not None else None


# Verified codes in iems_course_type. This table has no crclm_component_id in the target DB.
COURSE_TYPE_ALIASES = {
    "OE": "OPEN_ELECTIVE", "OE1": "OPEN_ELECTIVE", "OE2": "OPEN_ELECTIVE",
    "CE": "ELECTIVE", "CE1": "ELECTIVE", "CE2": "ELECTIVE",
    "PE": "ELECTIVE", "PE1": "ELECTIVE", "PE2": "ELECTIVE",
    "OPEN_ELECTIVE": "OPEN_ELECTIVE", "ELECTIVE": "ELECTIVE",
}


class RegistrationService:
    def __init__(self, db, actor):
        self.db, self.actor = db, actor

    def settings(self):
        rows = self.db.query(IEMOrgConfigs).filter(
            IEMOrgConfigs.org_id == self.actor["org_id"],
            IEMOrgConfigs.program_id.is_(None), IEMOrgConfigs.crs_code.is_(None),
            IEMOrgConfigs.config_type.in_(["enable_crs_reg_by_stud", "lms_stud_crs_reg"]),
        ).all()
        # Defaults explicitly selected for this migration: enabled, credit-based registration.
        values = {"enable_crs_reg_by_stud": "1", "lms_stud_crs_reg": "1"}
        keys = [row.config_type for row in rows]
        values.update({row.config_type: row.value for row in rows})
        if len(keys) != len(set(keys)) or any(value not in ("0", "1") for value in values.values()):
            raise HTTPException(409, "Organisation registration settings must have unique keys and values of 0 or 1.")
        if values["enable_crs_reg_by_stud"] != "1":
            raise HTTPException(403, "Student course registration is disabled for this organisation.")
        return {"enabled": True, "mode": "credits" if values["lms_stud_crs_reg"] == "1" else "courses"}

    def batches(self):
        query = self.db.query(Batch).filter(Batch.org_id == self.actor["org_id"], Batch.status == 1)
        if not self.actor["all_departments"]:
            query = query.filter(Batch.dept_id == self.actor["department_id"])
        if self.actor["instructor_only"]:
            query = query.filter(Batch.academic_batch_id.in_(select(Instructor.academic_batch_id).where(
                Instructor.course_instructor_id == self.actor["user_id"])))
        return query

    def batch(self, batch_id):
        row = self.batches().filter(Batch.academic_batch_id == batch_id).first()
        if row is None:
            raise HTTPException(404, "Curriculum not found or inaccessible.")
        return row

    def term(self, batch_id, term_id, lock=False):
        self.batch(batch_id)
        query = self.db.query(Term).filter(Term.academic_batch_id == batch_id,
            Term.semester_id == term_id, Term.org_id == self.actor["org_id"], Term.status == 1)
        if lock:
            query = query.with_for_update()
        row = query.first()
        if row is None:
            raise HTTPException(404, "Term not found for this curriculum.")
        if row.semester is None:
            raise HTTPException(409, "Set the semester number before configuring registration.")
        return row

    def courses_query(self, term):
        return self.db.query(Course).options(load_only(Course.crs_id, Course.crs_code, Course.crs_title,
            Course.course_type_id, Course.total_credits, Course.total_stud_enroll, Course.reg_start_date,
            Course.reg_end_date)).filter(Course.academic_batch_id == term.academic_batch_id,
            Course.semester == term.semester, Course.org_id == self.actor["org_id"], Course.status > 0)

    def course_rows(self, term):
        rows = self.courses_query(term).add_entity(CourseType).options(
            load_only(CourseType.course_type_id, CourseType.course_type_desc, CourseType.course_type_code)).join(
            CourseType, CourseType.course_type_id == Course.course_type_id).order_by(CourseType.course_type_desc, Course.crs_code).all()
        return [(course, kind, SimpleNamespace(crclm_comp_alias_name=COURSE_TYPE_ALIASES.get(kind.course_type_code.upper(), "CORE")))
            for course, kind in rows]

    def enrollment_rows(self, term):
        statuses = select(MasterTypeDetails.mt_details_id).join(
            MasterType, MasterType.master_type_id == MasterTypeDetails.master_type_id).where(
            MasterType.master_type_name == "student_registration_status", MasterTypeDetails.mt_details_name != "Unregistered")
        return self.db.query(Enrollment.student_id, Enrollment.crs_id, Course.course_type_id,
            Course.total_credits).join(Course, Course.crs_id == Enrollment.crs_id).filter(
            Enrollment.academic_batch_id == term.academic_batch_id, Enrollment.semester_id == term.semester_id,
            Enrollment.status.in_(statuses), Course.org_id == self.actor["org_id"]).all()

    def summary(self, batch_id, term_id, term=None):
        settings = self.settings()
        term = term or self.term(batch_id, term_id)
        courses = self.course_rows(term)
        structures = {row.crs_type_id: row for row in self.db.query(Structure).filter(
            Structure.academic_batch_id == batch_id, Structure.semester_id == term_id).all()}
        per_student, per_type_student, per_type_count = defaultdict(Decimal), defaultdict(Decimal), defaultdict(int)
        for student, _, type_id, credits in self.enrollment_rows(term):
            amount = Decimal(str(credits or 0)) if settings["mode"] == "credits" else Decimal(1)
            per_student[student] += amount
            per_type_student[(type_id, student)] += amount
            per_type_count[type_id] += 1
        grouped = {}
        for course, kind, component in courses:
            amount = Decimal(str(course.total_credits or 0)) if settings["mode"] == "credits" else Decimal(1)
            if kind.course_type_id not in grouped:
                saved = structures.get(kind.course_type_id)
                grouped[kind.course_type_id] = {
                    "course_type_id": kind.course_type_id, "name": kind.course_type_desc,
                    "alias": component.crclm_comp_alias_name if component else "",
                    "total": 0, "minimum_allowed": amount if settings["mode"] == "credits" else 0,
                    "minimum": number(saved.stud_min_crs_enroll) if saved else None,
                    "maximum": number(saved.stud_max_crs_enroll) if saved else None,
                    "registered": per_type_count[kind.course_type_id],
                    "max_registered": number(max((value for (type_id, _), value in per_type_student.items() if type_id == kind.course_type_id), default=0)),
                }
            row = grouped[kind.course_type_id]
            row["total"] += amount
            if settings["mode"] == "credits":
                row["minimum_allowed"] = min(row["minimum_allowed"], amount)
        total_available = number(sum(row["total"] for row in grouped.values()))
        for row in grouped.values():
            row["total"], row["minimum_allowed"] = number(row["total"]), number(row["minimum_allowed"])
        return {
            **settings, "academic_batch_id": batch_id, "semester_id": term_id,
            "curriculum_name": self.batch(batch_id).academic_batch_desc,
            "term_name": term.term_name or term.semester_desc or term.semester_code,
            "total_available": total_available,
            "max_registered": number(max(per_student.values(), default=0)),
            "saved": term.total_crs_enroll is not None and term.enroll_end_date is not None,
            "start": combined(term.enroll_start_date, term.enroll_start_time),
            "end": combined(term.enroll_end_date, term.enroll_end_time),
            "total": number(term.total_crs_enroll) if term.total_crs_enroll is not None else None,
            "own_electives": term.own_crclm_elective or 0, "other_electives": term.other_crclm_elective or 0,
            "types": list(grouped.values()),
        }

    def course_details(self, batch_id, term_id, type_id, term=None):
        term = term or self.term(batch_id, term_id)
        registered = defaultdict(int)
        for _, course_id, _, _ in self.enrollment_rows(term):
            registered[course_id] += 1
        result = []
        for course, kind, component in self.course_rows(term):
            if kind.course_type_id == type_id:
                result.append({"course_id": course.crs_id, "code": course.crs_code, "title": course.crs_title,
                    "credits": number(course.total_credits), "capacity": course.total_stud_enroll,
                    "start": course.reg_start_date, "end": course.reg_end_date,
                    "registered": registered[course.crs_id], "alias": component.crclm_comp_alias_name if component else ""})
        if not result:
            raise HTTPException(404, "No courses found for this course type in the selected term.")
        return result

    def save_configuration(self, batch_id, term_id, payload):
        try:
            term = self.term(batch_id, term_id, lock=True)
            summary = self.summary(batch_id, term_id, term)
            validate_configuration(payload, summary)
            for course, _, component in self.course_rows(term):
                if component and component.crclm_comp_alias_name == "OPEN_ELECTIVE" and (course.reg_start_date or course.reg_end_date):
                    if not course.reg_start_date or not course.reg_end_date or not payload.start <= course.reg_start_date < course.reg_end_date <= payload.end:
                        raise ValueError(f"{course.crs_code}: existing course registration dates fall outside the proposed term window.")
            # All validation precedes writes. Totals are recomputed, never trusted from the browser.
            totals = {row["course_type_id"]: Decimal(str(row["total"])) for row in summary["types"]}
            if any(value > Decimal("99.9") for value in totals.values()):
                raise ValueError("Course type totals exceed the existing NUMERIC(3,1) storage limit; widen the structure columns before saving.")
            self.db.query(Structure).filter(Structure.academic_batch_id == batch_id, Structure.semester_id == term_id).delete(synchronize_session=False)
            for limit in payload.limits:
                self.db.add(Structure(academic_batch_id=batch_id, semester_id=term_id, crs_type_id=limit.course_type_id,
                    crs_type_total=totals[limit.course_type_id], stud_min_crs_enroll=limit.minimum,
                    stud_max_crs_enroll=limit.maximum, created_by=self.actor["user_id"], created_date=datetime.now()))
            term.enroll_start_date, term.enroll_start_time = payload.start.date(), payload.start.time()
            term.enroll_end_date, term.enroll_end_time = payload.end.date(), payload.end.time()
            term.total_crs_enroll = payload.total
            term.own_crclm_elective, term.other_crclm_elective = payload.own_electives, payload.other_electives
            term.modified_by, term.modify_date = self.actor["user_id"], datetime.now()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return {"message": "Registration configuration saved."}

    def save_courses(self, batch_id, term_id, type_id, payload):
        try:
            term = self.term(batch_id, term_id, lock=True)
            self.settings()
            self.courses_query(term).filter(Course.course_type_id == type_id).with_for_update().all()
            rows = self.course_details(batch_id, term_id, type_id, term)
            validate_courses(payload, rows, combined(term.enroll_start_date, term.enroll_start_time), combined(term.enroll_end_date, term.enroll_end_time))
            known = {row["course_id"]: row for row in rows}
            courses = {row.crs_id: row for row in self.courses_query(term).filter(Course.course_type_id == type_id).all()}
            for item in payload.courses:
                course = courses[item.course_id]
                course.total_stud_enroll = item.capacity
                if known[item.course_id]["alias"] == "OPEN_ELECTIVE":
                    course.reg_start_date, course.reg_end_date = item.start, item.end
                course.modified_by, course.modify_date = self.actor["user_id"], datetime.now()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return {"message": "Course enrollment limits saved."}
