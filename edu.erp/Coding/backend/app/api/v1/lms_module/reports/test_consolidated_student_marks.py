"""Run with unittest; fixtures deliberately have no legacy curriculum tables."""
import importlib.util
from io import BytesIO
from pathlib import Path
import unittest

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


service = load("consolidated_student_marks_service")
schema = load("consolidated_student_marks_schema")


class ConsolidatedMarksTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        self.db = Session(self.engine)
        statements = [
            "CREATE TABLE iems_organisation (org_id INTEGER, marks_fetch_from INTEGER)",
            "INSERT INTO iems_organisation VALUES (1, 0), (2, 1), (3, NULL)",
            "CREATE TABLE iems_department (dept_id INTEGER, dept_name TEXT, org_id INTEGER)",
            "CREATE TABLE iems_academic_batch (academic_batch_id INTEGER, academic_batch_desc TEXT, academic_batch_code TEXT, dept_id INTEGER, pgm_id INTEGER, org_id INTEGER)",
            "CREATE TABLE iems_semester (semester_id INTEGER, semester INTEGER, semester_desc TEXT, academic_batch_id INTEGER)",
            "CREATE TABLE iems_courses (crs_id INTEGER, crs_code TEXT, crs_title TEXT, academic_batch_id INTEGER, semester INTEGER, edu_sys_flag INTEGER)",
            "CREATE TABLE cudos_master_type_details (mt_details_id INTEGER, mt_details_name TEXT, parent_id INTEGER)",
            "CREATE TABLE cudos_map_courseto_course_instructor (academic_batch_id INTEGER, semester_id INTEGER, section_id INTEGER, crs_id INTEGER)",
            "CREATE TABLE cudos_qp_definition (qpd_id INTEGER, crs_id INTEGER, academic_batch_id INTEGER, semester_id INTEGER, qpd_title TEXT, qpd_max_marks REAL, qp_rollout INTEGER, qpd_type INTEGER)",
            "CREATE TABLE iems_assessment_occasions (ao_id INTEGER, qpd_id INTEGER, crs_id INTEGER, academic_batch_id INTEGER, semester_id INTEGER, ao_name TEXT, max_marks REAL, section_id INTEGER, mte_flag INTEGER)",
            "CREATE TABLE iems_students (student_id INTEGER, usno TEXT, regno TEXT, name TEXT, first_name TEXT, middle_name TEXT, last_name TEXT, academic_batch_id INTEGER, section TEXT)",
            "CREATE TABLE cudos_map_courseto_student (student_id INTEGER, crs_id INTEGER, academic_batch_id INTEGER, semester_id INTEGER, section_id INTEGER, batch_id INTEGER)",
            "CREATE TABLE cudos_student_assessment_totalmarks (sat_id INTEGER, student_usn TEXT, crs_id INTEGER, qpd_id INTEGER, total_marks REAL, section_id INTEGER)",
            "INSERT INTO iems_department VALUES (1, 'Computing', 1)",
            "INSERT INTO iems_academic_batch VALUES (10, 'Batch 2026', '2026', 1, 1, 1)",
            "INSERT INTO iems_semester VALUES (81, 3, 'Term 3', 10), (82, 3, 'Other batch', 20)",
            "INSERT INTO iems_courses VALUES (100, 'CS1', 'Algorithms', 10, 3, 0), (101, 'CS2', 'Networks', 10, 3, 0), (102, 'LAB', 'Lab', 10, 3, 1)",
            "INSERT INTO cudos_master_type_details VALUES (143, 'A', 0), (144, 'B', 0), (145, 'A1', 143)",
            "INSERT INTO cudos_map_courseto_course_instructor VALUES (10,81,143,100), (10,81,143,100), (10,81,144,101), (10,81,145,102)",
            "INSERT INTO cudos_qp_definition VALUES (1,100,10,81,'Test',20,2,1), (2,100,10,81,'Test',30,2,1), (3,100,10,81,'Draft',10,1,1), (4,100,10,81,'Final',50,2,5)",
            "INSERT INTO iems_assessment_occasions VALUES (1,1,100,10,81,'Test',20,143,0), (2,2,100,10,81,'Test',30,143,0), (3,3,100,10,81,'Draft',10,143,0)",
            "INSERT INTO iems_students VALUES (1,'U1','12345','Alice',NULL,NULL,NULL,10,'A'), (2,'U2','23456','Bob',NULL,NULL,NULL,10,'A'), (3,'U3','34567','Charlie',NULL,NULL,NULL,10,'B'), (4,'U4','45678','Dana',NULL,NULL,NULL,10,'A')",
            "INSERT INTO cudos_map_courseto_student VALUES (1,102,10,81,143,145)",
            "INSERT INTO cudos_student_assessment_totalmarks VALUES (1,'U1',100,1,5,143), (2,'U1',100,1,10,143), (3,'U2',100,1,0,143), (4,'U1',100,2,20,143), (5,'U2',100,2,NULL,143), (6,'U3',100,1,99,144), (7,'U1',100,3,10,143), (8,'U1',100,4,40,NULL)",
        ]
        for statement in statements:
            self.db.execute(text(statement))

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def request(self, **updates):
        return schema.ConsolidatedStudentMarksRequest(**{
            "department_id": 1, "academic_batch_id": 10, "semester_id": 81,
            "section_id": 143, "course_ids": [100], **updates})

    def test_migrated_dropdowns_and_section_course_mapping(self):
        self.assertEqual(service.get_curriculum_options(self.db, 1, 1)[0]["crclm_id"], 10)
        self.assertEqual(service.get_term_options(self.db, 10)[0]["semester_id"], 81)
        self.assertEqual(len(service.get_section_options(self.db, 10, 81)), 3)
        self.assertEqual([c["course_id"] for c in service.get_course_options(self.db, 10, 81, section_id=143)], [100])

    def test_invalid_term_section_and_course_are_rejected(self):
        for changes in ({"semester_id": 3}, {"semester_id": 82}, {"section_id": 999}, {"course_ids": [101]}, {"course_ids": []}, {"crclm_term_id": 82}):
            with self.subTest(changes=changes), self.assertRaises(HTTPException):
                service.build_consolidated_student_marks_report(self.db, self.request(**changes))

    def test_report_released_assessments_zero_absence_duplicates_and_identity(self):
        report = service.build_consolidated_student_marks_report(self.db, self.request())
        schema.ReportData.model_validate(report)
        self.assertEqual([r["student_usn"] for r in report["rows"]], ["U1", "U2", "U4"])
        self.assertEqual(report["rows"][0]["regno"], "12345")
        first = report["rows"][0]["courses"][0]
        self.assertEqual([c["component_id"] for c in first["components"]], ["1", "2", "4"])
        self.assertEqual(first["total_marks"], 70)
        second = report["rows"][1]["courses"][0]
        self.assertEqual(second["components"][0]["marks"], 0)
        self.assertEqual(second["components"][1]["status"], "absent")
        self.assertIsNone(report["rows"][2]["courses"][0]["total_marks"])

    def test_mark_range_is_inclusive_and_absence_is_explicit(self):
        report = service.build_consolidated_student_marks_report(self.db, self.request(start_range=10, end_range=20))
        self.assertEqual(len(report["rows"]), 1)
        self.assertEqual(report["rows"][0]["courses"][0]["total_marks"], 30)
        report = service.build_consolidated_student_marks_report(self.db, self.request(start_range=10, end_range=20, include_absents=True))
        self.assertEqual([r["student_usn"] for r in report["rows"]], ["U1", "U2"])
        self.assertEqual(report["rows"][1]["courses"][0]["components"][0]["status"], "filtered")

    def test_graph_averages_include_zero_exclude_missing_and_absent(self):
        graph = service.build_consolidated_student_marks_graph(self.db, self.request(include_total_marks=False))
        schema.GraphData.model_validate(graph)
        assessments = graph["courses"][0]["assessments"]
        self.assertEqual([a["average_marks"] for a in assessments], [5, 20, 40])
        self.assertEqual(assessments[1]["absent_count"], 1)
        self.assertEqual(graph["courses"][0]["student_count"], 2)

    def test_child_batch_roster(self):
        report = service.build_consolidated_student_marks_report(self.db, self.request(section_id=145, course_ids=[102]))
        self.assertEqual([r["student_usn"] for r in report["rows"]], ["U1"])

    def test_organisation_controls_marks_source(self):
        self.assertEqual(service.get_organisation_marks_source(self.db, 1), "lms")
        self.assertEqual(service.get_organisation_marks_source(self.db, 2), "ems")
        for org_id in (3, 999):
            with self.assertRaises(HTTPException):
                service.get_organisation_marks_source(self.db, org_id)
        report = service.build_consolidated_student_marks_report(self.db, self.request(marks_source="ems"))
        self.assertEqual(report["filters"]["marks_source"], "lms")

    def test_range_validation(self):
        for changes in ({"start_range": 0}, {"start_range": 20, "end_range": 10}, {"start_range": -1, "end_range": 10}, {"start_range": 0, "end_range": 101}, {"from_date": "2026-01-01"}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                self.request(**changes)

    def test_ems_totals_do_not_double_count_cia_and_absence_overrides_marks(self):
        for column in ("cia_max_marks", "ise_max_marks", "mse_max_marks", "see_max_marks", "viva_max_marks", "tw_max_marks"):
            self.db.execute(text(f"ALTER TABLE iems_courses ADD COLUMN {column} REAL"))
        self.db.execute(text("""CREATE TABLE iems_student_courses (
            std_crs_id INTEGER, regno TEXT, usno TEXT, crs_code TEXT, batch_id INTEGER,
            semester INTEGER, result_year TEXT, is_withdrawn INTEGER, is_drop INTEGER,
            total_cia REAL, total_ise REAL, total_mse REAL, see_actual REAL, see REAL,
            tw_marks_actual REAL, tw_marks REAL, viva_marks REAL, see_absentee INTEGER,
            tw_absentee INTEGER, viva_absentee INTEGER, cia_see REAL)"""))
        self.db.execute(text("""CREATE TABLE iems_cia_student_courses (
            id INTEGER, std_crs_id INTEGER, occasion_id INTEGER, cia_master_id INTEGER,
            secured_marks REAL, is_absentee INTEGER, result_year TEXT)"""))
        self.db.execute(text("CREATE TABLE iems_cia_occasion_type (cia_occasion_type_id INTEGER, cia_occasion_type_desc TEXT, cia_occasion_type_code TEXT)"))
        self.db.execute(text("CREATE TABLE iems_cia_exam_master (id INTEGER, cia_master_name TEXT, cia_max_marks REAL)"))
        self.db.execute(text("""INSERT INTO iems_student_courses VALUES
            (1,'12345','U1','CS1',10,3,'2026-01-01',0,0,30,20,10,40,40,NULL,NULL,NULL,0,0,0,70),
            (2,'23456','U2','CS1',10,3,'2026-01-01',0,0,NULL,NULL,NULL,40,40,NULL,NULL,NULL,1,0,0,40)"""))
        self.db.execute(text("INSERT INTO iems_cia_exam_master VALUES (1,'CIA',50)"))
        self.db.execute(text("INSERT INTO iems_cia_occasion_type VALUES (1,'Test','T')"))
        self.db.execute(text("INSERT INTO iems_cia_student_courses VALUES (1,1,1,1,45,0,'2026-01-01'), (2,2,1,1,0,1,'2026-01-01')"))
        report = service.build_consolidated_student_marks_report(self.db, self.request(), org_id=2)
        first, second = report["rows"][:2]
        self.assertEqual(first["courses"][0]["total_marks"], 70)
        self.assertEqual(first["courses"][0]["components"][0]["marks"], 45)
        self.assertIsNone(second["courses"][0]["total_marks"])
        self.assertTrue(all(c["status"] == "absent" for c in second["courses"][0]["components"]))

    def test_real_exports_and_formula_safety(self):
        from openpyxl import load_workbook
        self.db.execute(text("UPDATE iems_students SET name = '=HYPERLINK(1)' WHERE student_id = 1"))
        for format in ("excel", "csv", "pdf"):
            with self.subTest(format=format):
                payload = schema.ExportRequest(**self.request().model_dump(), format=format)
                content, media_type, extension = service.export_consolidated_student_marks_report(self.db, payload)
                self.assertGreater(len(content), 100)
                if format == "excel":
                    workbook = load_workbook(BytesIO(content))
                    self.assertEqual(workbook.active['C2'].data_type, 's')
                    self.assertEqual(workbook.active['D2'].value, 10)
                elif format == "csv":
                    self.assertIn("'=HYPERLINK(1)", content.decode("utf-8-sig"))
                else:
                    self.assertTrue(content.startswith(b'%PDF'))


if __name__ == "__main__":
    unittest.main()
