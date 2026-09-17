"""Pure business rules; shared by save endpoints and tested without a database."""
from datetime import timedelta
from decimal import Decimal


def validate_window(start, end):
    if start is None or end is None:
        raise ValueError("Start and end date/time are required.")
    if start.tzinfo is not None or end.tzinfo is not None:
        raise ValueError("Use institution-local date/time without a timezone offset.")
    if end - start < timedelta(minutes=30):
        raise ValueError("The registration window must be at least 30 minutes.")


def validate_configuration(payload, summary):
    validate_window(payload.start, payload.end)
    types = {row["course_type_id"]: row for row in summary["types"]}
    ids = [row.course_type_id for row in payload.limits]
    if len(ids) != len(set(ids)) or set(ids) != set(types):
        raise ValueError("Supply each current course type exactly once; reload the configuration.")
    if payload.total < Decimal(str(summary["max_registered"])):
        raise ValueError("The total cannot be lower than a student's existing registrations.")
    minimum_sum = Decimal(0)
    for limit in payload.limits:
        row = types[limit.course_type_id]
        floor = Decimal(str(row["minimum_allowed"]))
        if not floor <= limit.minimum <= limit.maximum <= Decimal(str(row["total"])):
            raise ValueError(f'{row["name"]}: minimum and maximum must be between {floor} and {row["total"]}, with minimum <= maximum.')
        if limit.maximum < Decimal(str(row["max_registered"])):
            raise ValueError(f'{row["name"]}: maximum cannot be lower than existing registrations.')
        if summary["mode"] == "courses" and any(v != v.to_integral_value() for v in (limit.minimum, limit.maximum)):
            raise ValueError("Course counts must be whole numbers.")
        minimum_sum += limit.minimum
    if summary["mode"] == "courses" and payload.total != payload.total.to_integral_value():
        raise ValueError("Total courses must be a whole number.")
    if minimum_sum > payload.total:
        raise ValueError("The sum of minimum limits cannot exceed the total student limit.")


def validate_courses(payload, rows, start, end):
    known = {row["course_id"]: row for row in rows}
    ids = [row.course_id for row in payload.courses]
    if len(ids) != len(set(ids)) or set(ids) != set(known):
        raise ValueError("Supply each course in this course type exactly once; reload the courses.")
    for item in payload.courses:
        row = known[item.course_id]
        if row["alias"] not in ("ELECTIVE", "OPEN_ELECTIVE"):
            raise ValueError("Course capacities are configurable only for elective course types.")
        if item.capacity is not None and item.capacity < row["registered"]:
            raise ValueError(f'{row["code"]}: capacity cannot be lower than existing registrations.')
        if row["alias"] == "OPEN_ELECTIVE":
            validate_window(item.start, item.end)
            if start is None or end is None:
                raise ValueError("Save the term registration window before configuring open electives.")
            if not start <= item.start < item.end <= end:
                raise ValueError(f'{row["code"]}: course dates must be within the saved term window.')
        elif item.start is not None or item.end is not None:
            raise ValueError("Individual registration windows apply only to open electives.")
