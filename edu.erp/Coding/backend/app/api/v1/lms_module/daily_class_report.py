"""Daily class timetable report for the migrated IEMS/Cudos schema."""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess

router = APIRouter(tags=["Daily Class Timetable Report"])


def section_table(db):
    schema = inspect(db.get_bind())
    for name in ("cudos_mastere_type_details", "cudos_master_type_details"):
        if schema.has_table(name):
            return name
    raise HTTPException(409, "Section master table is unavailable")


def day_sql(column):
    # All callers supply fixed SQL identifiers, never request values.
    # MySQL can partially parse DD-MM-YYYY using %Y-%m-%d without returning
    # NULL (e.g. a year below 100). Choose the format before parsing.
    return f"""CASE
        WHEN {column} REGEXP '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN STR_TO_DATE(LEFT({column},10),'%Y-%m-%d')
        WHEN {column} REGEXP '^[0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}}' THEN STR_TO_DATE(LEFT({column},10),'%d-%m-%Y')
        WHEN {column} REGEXP '^[0-9]{{2}}/[0-9]{{2}}/[0-9]{{4}}' THEN STR_TO_DATE(LEFT({column},10),'%d/%m/%Y')
        ELSE NULL END"""


def user_scope(user):
    if not user.get("org_id") or not user.get("user_id"):
        raise HTTPException(403, "Organization and user context are required")
    return {"org_id": user["org_id"], "user_id": user["user_id"]}


def mapping_scope(user):
    if user.get("super_admin") or user.get("technical_admin"):
        return ""
    # Course owners can inspect their courses, instructors their mapped sections.
    return """ AND (EXISTS (
        SELECT 1 FROM cudos_users_groups ug JOIN cudos_groups g ON g.id=ug.group_id
        WHERE ug.user_id=:user_id AND LOWER(g.name) IN ('admin','director'))
      OR (EXISTS (
        SELECT 1 FROM cudos_users_groups ug JOIN cudos_groups g ON g.id=ug.group_id
        WHERE ug.user_id=:user_id AND LOWER(g.name) IN ('chairman','program owner'))
        AND (EXISTS (SELECT 1 FROM cudos_map_user_dept ud WHERE ud.user_id=:user_id
                     AND (ud.base_dept_id=d.dept_id OR ud.assigned_dept_id=d.dept_id))
             OR EXISTS (SELECT 1 FROM iems_users u WHERE u.id=:user_id
                        AND u.org_id=:org_id AND u.user_dept_id=d.dept_id)))
      OR m.course_instructor_id = :user_id OR EXISTS (
        SELECT 1 FROM cudos_course_clo_owner own
        WHERE own.academic_batch_id=m.academic_batch_id
          AND own.semester_id=m.semester_id AND own.crs_id=m.crs_id
          AND own.clo_owner_id=:user_id))"""


def hierarchy_sql(user):
    return """
        FROM iems_department d
        JOIN iems_program p ON p.dept_id=d.dept_id AND p.org_id=d.org_id
        JOIN iems_academic_batch b ON b.pgm_id=p.pgm_id AND b.org_id=p.org_id
        JOIN iems_semester s ON s.academic_batch_id=b.academic_batch_id AND s.org_id=b.org_id
        JOIN cudos_map_courseto_course_instructor m
          ON m.academic_batch_id=b.academic_batch_id AND m.semester_id=s.semester_id
        JOIN iems_courses c ON c.crs_id=m.crs_id
          AND c.academic_batch_id=b.academic_batch_id AND c.org_id=b.org_id
        WHERE d.org_id=:org_id AND d.status=1 AND p.status=1 AND b.status=1
    """ + mapping_scope(user)


def fetch(db, sql, params):
    return [dict(r) for r in db.execute(text(sql), params).mappings()]


def parse_ids(value):
    parts = str(value or '').split(',')
    if any(not p.strip().isascii() or not p.strip().isdigit() or int(p.strip()) <= 0 for p in parts):
        raise HTTPException(422, 'Filters must contain positive IDs separated by commas')
    return list(dict.fromkeys(int(p.strip()) for p in parts))


