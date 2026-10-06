"""Read-only Open Elective report migrated from lms_oe_report.

Uses the target application's shared read-only report session scope. Cross-batch
terms match by legacy term_code where present, otherwise by semester number.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from .student_registration_report import context

router = APIRouter(prefix="/student-registration-oe", tags=["Student Registration OE Report"])


def rows(svc, sql, **params):
    return [dict(row) for row in svc.db.execute(text(sql), {"org": svc.actor["org_id"], **params}).mappings()]


@router.get("/curriculums")
def curricula(svc=Depends(context)):
    return [{"id": b.academic_batch_id, "name": b.academic_batch_desc}
            for b in svc.batches().order_by("academic_batch_desc").all()]


@router.get("/terms")
def terms(academic_batch_id: int = Query(..., gt=0), svc=Depends(context)):
    svc.batch(academic_batch_id)
    return rows(svc, """SELECT semester_id AS id,
        CONCAT(semester,'- Semester') AS name
        FROM iems_semester WHERE academic_batch_id=:batch AND org_id=:org AND status=1
        ORDER BY semester,semester_id""", batch=academic_batch_id)


REPORT_SQL = """
SELECT s.usno AS student_usn,
    COALESCE(NULLIF(s.name,''),CONCAT_WS(' ',s.first_name,s.middle_name,s.last_name)) AS student_name,
    section.mt_details_name AS section_name,
    c.crs_code,c.crs_title,b.academic_batch_desc AS offering_crclm,
    d.dept_name AS offering_department,
    CONCAT_WS(' ',fac.first_name,fac.middle_name,fac.last_name) AS faculty_name
FROM cudos_map_courseto_student e
JOIN iems_students s ON s.student_id=e.student_id AND s.org_id=:org AND s.status=1
JOIN iems_courses c ON c.crs_id=e.crs_id AND c.org_id=:org AND c.status=1
JOIN iems_course_type kind ON kind.course_type_id=c.course_type_id
JOIN iems_semester offering ON offering.semester_id=e.semester_id
    AND offering.academic_batch_id=c.academic_batch_id AND offering.org_id=:org
    AND offering.semester=c.semester
JOIN iems_semester selected ON selected.semester_id=:term
    AND selected.academic_batch_id=:batch AND selected.org_id=:org
JOIN iems_academic_batch b ON b.academic_batch_id=c.academic_batch_id AND b.org_id=:org
JOIN iems_program p ON p.pgm_id=b.pgm_id AND p.org_id=:org
JOIN iems_department d ON d.dept_id=p.dept_id AND d.org_id=:org
JOIN cudos_master_type_details section ON section.mt_details_id=s.section_id
LEFT JOIN cudos_map_courseto_course_instructor mci ON mci.crs_id=c.crs_id
    AND mci.academic_batch_id=c.academic_batch_id AND mci.semester_id=offering.semester_id
    AND mci.section_id=s.section_id
LEFT JOIN iems_users fac ON fac.id=mci.course_instructor_id AND fac.org_id=:org
WHERE e.std_crclm_id=:batch
    AND ((NULLIF(selected.term_code,'') IS NOT NULL AND offering.term_code=selected.term_code)
         OR (NULLIF(selected.term_code,'') IS NULL AND offering.semester=selected.semester))
    AND kind.course_type_desc LIKE 'Open Elective%'
    AND e.status IN (SELECT status.mt_details_id FROM cudos_master_type_details status
        JOIN cudos_master_type master ON master.master_type_id=status.master_type_id
        WHERE master.master_type_name='student_registration_status'
        AND status.mt_details_name NOT IN ('Unregistered','Hospital'))
ORDER BY section.mt_details_name,s.usno,c.crs_code,e.mcstd_id,mci.mcci_id
"""


@router.get("/report")
def report(academic_batch_id: int = Query(..., gt=0), semester_id: int = Query(..., gt=0), svc=Depends(context)):
    batch = svc.batch(academic_batch_id)
    term = svc.term(academic_batch_id, semester_id)
    result = rows(svc, REPORT_SQL, batch=academic_batch_id, term=semester_id)
    org = rows(svc, "SELECT org_name FROM iems_organisation WHERE org_id=:org")
    department = rows(svc, """SELECT d.dept_name FROM iems_department d
        JOIN iems_program p ON p.dept_id=d.dept_id AND p.org_id=:org
        WHERE p.pgm_id=:program AND d.org_id=:org""", program=batch.pgm_id)
    return {"curriculum": batch.academic_batch_desc,
            "term": f"{term.semester}- Semester",
            "organisation": org[0]["org_name"] if org else "",
            "department": department[0]["dept_name"] if department else "", "rows": result}
