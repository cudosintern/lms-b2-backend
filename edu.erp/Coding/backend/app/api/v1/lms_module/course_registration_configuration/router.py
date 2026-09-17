from io import BytesIO
import os
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session, load_only
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.db.models import (IEMSUsers, IEMSUserOrg,
    IEMSDepartment, IEMProgram, IEMSemester)
from .schemas import ConfigurationSave, CourseSave
from .service import RegistrationService

router = APIRouter(prefix="/course-registration-configuration", tags=["Course Registration Configuration"])
bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/staff_login", auto_error=False)


def actor(token: str | None = Depends(bearer), org_id: int = Header(..., gt=0), db: Session = Depends(get_db)):
    # Match app/api/auth/login.py; the shared auth_helper currently bypasses authentication.
    secret, algorithm = os.getenv("SECRET_KEY"), os.getenv("ALGORITHM")
    if not token:
        raise HTTPException(401, "No login token was sent. Please sign in again.", headers={"WWW-Authenticate": "Bearer"})
    if not secret or not algorithm:
        raise HTTPException(503, "JWT authentication is not configured.")
    try:
        claims = jwt.decode(token, secret, algorithms=[algorithm], options={"require_exp": True})
        user_id = int(claims["id"])
    except ExpiredSignatureError as error:
        raise HTTPException(401, "Your login session has expired. Please sign in again.", headers={"WWW-Authenticate": "Bearer"}) from error
    except (JWTError, KeyError, ValueError, TypeError) as error:
        raise HTTPException(401, "The login token is invalid. Please sign in again.", headers={"WWW-Authenticate": "Bearer"}) from error
    account = db.query(IEMSUsers).options(load_only(IEMSUsers.id, IEMSUsers.status, IEMSUsers.active,
        IEMSUsers.is_locked, IEMSUsers.org_id, IEMSUsers.super_admin, IEMSUsers.user_dept_id)).filter(IEMSUsers.id == user_id, IEMSUsers.status == 1).first()
    if account is None or not account.active or account.is_locked:
        raise HTTPException(403, "An active staff account is required.")
    if account.org_id != org_id and not db.query(IEMSUserOrg.user_id).filter(
            IEMSUserOrg.user_id == account.id, IEMSUserOrg.org_id == org_id).first():
        raise HTTPException(403, "No access to this organisation.")
    # These names match the live access-control schema; the shared legacy ORM role models are stale.
    roles = {row[0].strip().lower() for row in db.execute(text("""
        SELECT rm.role_name FROM iems_user_roles ur
        JOIN iems_user_role_master rm ON rm.user_role_id = ur.user_role_id
        WHERE ur.user_id = :user_id AND ur.org_id = :org_id AND rm.status = 1
    """), {"user_id": account.id, "org_id": org_id}).all()}
    global_roles = {"admin", "administrator", "director"}
    dept_roles = {"chairman", "program owner", "department admin"}
    instructor_roles = {"course owner", "course instructor", "instructor"}
    all_departments = bool(account.super_admin) or bool(roles & global_roles)
    if not all_departments and not roles & (dept_roles | instructor_roles):
        raise HTTPException(403, "Registration configuration requires an administrator, owner, or instructor role.")
    return {"user_id": account.id, "org_id": org_id, "department_id": account.user_dept_id,
        "all_departments": all_departments, "instructor_only": not all_departments and not bool(roles & dept_roles)}


def service(db: Session = Depends(get_db), identity=Depends(actor)):
    instance = RegistrationService(db, identity)
    instance.settings()
    return instance


@router.get("/options")
def options(svc=Depends(service)):
    batches = svc.batches().order_by("academic_batch_desc").all()
    dept_ids, pgm_ids = {b.dept_id for b in batches}, {b.pgm_id for b in batches}
    departments = svc.db.query(IEMSDepartment).filter(IEMSDepartment.dept_id.in_(dept_ids), IEMSDepartment.status == 1).order_by(IEMSDepartment.dept_name).all()
    programs = svc.db.query(IEMProgram).filter(IEMProgram.pgm_id.in_(pgm_ids), IEMProgram.status == 1).order_by(IEMProgram.pgm_title).all()
    return {**svc.settings(),
        "departments": [{"id": d.dept_id, "name": d.dept_name} for d in departments],
        "programs": [{"id": p.pgm_id, "name": p.pgm_title, "department_id": p.dept_id} for p in programs],
        "curricula": [{"id": b.academic_batch_id, "name": b.academic_batch_desc, "program_id": b.pgm_id, "department_id": b.dept_id} for b in batches]}