def selected_sql(values, columns, params):
    clauses = []
    for key, column in columns.items():
        ids = values[key] if isinstance(values[key], list) else parse_ids(values[key])
        placeholders = []
        for i, value in enumerate(ids):
            name = f'{key}_{i}'
            params[name] = value
            placeholders.append(':' + name)
        clauses.append(f" AND {column} IN ({','.join(placeholders)})")
    return ''.join(clauses)


@router.get("/options/{level}")
def options(level: str, dept_id: str = Query(None), program_id: str = Query(None),
            academic_batch_id: str = Query(None), semester_id: str = Query(None),
            db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    levels = {
        "departments": ("d.dept_id", "d.dept_name", []),
        "programs": ("p.pgm_id", "p.pgm_title", ["dept_id"]),
        "curriculums": ("b.academic_batch_id", "COALESCE(NULLIF(b.academic_batch_desc,''),b.academic_batch_code)", ["dept_id", "program_id"]),
        "terms": ("s.semester_id", "CONCAT(s.semester,' - Semester')", ["dept_id", "program_id", "academic_batch_id"]),
        "sections": ("m.section_id", f"(SELECT sec.mt_details_name FROM {section_table(db)} sec WHERE sec.mt_details_id=m.section_id)", ["dept_id", "program_id", "academic_batch_id", "semester_id"]),
    }
    if level not in levels:
        raise HTTPException(404, "Unknown dropdown")
    values = dict(dept_id=dept_id, program_id=program_id, academic_batch_id=academic_batch_id, semester_id=semester_id)
    key, label, required = levels[level]
    if any(values[k] is None for k in required):
        raise HTTPException(422, "Select the preceding dropdowns first")
    columns = dict(dept_id="d.dept_id", program_id="p.pgm_id", academic_batch_id="b.academic_batch_id", semester_id="s.semester_id")
    # Master filters remain selectable before downstream timetable mappings exist.
    catalog = " FROM iems_department d"
    conditions = " WHERE d.org_id=:org_id AND d.status=1"
    if level in ('programs', 'curriculums', 'terms'):
        catalog += " JOIN iems_program p ON p.dept_id=d.dept_id AND p.org_id=d.org_id"
        conditions += " AND p.status=1"
    if level in ('curriculums', 'terms'):
        catalog += " JOIN iems_academic_batch b ON b.pgm_id=p.pgm_id AND b.org_id=p.org_id"
        conditions += " AND b.status=1"
    if level == 'terms':
        catalog += " JOIN iems_semester s ON s.academic_batch_id=b.academic_batch_id AND s.org_id=b.org_id"
    source = hierarchy_sql(user) if level == 'sections' else catalog + conditions
    sql = f"SELECT DISTINCT {key} AS id, {label} AS name " + source
    params = user_scope(user)
    sql += selected_sql(values, {name: columns[name] for name in required}, params)
    order = " ORDER BY CAST(s.semester AS UNSIGNED), s.semester_id" if level == 'terms' else " ORDER BY name, id"
    rows = fetch(db, sql + order, params)
    return returnSuccess([r for r in rows if r["id"] is not None and r["name"] is not None])


def filters(dept_id: str = Query(...), program_id: str = Query(...),
            academic_batch_id: str = Query(...), semester_id: str = Query(...),
            section_id: str = Query(...)):
    return {key: parse_ids(value) for key, value in dict(dept_id=dept_id, program_id=program_id,
        academic_batch_id=academic_batch_id, semester_id=semester_id, section_id=section_id).items()}


def selected_scope(user, values, params):
    sql = """SELECT DISTINCT b.academic_batch_id,s.semester_id,c.crs_id,m.section_id,
             d.dept_name,p.pgm_id,d.dept_id """ + hierarchy_sql(user)
    return sql + selected_sql(values, dict(dept_id='d.dept_id', program_id='p.pgm_id',
        academic_batch_id='b.academic_batch_id', semester_id='s.semester_id', section_id='m.section_id'), params)


def class_cte(db, user, values, start_date, end_date):
    if start_date > end_date:
        raise HTTPException(422, "Start date cannot be later than end date")
    params = {**user_scope(user), 'start_date': start_date, 'end_date': end_date}
    scope = selected_scope(user, values, params)
    course = "CASE WHEN dm.extra_class_flag>0 AND dm.allot_crs_id IS NOT NULL THEN dm.allot_crs_id ELSE t.crs_id END"
    day = day_sql('dm.class_date')
    cte = f"""WITH scope AS ({scope}), classes AS (
        SELECT DISTINCT dm.tt_day_map_id, t.time_table_id, td.tt_detail_id,
          scope.academic_batch_id,scope.semester_id,scope.crs_id,scope.section_id,
          scope.dept_name AS department,{day} AS date,
          t.class_start_time,t.class_end_time
        FROM lms_tt_time_table_day_mapping dm
        JOIN lms_tt_time_table t ON t.time_table_id=dm.time_table_id
        JOIN lms_tt_time_table_details td ON td.tt_detail_id=dm.tt_detail_id
        JOIN scope ON scope.academic_batch_id=td.academic_batch_id
          AND scope.semester_id=td.semester_id AND scope.crs_id={course}
          AND (scope.section_id=td.section_id OR EXISTS (
              SELECT 1 FROM lms_tt_time_table_batch_map bm
              WHERE bm.time_table_id=t.time_table_id AND bm.batch_id=scope.section_id))
        WHERE {day} BETWEEN :start_date AND :end_date
    )"""
    return cte, params


def context_key(row):
    return tuple(row[k] for k in ('academic_batch_id','semester_id','crs_id','section_id','date'))


def actor_name(alias, id_column):
    # Fixed identifiers from this module only. Never substitute request values.
    return f"""COALESCE(NULLIF(TRIM(CONCAT_WS(' ',{alias}.first_name,{alias}.middle_name,{alias}.last_name)),''),
        NULLIF(TRIM({alias}.username),''),NULLIF(TRIM({alias}.email),''),
        CASE WHEN {id_column}>0 THEN CONCAT('User #',{id_column}) ELSE NULL END)"""


def attach_attendance(rows, lessons, attendance):
    """Index once; never reuse a date-level header for two class slots."""
    from collections import defaultdict
    by_lesson, by_context = defaultdict(list), defaultdict(list)
    counts, detail_counts = defaultdict(int), defaultdict(int)
    for a in attendance:
        if a.get('lls_id'):
            by_lesson[a['lls_id']].append(a)
        else:
            by_context[context_key(a)].append(a)
    for row in rows:
        counts[context_key(row)] += 1
        detail_counts[(context_key(row),row['tt_detail_id'])] += 1
    for row in rows:
        lesson_ids = lessons.get(row['id'], set())
        exact = [a for lesson in lesson_ids for a in by_lesson[lesson]]
        legacy = [a for a in by_context[context_key(row)]
                  if not a.get('tt_detail_id') or a['tt_detail_id']==row['tt_detail_id']]
        # With a detail identifier, only classes sharing that detail compete.
        eligible = []
        for a in legacy:
            count = detail_counts[(context_key(row),a['tt_detail_id'])] if a.get('tt_detail_id') else counts[context_key(row)]
            if count == 1:
                eligible.append(a)
        ambiguous = bool(legacy and not eligible and not exact)
        matches = exact or eligible
        # Multiple lesson IDs may describe topics of one class. Multiple headers
        # cannot be combined into an invented per-class attendance total.
        a = matches[0] if len(matches)==1 else None
        row.update(time='',email='',faculty='',students_present=None,total_students=None,attendance_scope=None)
        if not lesson_ids:
            row['status'] = 'Class Not Scheduled'
        elif ambiguous or len(matches)>1:
            row['status'] = 'Attendance Match Ambiguous'
        elif not a or str(a['status'])=='0':
            row['status'] = 'Attendance Not Taken'
        else:
            # Current FastAPI attendance writer: 1=draft, 2=finalized.
            row['status'] = 'Finalized' if str(a['status'])=='2' else 'In Progress'
            row.update(email=a['email'], faculty=a['faculty'], students_present=a['students_present'], total_students=a['total_students'],
                time=' / '.join(dict.fromkeys(str(v) for v in (a['created_at'],a['modified_at']) if v)),
                attendance_scope='lesson' if a.get('lls_id') else 'unique-class')
        for key in ('academic_batch_id','semester_id','crs_id','section_id','tt_detail_id','tt_day_map_id','time_table_id','class_start_time','class_end_time'):
            row.pop(key, None)
    return rows


@router.get("/scheduled-dates")
def scheduled_dates(start_date: date, end_date: date, values: dict = Depends(filters),
                    db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    cte, params = class_cte(db,user,values,start_date,end_date)
    return returnSuccess([str(r['date']) for r in fetch(db,cte+f"""
        SELECT DISTINCT cl.date FROM classes cl JOIN lms_lesson_schedule ls
          ON ls.academic_batch_id=cl.academic_batch_id AND ls.semester_id=cl.semester_id
          AND ls.crs_id=cl.crs_id AND ls.section_id=cl.section_id
          AND (ls.tt_day_map_id=cl.tt_day_map_id OR
              ((ls.tt_day_map_id IS NULL OR ls.tt_day_map_id=0)
               AND ls.time_table_id=cl.time_table_id AND {day_sql('ls.plan_date')}=cl.date))
        ORDER BY cl.date
    """,params)])


@router.get("/report")
def report(start_date: date, end_date: date, values: dict = Depends(filters),
           db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    cte, params = class_cte(db,user,values,start_date,end_date)
    sec = section_table(db)
    rows = fetch(db,cte+f"""
        SELECT cl.*,CONCAT(cl.tt_day_map_id,':',cl.section_id) AS id,sec.mt_details_name AS section,
          CONCAT(cl.class_start_time,' - ',cl.class_end_time) AS class_timings,
          CONCAT_WS(' - ',c.crs_code,c.crs_title) AS scheduled_class
        FROM classes cl JOIN iems_courses c ON c.crs_id=cl.crs_id
        JOIN {sec} sec ON sec.mt_details_id=cl.section_id
        ORDER BY cl.date DESC,cl.class_start_time,cl.tt_day_map_id,cl.section_id
    """,params)
    if not rows:
        scope_params = user_scope(user)
        scope = selected_scope(user,values,scope_params)
        if not fetch(db,'SELECT 1 FROM ('+scope+') permitted LIMIT 1',scope_params):
            raise HTTPException(404, "The selected hierarchy or section is unavailable")
        return returnSuccess([])
    lesson_rows = fetch(db,cte+f"""
        SELECT DISTINCT CONCAT(cl.tt_day_map_id,':',cl.section_id) AS id,ls.lls_id
        FROM classes cl JOIN lms_lesson_schedule ls
          ON ls.academic_batch_id=cl.academic_batch_id AND ls.semester_id=cl.semester_id
          AND ls.crs_id=cl.crs_id AND ls.section_id=cl.section_id
          AND (ls.tt_day_map_id=cl.tt_day_map_id OR
              ((ls.tt_day_map_id IS NULL OR ls.tt_day_map_id=0)
               AND ls.time_table_id=cl.time_table_id AND {day_sql('ls.plan_date')}=cl.date))
    """,params)
    from collections import defaultdict
    lessons = defaultdict(set)
    for lesson in lesson_rows:
        lessons[lesson['id']].add(lesson['lls_id'])
    attendance = fetch(db,cte+f""", headers AS (
        SELECT a.*,{day_sql('a.attendance_date')} AS date
        FROM lms_manage_attendance a WHERE EXISTS (
          SELECT 1 FROM classes cl WHERE cl.academic_batch_id=a.academic_batch_id
            AND cl.semester_id=a.semester_id AND cl.crs_id=a.crs_id AND cl.section_id=a.section_id
            AND cl.date={day_sql('a.attendance_date')})
    ), totals AS (
        SELECT msa.attendance_id,
          COUNT(DISTINCT CASE WHEN LOWER(TRIM(CAST(msa.attendance_status AS CHAR))) IN ('present','p','1') THEN msa.ssd_id END) AS students_present,
          COUNT(DISTINCT msa.ssd_id) AS total_students
        FROM lms_map_student_attendance msa JOIN headers h ON h.attendance_id=msa.attendance_id
        GROUP BY msa.attendance_id
    )
        SELECT a.*,CONCAT_WS(' / ',created.email,IF(a.created_by<>a.modified_by,modified.email,NULL)) AS email,
          CONCAT_WS(' / ',{actor_name('created','a.created_by')},
            IF(COALESCE(a.created_by,0)<>COALESCE(a.modified_by,0),{actor_name('modified','a.modified_by')},NULL)) AS faculty,
          COALESCE(totals.students_present,0) AS students_present,
          COALESCE(totals.total_students,0) AS total_students
        FROM headers a
        LEFT JOIN totals ON totals.attendance_id=a.attendance_id
        LEFT JOIN iems_users created ON created.id=a.created_by AND created.org_id=:org_id
        LEFT JOIN iems_users modified ON modified.id=a.modified_by AND modified.org_id=:org_id
    """,params)
    faculty_rows = fetch(db,cte+"""
        SELECT DISTINCT CONCAT(cl.tt_day_map_id,':',cl.section_id) AS id,
          CONCAT_WS(' ',u.first_name,u.middle_name,u.last_name) AS name
        FROM classes cl JOIN cudos_map_courseto_course_instructor ci
          ON ci.academic_batch_id=cl.academic_batch_id AND ci.semester_id=cl.semester_id
          AND ci.crs_id=cl.crs_id AND ci.section_id=cl.section_id
        JOIN iems_users u ON u.id=ci.course_instructor_id AND u.org_id=:org_id
    """,params)
    names = defaultdict(set)
    for faculty in faculty_rows:
        names[faculty['id']].add(faculty['name'])
    if lesson_rows:
        # Only topic instructors for the selected lessons; one bulk query.
        lesson_params = dict(params)
        ids = sorted({r['lls_id'] for r in lesson_rows})
        tokens = []
        for i,value in enumerate(ids):
            lesson_params[f'lesson_{i}']=value
            tokens.append(f':lesson_{i}')
        topics = fetch(db,"""
            SELECT DISTINCT ls.lls_id,CONCAT_WS(' ',u.first_name,u.middle_name,u.last_name) AS name
            FROM lms_lesson_schedule ls JOIN lms_ls_topic_map tm ON tm.lls_id=ls.lls_id
            JOIN lms_map_instructor_topic mit ON mit.topic_id=tm.topic_id
              AND mit.academic_batch_id=ls.academic_batch_id AND mit.semester_id=ls.semester_id
              AND mit.crs_id=ls.crs_id AND mit.section_id=ls.section_id AND mit.status=1
            JOIN iems_users u ON u.id=mit.instructor_id AND u.org_id=:org_id
            WHERE ls.lls_id IN (""" + ','.join(tokens)+")",lesson_params)
        topic_names = defaultdict(set)
        for topic in topics:
            topic_names[topic['lls_id']].add(topic['name'])
        for row in rows:
            assigned = set().union(*(topic_names[i] for i in lessons[row['id']]))
            if assigned:
                names[row['id']]=assigned
    for row in rows:
        row['scheduled_faculty']=', '.join(sorted(names[row['id']]))
    return returnSuccess(attach_attendance(rows,lessons,attendance))
