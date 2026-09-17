# Course registration configuration

Migrates `lms_stud_enroll_crs.zip` to the existing FastAPI application and React LMS screen. Credit mode is the explicitly selected default. The module requires no new packages or database migration on the inspected local database.

## Integration

Backend: `app/api/v1/lms_module/course_registration_configuration`.

```python
from app.api.v1.lms_module.course_registration_configuration.router import router as course_registration_configuration_router
router.include_router(course_registration_configuration_router)
```

Frontend: `src/pages/lms/course_registration_configuration`. Both existing `course-registration-setup` route entries point to the new default export. The existing Axios client supplies the API base URL, bearer token and `org-id` header.

API prefix: `/course-registration-configuration` under the existing v1 API prefix. Endpoints:

| Method | Path | Function |
| --- | --- | --- |
| GET | `/options` | Accessible departments, programs, curricula and registration mode |
| GET | `/curricula/{batch_id}/terms` | Curriculum terms |
| GET/PUT | `/curricula/{batch_id}/terms/{term_id}` | Read or save term setup and course-type limits |
| GET/PUT | `/curricula/{batch_id}/terms/{term_id}/types/{type_id}/courses` | Course details, elective capacities and open-elective dates |
| GET | `/curricula/{batch_id}/terms/{term_id}/export.pdf` | PDF summary and per-course details |

## Legacy feature mapping

| CodeIgniter functionality | Migration |
| --- | --- |
| Curriculum/term selection and remembered selection | Accessible options and sessionStorage; selecting curriculum fills department/program |
| `fetch_course_details`, `check_enroll_data_exists` | Term GET combines available courses, saved limits, dates and registered counts |
| `check_max_courses_stud_enrolled*` | Summary maximum and save-time total validation; credit maximum uses the student with the most credits |
| `check_max_courses_enrolled_by_crstype` | Per-type maximum and save-time validation |
| `save_enroll_details` | Atomic term PUT, all types required, totals recalculated on server |
| `fetch_crs_by_crstype`, enrollment limit/date/count helpers | Course GET and React dialog |
| `save_modal_details` | Atomic elective-course PUT; core-course view is read-only |
| `export_to_pdf` | Authenticated PDF endpoint, wrapping tables and repeated headers |
| `org_setting`, `get_org_settings` | Organisation overrides with enabled/credit defaults |

`view_progress_vw.php` has no callable controller action in the archive. The archived controller also calls several dropdown model methods absent from the ZIP; the new implementation uses the target application's academic tables for these lookups. There is no separate progress workflow or student-registration submission action in this module.

## Verified schema mapping

- Curriculum → `iems_academic_batch`; term → `iems_semester`.
- Courses selected by `academic_batch_id`, `semester` number and `org_id` in `iems_courses`.
- Per-type limits → `lms_academic_batch_semester_crs_structure`.
- Enrollment counts → `cudos_map_courseto_student`, excluding master statuses named `Unregistered`.
- Role lookup uses live `iems_user_roles.user_role_id` and `iems_user_role_master.role_name`. The shared role ORM classes use different, stale column names, so this lookup uses parameterized SQL.
- `iems_course_type` has no `crclm_component_id` in the inspected database. Explicit code mappings in `service.py` classify `OE`, `OE1`, `OE2` as `OPEN_ELECTIVE`; `CE`, `CE1`, `CE2`, `PE`, `PE1`, `PE2` as `ELECTIVE`. Other codes are read-only core types. Extend this mapping when adding a new elective code.

## Settings and access

The user chose **credits**. When organisation-specific rows are absent, defaults are `enable_crs_reg_by_stud=1` and `lms_stud_crs_reg=1`. Optional overrides use `iems_org_configs` with the same `config_type` names, string `value` of `0` or `1`, the relevant `org_id`, and null `program_id`/`crs_code`. Disabled registration is rejected on every endpoint. Duplicate or malformed overrides return 409.

Authentication verifies the bearer JWT issued by `app/api/auth/login.py`, using configured `SECRET_KEY`, `ALGORITHM`, the `id` claim and expiry. It deliberately does not use the existing helper's hard-coded test administrator. Active, unlocked accounts and organisation membership are required. Admin/director users see all organisation departments; chairman/program owner/department admin users are scoped to their department; course owner/instructor users also require an instructor curriculum mapping. Roles are loaded from the database, not accepted from browser headers.

## Rules and intentional fixes

- Local institution date/time, no timezone offsets. Term and open-elective windows must last at least 30 minutes. Existing course windows must still fit when a term window changes.
- Total registration limit is 1–60; credits accept one decimal place; course counts must be whole numbers. Own/other open-elective counts are 0–9.
- Credit minimum is at least the lowest course credit in the type. Course-count minimum may be zero. Minimum <= maximum <= available total; sum of minimums <= total student limit.
- Neither total nor type maximum may be reduced below existing registrations. Credit maxima aggregate credits independently of course counts, correcting the legacy maximum-count selection bug.
- Blank elective capacity means unlimited. Zero is a real capacity (consistent with the PHP model's explicit blank-versus-zero handling) and can only be saved with no registrations. Capacity cannot drop below the current registration count.
- All validation precedes changes; saves commit once and roll back on failure. Term rows and elective course rows are locked for configuration updates. Concurrent student-registration endpoints must use the same locking protocol to guarantee limits against simultaneous student submissions; those endpoints are outside this module.
- Unknown, duplicate, omitted, or out-of-scope types/courses are rejected. Core-course capacities cannot be edited through the API.
- Existing structure columns are `DECIMAL(3,1)`: type totals above 99.9 return a clear validation error rather than truncating data.

## Verification

From the backend application root:

```powershell
.\.venv\Scripts\python.exe -B -m unittest app.api.v1.lms_module.course_registration_configuration.test_validation app.api.v1.lms_module.course_registration_configuration.test_service -v
```

Tests cover business rules, atomic-save error paths, payload validation, missing/invalid authentication, PDF generation, and highest-credit aggregation. HTTP tests use an in-process ASGI driver and do not require httpx. Service write tests use mocks and do not change the live database.

The migration workspace also contains read-only database smoke checks, React tests and a targeted TypeScript check. Read-only SQL checks verify the real schema and summaries. A full production build and live write round trip are separate deployment checks; no student or setup records were modified during migration.