@router.get("/curricula/{batch_id}/terms")
def terms(batch_id: int, svc=Depends(service)):
    svc.batch(batch_id)
    rows = svc.db.query(IEMSemester).filter(IEMSemester.academic_batch_id == batch_id,
        IEMSemester.org_id == svc.actor["org_id"], IEMSemester.status == 1).order_by(IEMSemester.semester).all()
    return [{"id": row.semester_id, "name": row.term_name or row.semester_desc or row.semester_code} for row in rows]


@router.get("/curricula/{batch_id}/terms/{term_id}")
def configuration(batch_id: int, term_id: int, svc=Depends(service)):
    return svc.summary(batch_id, term_id)


def save(operation):
    try:
        return operation()
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(500, "Database save failed; no changes were committed.") from error


@router.put("/curricula/{batch_id}/terms/{term_id}")
def update_configuration(batch_id: int, term_id: int, payload: ConfigurationSave, svc=Depends(service)):
    return save(lambda: svc.save_configuration(batch_id, term_id, payload))


@router.get("/curricula/{batch_id}/terms/{term_id}/types/{type_id}/courses")
def courses(batch_id: int, term_id: int, type_id: int, svc=Depends(service)):
    return svc.course_details(batch_id, term_id, type_id)


@router.put("/curricula/{batch_id}/terms/{term_id}/types/{type_id}/courses")
def update_courses(batch_id: int, term_id: int, type_id: int, payload: CourseSave, svc=Depends(service)):
    return save(lambda: svc.save_courses(batch_id, term_id, type_id, payload))


@router.get("/curricula/{batch_id}/terms/{term_id}/export.pdf")
def export_pdf(batch_id: int, term_id: int, svc=Depends(service)):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    summary = svc.summary(batch_id, term_id)
    if not summary["saved"]:
        raise HTTPException(409, "Save registration configuration before exporting.")
    stream = BytesIO()
    styles = getSampleStyleSheet()
    story = []
    def paragraph(value):
        return Paragraph(escape(str(value if value is not None else "—")), styles["BodyText"])
    def table(headers, rows, widths):
        item = Table([[paragraph(v) for v in row] for row in [headers, *rows]], colWidths=widths, repeatRows=1)
        item.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
            ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#cbd5e1")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
        story.extend([item, Spacer(1, 16)])
    story.append(Paragraph("Course Registration Configuration", styles["Title"]))
    for text in [summary["curriculum_name"], summary["term_name"],
        f'{summary["start"]} to {summary["end"]}',
        f'Total available {summary["mode"]}: {summary["total_available"]}; student limit: {summary["total"]}',
        f'Open electives: own curriculum {summary["own_electives"]}; other curricula {summary["other_electives"]}']:
        story.extend([paragraph(text), Spacer(1, 8)])
    table(["Course type", f'Total {summary["mode"]}', "Minimum", "Maximum", "Registrations"],
        [[r["name"], r["total"], r["minimum"], r["maximum"], r["registered"]] for r in summary["types"]], [240, 120, 100, 100, 180])
    for kind in summary["types"]:
        story.extend([Paragraph(escape(kind["name"]), styles["Heading2"]), Spacer(1, 6)])
        table(["Course", "Credits", "Capacity", "Registrations", "Start", "End"],
            [[f'{r["code"]} - {r["title"]}', r["credits"], "Unlimited" if r["capacity"] is None else r["capacity"],
                r["registered"], r["start"], r["end"]] for r in svc.course_details(batch_id, term_id, kind["course_type_id"])],
            [240, 60, 80, 100, 130, 130])
    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(790, 20, f"Page {doc.page}")
    SimpleDocTemplate(stream, pagesize=landscape(A4), leftMargin=40, rightMargin=40,
        topMargin=32, bottomMargin=32).build(story, onFirstPage=footer, onLaterPages=footer)
    return Response(stream.getvalue(), media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="course-registration-{batch_id}-{term_id}.pdf"'})
