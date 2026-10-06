"""Pure report calculations, shared by the main report and its drilldowns."""
from collections import defaultdict
from decimal import Decimal


def build_report(students, courses, enrollments, batch_id, sections=()):
    selected = {str(value) for value in sections}
    roster = {s['student_id']: dict(s) for s in students
              if not selected or str(s['section_id']) in selected}
    catalog = {c['course_id']: dict(c) for c in courses}
    registrations = {}
    for entry in enrollments:
        if selected and str(entry['section_id']) not in selected:
            continue
        key = (entry['student_id'], entry['course_id'])
        # Duplicate mappings must never inflate credits or headcounts.
        if key not in registrations:
            registrations[key] = dict(entry)
    per_student = defaultdict(list)
    for entry in registrations.values():
        per_student[entry['student_id']].append(entry)
    rows = []
    for student in roster.values():
        registered = sorted(per_student[student['student_id']], key=lambda c: (c['course_type'], c['course_code']))
        rows.append({**student, 'registered_courses': registered,
                     'total_credits': float(sum((Decimal(str(c['credits'] or 0)) for c in registered), Decimal(0)))})
    rows.sort(key=lambda s: (s['section'] or '', len(s['usn'] or ''), s['usn'] or '', s['student_id']))
    types = {c['course_type_id']: c['course_type'] for c in courses}
    for row in rows:
        for course in row['registered_courses']:
            types[course['course_type_id']] = course['course_type']
    overall, summary, columns = [], [], []
    for type_id, name in sorted(types.items(), key=lambda pair: (pair[1], pair[0])):
        registered_ids = {r['student_id'] for r in rows if any(c['course_type_id'] == type_id for c in r['registered_courses'])}
        overall.append({'course_type_id': type_id, 'course_type': name, 'total_students': len(rows),
                        'registered_students': len(registered_ids), 'unregistered_students': len(rows) - len(registered_ids)})
        own_courses = [c for c in catalog.values() if c['course_type_id'] == type_id]
        width = max([len([c for c in r['registered_courses'] if c['course_type_id'] == type_id]) for r in rows] + [1])
        columns.extend({'course_type_id': type_id, 'course_type': name, 'slot': i} for i in range(width))
        course_rows = []
        for course in sorted(own_courses, key=lambda c: c['course_code']):
            entries = [e for e in registrations.values() if e['course_id'] == course['course_id']]
            course_rows.append({**course, 'registered_students': len(entries),
                                'other_dept_students': sum(e['home_batch_id'] != batch_id for e in entries)})
        summary.append({'course_type_id': type_id, 'course_type': name, 'courses': course_rows,
                        'total_registered': sum(c['registered_students'] for c in course_rows)})
    return {'students': rows, 'overall_summary': overall, 'summary': summary, 'columns': columns,
            'registrations': list(registrations.values())}


def drilldown(report, course_type_id, registered=True, course_id=None, other=False, batch_id=None, by_course=False):
    if course_id is not None or by_course:
        return [r for r in report['registrations']
                if r['course_type_id'] == course_type_id
                and (course_id is None or r['course_id'] == course_id)
                and (not other or r['home_batch_id'] != batch_id)]
    result = []
    for student in report['students']:
        matching = [c for c in student['registered_courses'] if c['course_type_id'] == course_type_id]
        if bool(matching) == registered:
            result.append({**student, 'registered_courses': matching,
                           'total_credits': float(sum(Decimal(str(c['credits'] or 0)) for c in matching))})
    return result
