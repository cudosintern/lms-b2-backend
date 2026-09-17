import unittest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError
from .schemas import ConfigurationSave, CourseSave
from .validation import validate_configuration, validate_courses, validate_window


class RegistrationRulesTest(unittest.TestCase):
    def summary(self, mode="credits"):
        return {"mode": mode, "max_registered": 6, "types": [
            {"course_type_id": 1, "name": "Core", "total": 9, "minimum_allowed": 1.5 if mode == "credits" else 0, "max_registered": 6},
            {"course_type_id": 2, "name": "Elective", "total": 6, "minimum_allowed": 1.5 if mode == "credits" else 0, "max_registered": 3}]}

    def payload(self, **changes):
        values = dict(start="2026-09-10T09:00", end="2026-09-11T10:00", total=12,
            limits=[dict(course_type_id=1, minimum=3, maximum=9), dict(course_type_id=2, minimum=1.5, maximum=6)])
        values.update(changes)
        return ConfigurationSave(**values)

    def test_fractional_credit_limits(self):
        validate_configuration(self.payload(), self.summary())

    def test_credit_maximum_uses_student_credits(self):
        with self.assertRaisesRegex(ValueError, "existing registrations"):
            validate_configuration(self.payload(total=5), self.summary())

    def test_type_maximum_protects_existing_students(self):
        data = self.payload(); data.limits[0].maximum = Decimal(5)
        with self.assertRaisesRegex(ValueError, "existing registrations"):
            validate_configuration(data, self.summary())

    def test_sum_minimums(self):
        data = self.payload(total=6); data.limits[0].minimum = Decimal(6)
        with self.assertRaisesRegex(ValueError, "sum of minimum"):
            validate_configuration(data, self.summary())

    def test_count_mode_rejects_fractions(self):
        with self.assertRaisesRegex(ValueError, "whole numbers"):
            validate_configuration(self.payload(), self.summary("courses"))

    def test_count_mode_allows_zero_minimum(self):
        data = self.payload()
        for row in data.limits: row.minimum = Decimal(0)
        validate_configuration(data, self.summary("courses"))

    def test_missing_duplicate_or_foreign_types(self):
        for ids in ([1], [1, 1], [1, 3]):
            with self.subTest(ids=ids), self.assertRaisesRegex(ValueError, "exactly once"):
                data = self.payload(limits=[dict(course_type_id=i, minimum=1.5, maximum=9) for i in ids])
                validate_configuration(data, self.summary())

    def test_minimum_credit_floor(self):
        data = self.payload(); data.limits[0].minimum = Decimal(0)
        with self.assertRaisesRegex(ValueError, "minimum and maximum"):
            validate_configuration(data, self.summary())

    def test_term_window_duration(self):
        for end in ("2026-09-10T08:00", "2026-09-10T09:00", "2026-09-10T09:29"):
            with self.subTest(end=end), self.assertRaisesRegex(ValueError, "30 minutes"):
                validate_configuration(self.payload(end=end), self.summary())
        validate_configuration(self.payload(end="2026-09-10T09:30"), self.summary())

    def test_timezone_offsets_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            validate_window(datetime.fromisoformat("2026-09-10T09:00+05:30"), datetime.fromisoformat("2026-09-10T10:00+05:30"))

    def test_payload_bounds(self):
        for changes in (dict(total=0), dict(total=61), dict(total="NaN"), dict(own_electives=10), dict(other_electives=1.2), dict(other_electives=True), dict(limits=[])):
            with self.subTest(changes=changes), self.assertRaises(ValidationError): self.payload(**changes)

    def course_rows(self):
        return [dict(course_id=1, code="OE1", alias="OPEN_ELECTIVE", registered=3)]

    def course_payload(self, **changes):
        values = dict(course_id=1, capacity=3, start="2026-09-10T09:00", end="2026-09-10T10:00")
        values.update(changes)
        return CourseSave(courses=[values])

    def validate_course(self, data, rows=None):
        validate_courses(data, rows or self.course_rows(), datetime(2026, 9, 10, 9), datetime(2026, 9, 11, 10))

    def test_unlimited_and_existing_capacity(self):
        self.validate_course(self.course_payload(capacity=None))
        self.validate_course(self.course_payload(capacity=3))
        with self.assertRaisesRegex(ValueError, "capacity"):
            self.validate_course(self.course_payload(capacity=2))

    def test_zero_capacity_is_not_unlimited(self):
        rows = self.course_rows(); rows[0]["registered"] = 0
        self.validate_course(self.course_payload(capacity=0), rows)

    def test_open_elective_window(self):
        for changes in (dict(start=None), dict(end=None), dict(start="2026-09-10T08:59"), dict(end="2026-09-11T10:01"), dict(end="2026-09-10T09:29")):
            with self.subTest(changes=changes), self.assertRaises(ValueError): self.validate_course(self.course_payload(**changes))

    def test_foreign_course_and_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly once"):
            self.validate_course(self.course_payload(course_id=2))
        data = self.course_payload(); data.courses.append(data.courses[0])
        with self.assertRaisesRegex(ValueError, "exactly once"): self.validate_course(data)

    def test_only_open_electives_accept_windows(self):
        rows = self.course_rows(); rows[0]["alias"] = "ELECTIVE"
        with self.assertRaisesRegex(ValueError, "only to open"):
            self.validate_course(self.course_payload(), rows)
        self.validate_course(self.course_payload(start=None, end=None), rows)

    def test_core_courses_are_read_only(self):
        rows = self.course_rows(); rows[0]["alias"] = "CORE"
        with self.assertRaisesRegex(ValueError, "only for elective"):
            self.validate_course(self.course_payload(start=None, end=None), rows)


if __name__ == "__main__": unittest.main()
