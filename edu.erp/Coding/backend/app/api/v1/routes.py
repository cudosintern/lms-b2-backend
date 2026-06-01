from fastapi import APIRouter
from ...api.auth import login
from app.api.v1.cudo_module.curriculum.delivery_method.curriculum_delivery_method import (
    router as curriculum_delivery_router
)
# from ...api.v1.home import dashboard_info 
# from ...api.v1.configurations.all_master import all_master
# from ...api.v1.configurations.usermaster import user_master
# from ...api.v1.configurations.userroles import user_roles
# from ...api.v1.configurations.useraccess import user_access
# from ...api.v1.configurations.staff_course_allocation import staff_course_allocation
# from ...api.v1.configurations.department import department
# from ...api.v1.configurations.program import program
# from ...api.v1.configurations.program_type import program_type
# from ...api.v1.academics.academic_batch import academic_batch
# from ...api.v1.academics.academic_calender import academic_calender
# from ...api.v1.academics.course import course
# from ...api.v1.academics.bulk_course_import import bulk_course_import
# from ...api.v1.academics.event_calender import event_calender
# from ...api.v1.academics.semester import semester
# from ...api.v1.academics.class_time_table import class_time_table
# from ...api.v1.examination.exam_time_table import exam_time_table
# from ...api.v1.registration.student_admission_lite import student_admission_lite
# from ...api.v1.registration.student_admission import student_admission
# from ...api.v1.registration.bulk_course_registration import bulk_course_registration
# from ...api.v1.registration.course_registration import course_registration
# from ...api.v1.registration.student_allocation import student_allocation
# from ...api.v1.registration.examiner_registration import examiner_registration
# from ...api.v1.comman_functions import comman_function
# from ...api.v1.registration.student_exam_registration import student_exam_registration
# from ...api.v1.exam_eligibility.attendence import attendence
# from ...api.v1.exam_eligibility.cia_process import cia_process
# from ...api.v1.exam_eligibility.elgibility_list import elgibility_list
# from ...api.v1.exam_eligibility.grace_attendence import grace_attendence
# from ...api.v1.registration.open_elective_entry import open_elective_entry
# from ...api.v1.examination.lab_batch_allocation import lab_batch_allocation
# #below sub_occasions_lab_theroy_cia part of sub occasion cia and also lab theory
# from .exam_eligibility.sub_occasions import sub_occasions_lab_theroy_cia 
# from ...api.v1.examination.examiner_lab_batch_allocation import examiner_lab_batch_allocation
# from ...api.v1.examination.exam_hall_allocation import exam_hall_allocation
# from ...api.v1.examination.examiner_lab_batch_marks import examiner_lab_batch_marks
# from ...api.v1.evaluation.grade_processing import grade_processing
# from ...api.v1.examination.transitional_grade import transitional_grade
# from ...api.v1.examination.rollback import rollback
# from ...api.v1.registration.fasttrack_registration import fasttrack_registration
# from ...api.v1.registration.backlog_registration import backlog_registration
# from ...api.v1.registration.supplimentary_registration import supplimentary_registration
# from ...api.v1.registration.makeup_registration import makeup_registration
# from ...api.v1.registration.department_change import department_change
# from ...api.v1.evaluation.exam_marks import exam_marks
# from ...api.v1.evaluation.grace_marks_see import grace_marks_see
# from ...api.v1.evaluation.exam_attendence import exam_attendence
# from ...api.v1.evaluation.re_evaluation_grade import re_evaluation_grade
# from ...api.v1.evaluation.re_evaluation_marks import re_evaluation_marks
# from ...api.v1.evaluation.vertical_progression import vertical_progression
# from ...api.v1.registration.re_evaluation_registration import re_evaluation_registration
# from ...api.v1.reports.grade_card import grade_card
# from ...api.v1.reports.eligibilty_list_report import eligibilty_list_report
# from ...api.v1.reports.analysis_report import analysis_report
# from ...api.v1.reports.annual_report import annual_report
# from ...api.v1.reports.award_of_degree import award_of_degree
# from ...api.v1.reports.cia_report import cia_report
# from ...api.v1.reports.convocation_report import convocation_report
# from ...api.v1.reports.grade_card_ack_report import grade_card_ack_report
# from ...api.v1.reports.search_student import search_student
# from ...api.v1.reports.student_list_report import student_list_report
# from ...api.v1.reports.transcript import transcript
# from ...api.v1.reports.student_promotion import student_promotion
# from ...api.v1.reports.result_sheet import result_sheet
# from ...api.v1.reports.nad_report import nad_report
# from ...api.v1.reports.hall_ticket import hall_ticket
# from ...api.v1.reports.grade_report import grade_report
# from ...api.v1.reports.caste_wise_analysis import caste_wise_analysis
# from ...api.v1.reports.provisional_grade_card import provisional_grade_card
# from ...api.v1.reports.student_track_report import student_track_report
# from ...api.v1.reports.eligibility_ineligibility_report import eligibility_ineligibility_report
# from ...api.v1.reports.consolidated_ne_studentslist import consolidated_ne_studentslist
# from ...api.v1.reports.consolidated_see_absentees_list import consolidated_see_absentees_list
# from ...api.v1.reports.student_results import student_result
# from ...api.v1.reports.consolidated_form_a import consolidated_form_a
# from ...api.v1.reports.consolidated_course_reg_report import consolidated_course_reg_report
# from ...api.v1.hostel_module.hostels import get_hostels, add_hostel, edit_hostel
# from ...api.v1.hostel_module.room_allotment_queue import room_allotment_queue
# from app.api.v1.transport_module.vehicle_schedule import vehicle_schedule
# from app.api.v1.hostel_module.hostel_dashboard import hostel_dashboard
# from ...api.v1.hostel_module.wings_blocks import wings_blocks
# from ...api.v1.hostel_module.category import category
# from ...api.v1.hostel_module.hostel_room_tariff import hostel_room_tariff
# from app.api.v1.hostel_module.hostel_rooms import hostel_rooms

from ...api.auth import login
# from ...api.v1.ems_module.home import dashboard_info
# from ...api.v1.ems_module.configurations.all_master import all_master
# from ...api.v1.ems_module.configurations.usermaster import user_master
# from ...api.v1.ems_module.configurations.userroles import user_roles
# from ...api.v1.ems_module.configurations.useraccess import user_access
# from ...api.v1.ems_module.configurations.staff_course_allocation import (
#     staff_course_allocation,
# )
from ...api.v1.ems_module.configurations.department import department
# from ...api.v1.ems_module.configurations.program import program
# from ...api.v1.ems_module.configurations.program_type import program_type
# from ...api.v1.ems_module.academics.academic_batch import academic_batch
# from ...api.v1.ems_module.academics.academic_calender import academic_calender
# from ...api.v1.ems_module.academics.course import course
# from ...api.v1.ems_module.academics.bulk_course_import import bulk_course_import
# from ...api.v1.ems_module.academics.event_calender import event_calender
# from ...api.v1.ems_module.academics.semester import semester
# from ...api.v1.ems_module.academics.class_time_table import class_time_table
# from ...api.v1.ems_module.examination.exam_time_table import exam_time_table
# from ...api.v1.ems_module.registration.student_admission_lite import (
#     student_admission_lite,
# )
# from ...api.v1.ems_module.registration.student_admission import student_admission
# from ...api.v1.ems_module.registration.bulk_course_registration import (
#     bulk_course_registration,
# )
# from ...api.v1.ems_module.registration.course_registration import course_registration
# from ...api.v1.ems_module.registration.student_allocation import student_allocation
# from ...api.v1.ems_module.registration.examiner_registration import (
#     examiner_registration,
# )
from ...api.v1.ems_module.comman_functions import comman_function
# from ...api.v1.ems_module.registration.student_exam_registration import (
#     student_exam_registration,
# )
# from ...api.v1.ems_module.exam_eligibility.attendence import attendence
# from ...api.v1.ems_module.exam_eligibility.cia_process import cia_process
# from ...api.v1.ems_module.exam_eligibility.elgibility_list import elgibility_list
# from ...api.v1.ems_module.exam_eligibility.grace_attendence import grace_attendence
# from ...api.v1.ems_module.registration.open_elective_entry import open_elective_entry
# from ...api.v1.ems_module.examination.lab_batch_allocation import lab_batch_allocation

# # below sub_occasions_lab_theroy_cia part of sub occasion cia and also lab theory

# from ...api.v1.ems_module.exam_eligibility.sub_occasions import (
#     sub_occasions_lab_theroy_cia,
# )
# from ...api.v1.ems_module.examination.examiner_lab_batch_allocation import (
#     examiner_lab_batch_allocation,
# )
# from ...api.v1.ems_module.examination.exam_hall_allocation import exam_hall_allocation
# from ...api.v1.ems_module.examination.examiner_lab_batch_marks import (
#     examiner_lab_batch_marks,
# )
# from ...api.v1.ems_module.evaluation.grade_processing import grade_processing
# from ...api.v1.ems_module.examination.transitional_grade import transitional_grade
# from ...api.v1.ems_module.examination.rollback import rollback
# from ...api.v1.ems_module.registration.fasttrack_registration import (
#     fasttrack_registration,
# )
# from ...api.v1.ems_module.registration.backlog_registration import backlog_registration
# from ...api.v1.ems_module.registration.supplimentary_registration import (
#     supplimentary_registration,
# )
# from ...api.v1.ems_module.registration.makeup_registration import makeup_registration
# from ...api.v1.ems_module.registration.department_change import department_change
# from ...api.v1.ems_module.evaluation.exam_marks import exam_marks
# from ...api.v1.ems_module.evaluation.grace_marks_see import grace_marks_see
# from ...api.v1.ems_module.evaluation.exam_attendence import exam_attendence
# from ...api.v1.ems_module.evaluation.re_evaluation_grade import re_evaluation_grade
# from ...api.v1.ems_module.evaluation.re_evaluation_marks import re_evaluation_marks
# from ...api.v1.ems_module.evaluation.vertical_progression import vertical_progression
# from ...api.v1.ems_module.registration.re_evaluation_registration import (
#     re_evaluation_registration,
# )
# from ...api.v1.ems_module.reports.grade_card import grade_card
# from ...api.v1.ems_module.reports.eligibilty_list_report import eligibilty_list_report
# from ...api.v1.ems_module.reports.analysis_report import analysis_report
# from ...api.v1.ems_module.reports.annual_report import annual_report
# from ...api.v1.ems_module.reports.award_of_degree import award_of_degree
# from ...api.v1.ems_module.reports.cia_report import cia_report
# from ...api.v1.ems_module.reports.convocation_report import convocation_report
# from ...api.v1.ems_module.reports.grade_card_ack_report import grade_card_ack_report
# from ...api.v1.ems_module.reports.search_student import search_student
# from ...api.v1.ems_module.reports.student_list_report import student_list_report
# from ...api.v1.ems_module.reports.transcript import transcript
# from ...api.v1.ems_module.reports.student_promotion import student_promotion
# from ...api.v1.ems_module.reports.result_sheet import result_sheet
# from ...api.v1.ems_module.reports.nad_report import nad_report
# from ...api.v1.ems_module.reports.hall_ticket import hall_ticket
# from ...api.v1.ems_module.reports.grade_report import grade_report
# from ...api.v1.ems_module.reports.caste_wise_analysis import caste_wise_analysis
# from ...api.v1.ems_module.reports.provisional_grade_card import provisional_grade_card
# from ...api.v1.ems_module.reports.student_track_report import student_track_report
# from ...api.v1.ems_module.reports.eligibility_ineligibility_report import (
#     eligibility_ineligibility_report,
# )
# from ...api.v1.ems_module.reports.consolidated_ne_studentslist import (
#     consolidated_ne_studentslist,
# )
# from ...api.v1.ems_module.reports.consolidated_see_absentees_list import (
#     consolidated_see_absentees_list,
# )
# from ...api.v1.ems_module.reports.student_results import student_result
# from ...api.v1.ems_module.reports.consolidated_form_a import consolidated_form_a
# from ...api.v1.ems_module.reports.consolidated_course_reg_report import (
#     consolidated_course_reg_report,
# )



# #Admission Module
# #api
# from app.api.v1.admission_module.routes.api.Api import router as api_router
# from app.api.v1.admission_module.routes.api.CRM_students import router as CRM_students_router
# from app.api.v1.admission_module.routes.api.Dashboards import router as Dashboards_router
# from app.api.v1.admission_module.routes.api.Departments import router as Departments_router
# from app.api.v1.admission_module.routes.api.Programs import router as Programs_router
# from app.api.v1.admission_module.routes.api.Schools import router as Schools_router
# from app.api.v1.admission_module.routes.api.University_organization import router as University_organization_router
# from app.api.v1.admission_module.routes.api.Users import router as Users_router

#masters
# from app.api.v1.admission_module.routes.masters.Boards_or_universities import router as board_or_universities_router
# from app.api.v1.admission_module.routes.masters.Iems_parent_occupation_masters import router as iems_parent_occupation_masters_router
# from ...api.v1.hostel_module.hostel_rooms import hostel_rooms

# #api configs
# from app.api.v1.admission_module.routes.api_configs.api_configs import router as api_configs_router

# #app routes
# from app.api.v1.admission_module.routes.app_routes.app_routes import router as app_routes_router

# #cruds
# from app.api.v1.admission_module.routes.cruds.Cruds import router as cruds_router

# #employee
# from app.api.v1.admission_module.routes.employee.Manage_employees import router as Manage_employee_router

# #instant fee
#from app.api.v1.admission_module.routes.instant_fee.Instant_fee_collection import router as Instant_fee_collection_router

# #Manage register config
# from app.api.v1.admission_module.routes.manager_register_configuration.Manage_register_configuration import router as Manage_register_configuration_router

# #masters
# from app.api.v1.admission_module.routes.masters.Boards_or_universities import router as Boards_or_universities_router
# from app.api.v1.admission_module.routes.masters.Castes import router as Castes_router
# from app.api.v1.admission_module.routes.masters.Citys import router as Citys_router
# from app.api.v1.admission_module.routes.masters.Countries import router as Countries_router
# from app.api.v1.admission_module.routes.masters.Districts import router as Districts_router
# from app.api.v1.admission_module.routes.masters.Iems_academic_batches import router as Iems_academic_batches_router
# from app.api.v1.admission_module.routes.masters.Iems_admission_quotas import router as Iems_admission_quotas_router
#from app.api.v1.admission_module.routes.masters.Iems_candidate_type_master import router as Iems_candidate_type_master_router
# from app.api.v1.admission_module.routes.masters.Iems_category_type_master import router as Iems_category_type_master_router
# from app.api.v1.admission_module.routes.masters.Iems_certificate_type_master import router as Iems_certificate_type_master_router
# from app.api.v1.admission_module.routes.masters.Iems_college_bank_infos import router as Iems_college_bank_infos_router
# from app.api.v1.admission_module.routes.masters.Iems_degree_masters import router as Iems_degree_masters_router
# from app.api.v1.admission_module.routes.masters.Iems_departments import router as Iems_departments_router
# from app.api.v1.admission_module.routes.masters.Iems_higher_admission_fee_heads import router as Iems_higher_admission_fee_heads_router
# from app.api.v1.admission_module.routes.masters.Iems_higher_admission_fee_types import router as Iems_higher_admission_fee_types_router
# from app.api.v1.admission_module.routes.masters.Iems_org_configs import router as Iems_org_configs_router
# from app.api.v1.admission_module.routes.masters.Iems_organisation_types import router as Iems_organisation_types_router
# from app.api.v1.admission_module.routes.masters.Iems_organisations import router as Iems_organisations_router
# from app.api.v1.admission_module.routes.masters.Iems_parent_occupation_masters import router as Iems_parent_occupation_masters_router
# from app.api.v1.admission_module.routes.masters.Iems_program_types import router as Iems_program_types_router
# from app.api.v1.admission_module.routes.masters.Iems_programs_backup import router as Iems_programs_backup_router
# from app.api.v1.admission_module.routes.masters.Iems_programs import router as Iems_programs_router
# from app.api.v1.admission_module.routes.masters.Iems_qualification_subject_masters import router as Iems_qualification_subject_masters_router
# from app.api.v1.admission_module.routes.masters.Iems_semesters import router as Iems_semesters_router
# from app.api.v1.admission_module.routes.masters.Iems_speach_languages import router as Iems_speach_languages_router
# #from app.api.v1.admission_module.routes.masters.Iems_universities import router as Iems_universities_router
# #from app.api.v1.admission_module.routes.masters.Iems_user_orgs import router as Iems_user_orgs_router
# #from app.api.v1.admission_module.routes.masters.Program_mode import router as Program_mode_router
# from app.api.v1.admission_module.routes.masters.Referrals import router as Referrals_router
# from app.api.v1.admission_module.routes.masters.Refund_type import router as Refund_type_router
# from app.api.v1.admission_module.routes.masters.Religions import router as Religions_router
# from app.api.v1.admission_module.routes.masters.Sections import router as Sections_router
# from app.api.v1.admission_module.routes.masters.States import router as States_router

# #menus
# from app.api.v1.admission_module.routes.menus.Menus import router as Menus_router

# #rbac
# from app.api.v1.admission_module.routes.rbac.Delegated_roles import router as delegated_roles_router
# from app.api.v1.admission_module.routes.rbac.Erp_rbac_roles import router as Erp_rbac_roles_router
# from app.api.v1.admission_module.routes.rbac.Erp_Rbac_users import router as Erp_Rbac_users_router
# from app.api.v1.admission_module.routes.rbac.Manage_staffs import router as Manage_staffs_router
# from api.v1.admission_module.routes.rbac.Rbac_actions import router as rbac_actions_router
# from api.v1.admission_module.routes.rbac.Rbac_custom_permissions import router as rbac_custom_permission_router
# from api.v1.admission_module.routes.rbac.Rbac_menus import router as Rbac_menus_router
# from api.v1.admission_module.routes.rbac.Rbac_modules import router as Rbac_modules_router
# from api.v1.admission_module.routes.rbac.Rbac_permissions import router as Rbac_permissions_router
# from api.v1.admission_module.routes.rbac.Rbac_role_permissions import router as Rbac_role_permissions_router

# #reports
# from api.v1.admission_module.routes.reports.Admission_report_summary import router as Admission_report_summary_router
# from api.v1.admission_module.routes.reports.Branch_wise_report import router as Branch_wise_report_router
# from app.api.v1.admission_module.routes.reports.Cancel_of_admission import router as Cancel_student_list_report_router
# from app.api.v1.admission_module.routes.reports.Category_wise_report import router as Category_wise_report_router
# from app.api.v1.admission_module.routes.reports.Consolidate_admission_report import router as Consolidate_admission_report_router
# # from api.v1.admission_module.routes.reports.Cut_off_rank_report import router as Cut_off_rank_report_router
# from app.api.v1.admission_module.routes.reports.Fees_collection_categorywise_report import router as Fees_collection_category_wise_report_report_router
# from app.api.v1.admission_module.routes.reports.Full_transaction_report import router as Full_transaction_report_router
# # from api.v1.admission_module.routes.reports.Ioncudos_import import router as Ioncudos_import_router
# from app.api.v1.admission_module.routes.reports.Ionems_import import router as Ionems_import_router
# from app.api.v1.admission_module.routes.reports.Quota_wise_report import router as Quota_wise_report_router
# # from api.v1.admission_module.routes.reports.Sales_management_app_report import router as Sales_management_app_report_router
# # from api.v1.admission_module.routes.reports.Scholarship_refund_report import router as Scholarship_refund_report_router
# from app.api.v1.admission_module.routes.reports.School_admission_report import router as School_admission_report_router
# from app.api.v1.admission_module.routes.reports.Student_seat_list_report import router as Student_seat_list_report_router
# from app.api.v1.admission_module.routes.reports.Student_transaction_report import router as Student_transaction_report_router
# #from app.api.v1.admission_module.routes.reports.Students_report import router as Students_report_router
# from app.api.v1.admission_module.routes.reports.User_wise_fee_collection_report import router as User_wise_fee_collection_report_router

# #seat enquiry
# from api.v1.admission_module.routes.seat_enquiry.Student_enquiry import router as Student_enquiry_router

# #seats
# from app.api.v1.admission_module.routes.seats.Seats import router as Seats_router

# #students
# from app.api.v1.admission_module.routes.students.Challans import router as Challans_router
# from api.v1.admission_module.routes.students.Manage_students import router as Manage_students_router
#from app.api.v1.admission_module.routes.students.Registers import router as Registers_router
# from api.v1.admission_module.routes.students.Rename_folders_with_excel import router as Rename_folders_with_excel_router
# from api.v1.admission_module.routes.students.Student_generic_refund import router as Student_generic_refund_router
# from api.v1.admission_module.routes.students.Student_inquiries import router as Student_inquiries_router
# from api.v1.admission_module.routes.students.Student_next_year_admission import router as Student_next_year_admission_router
# from api.v1.admission_module.routes.students.Student_parent_profiles import router as Student_parent_profiles_admission_router
# from api.v1.admission_module.routes.students.Student_profiles import router as Student_profiles_router
# from app.api.v1.admission_module.routes.students.Student_upload_usn import router as Student_upload_usn_router
# from api.v1.admission_module.routes.students.Student_users import router as Student_users_router
# from api.v1.admission_module.routes.students.Student_vertical_mobility import router as Student_vertical_mobility_router
# from api.v1.admission_module.routes.students.Students_bulk_import import router as Students_bulk_import_router
# from app.api.v1.admission_module.routes.students.Students import router as Students_router





# transport
# from app.api.v1.transport_module.vehicles import vehicles
# from app.api.v1.transport_module.vehicle_routes import vehicle_routes
# from app.api.v1.transport_module.employees import employee
# from app.api.v1.transport_module.tariff import tariff
# from app.api.v1.transport_module.student_route import student_route

#board of studies members
from app.api.v1.cudo_module.board_of_studies.api.bos_member_api import (
    router as bos_member_router
)

from app.api.v1.cudo_module.users.api.user_api import (
    router as user_router
)

from app.api.v1.cudo_module.bloom_domain.api.bloom_domain_api import (
    router as bloom_domain_router
)
from app.api.v1.cudo_module.delivery_method.api.delivery_method_api import (
    router as delivery_method_router
)
from app.api.v1.cudo_module.program_mode.api.program_mode_api import (
    router as program_mode_router
)

# Main API router
from app.api.v1.cudo_module.map_level_weightage.map_level_weightage import (
    router as map_level_weightage_router
)

# Program Outcome router
from app.api.v1.cudo_module.program_outcome.api.po_type_api import (
    router as program_outcome_router
)

from app.api.v1.cudo_module.generic_program_outcome.generic_po_api import (
    router as generic_program_outcome_router
)

from app.api.v1.cudo_module.lab_category.lab_category_api import (
    router as lab_category_router
)


from app.api.v1.cudo_module.manage_knowledge_and_attitude_profile.api import (
    router as manage_knowledge_and_attitude_profile_router
)


router = APIRouter()

router.include_router(
    bloom_domain_router, prefix="/bloom_domain", tags=["Bloom Domain"]
)
router.include_router(
    curriculum_delivery_router,
    prefix="/curriculum/curriculum_delivery_method",
    tags=["Curriculum Delivery Method"]
)

router.include_router(
    user_router, prefix="/user", tags=["User"]
)

router.include_router(
    manage_knowledge_and_attitude_profile_router, prefix="/manage_knowledge_and_attitude_profile", tags=["Manage Knowledge and Attitude Profile"]
)

## Below include all modules routes

# Include auth routes
# router.include_router(login.router, prefix="/auth", tags=["auth"])
# router.include_router(register.router, prefix="/auth", tags=["auth"])
# router.include_router(refresh_token.router, prefix="/auth", tags=["auth"])

# Include routes for registartion module
router.include_router(login.router, prefix="/staff_student_login", tags=["auth"])

# Include routes for dashboard module
# router.include_router(dashboard_info.router, prefix="/dashboard_info_route", tags=["auth"])

# Include routes for comman function  module
router.include_router(comman_function.router, prefix="/comman_function", tags=["auth"])

# Include routes for configuration module
# router.include_router(all_master.router, prefix="/all_master", tags=["auth"])
# router.include_router(user_master.router, prefix="/user_master", tags=["auth"])
# router.include_router(user_roles.router, prefix="/user_roles", tags=["auth"])
# router.include_router(user_access.router, prefix="/user_acccess", tags=["auth"])
# router.include_router(staff_course_allocation.router, prefix="/user_courses", tags=["auth"])
router.include_router(department.router, prefix="/department", tags=["auth"])
# router.include_router(program.router, prefix="/program", tags=["auth"])
# router.include_router(program_type.router, prefix="/program_type", tags=["auth"])

# # Include routes for academic module
# router.include_router(academic_batch.router, prefix="/academic_batch", tags=["auth"])
# router.include_router(academic_calender.router, prefix="/academic_calender", tags=["auth"])
# router.include_router(course.router, prefix="/course_type", tags=["auth"])
# router.include_router(event_calender.router, prefix="/event_calender", tags=["auth"])
# router.include_router(semester.router, prefix="/semester", tags=["auth"])
# router.include_router(class_time_table.router, prefix="/class_time_table", tags=["auth"])
# router.include_router(bulk_course_import.router, prefix="/bulk_course_import", tags=["auth"])

# # Include routes for registartion module
# router.include_router(student_admission_lite.router, prefix="/registration_std_lite", tags=["auth"])
# router.include_router(student_admission.router, prefix="/registration_std", tags=["auth"])
# router.include_router(bulk_course_registration.router, prefix="/bulk_reg", tags=["auth"])
# router.include_router(course_registration.router, prefix="/course_reg", tags=["auth"])
# router.include_router(student_allocation.router, prefix="/student_alc", tags=["auth"])
# router.include_router(examiner_registration.router, prefix="/examiner_reg", tags=["auth"])
# router.include_router(student_exam_registration.router, prefix="/std_exam_reg", tags=["auth"])
# router.include_router(open_elective_entry.router, prefix="/open_elective_entry", tags=["auth"])
# router.include_router(backlog_registration.router, prefix="/backlog_registration", tags=["auth"])
# router.include_router(supplimentary_registration.router, prefix="/supplimentary_registration", tags=["auth"])
# router.include_router(makeup_registration.router, prefix="/makeup_registration", tags=["auth"])
# router.include_router(re_evaluation_registration.router, prefix="/re_evaluation_registration", tags=["auth"])
# router.include_router(fasttrack_registration.router, prefix="/fasttrack_registration", tags=["auth"])
# router.include_router(department_change.router, prefix="/department_change", tags=["auth"])


# # Include routes for exam eligibility module
# router.include_router(attendence.router, prefix="/attendence", tags=["auth"])
# router.include_router(cia_process.router, prefix="/cia_process", tags=["auth"])
# router.include_router(elgibility_list.router, prefix="/elgibility_list", tags=["auth"])
# router.include_router(grace_attendence.router, prefix="/grace_attendence", tags=["auth"])
# router.include_router(sub_occasions_lab_theroy_cia.router, prefix="/lab_theroy_cia", tags=["auth"])


# # Include routes for examination module
# router.include_router(lab_batch_allocation.router, prefix="/lab_batch_allocation", tags=["auth"])
# router.include_router(examiner_lab_batch_allocation.router, prefix="/examiner_lab_batch_allocation", tags=["auth"])
# router.include_router(exam_hall_allocation.router, prefix="/exam_hall_allocation", tags=["auth"])
# router.include_router(examiner_lab_batch_marks.router, prefix="/examiner_lab_exam_marks", tags=["auth"])
# router.include_router(transitional_grade.router, prefix="/transitional_grade", tags=["auth"])
# router.include_router(rollback.router, prefix="/rollback", tags=["auth"])
# router.include_router(exam_time_table.router, prefix="/exam_time_table", tags=["auth"])


# # Include routes for evaluation module
# router.include_router(grade_processing.router, prefix="/grade_processing", tags=["auth"])
# router.include_router(exam_marks.router, prefix="/exam_marks", tags=["auth"])
# router.include_router(grace_marks_see.router, prefix="/grace_marks_see", tags=["auth"])
# router.include_router(exam_attendence.router, prefix="/exam_attendence", tags=["auth"])
# router.include_router(re_evaluation_grade.router, prefix="/re_evaluation_grade", tags=["auth"])
# router.include_router(re_evaluation_marks.router, prefix="/re_evaluation_marks", tags=["auth"])
# router.include_router(vertical_progression.router, prefix="/vertical_progression", tags=["auth"])


# # Include routes for report module
# router.include_router(grade_card.router, prefix="/grade_card", tags=["auth"])
# router.include_router(eligibilty_list_report.router, prefix="/eligibilty_list_report", tags=["auth"])
# router.include_router(analysis_report.router, prefix="/analysis_report", tags=["auth"])
# router.include_router(annual_report.router, prefix="/annual_report", tags=["auth"])
# router.include_router(award_of_degree.router, prefix="/award_of_degree", tags=["auth"])
# router.include_router(cia_report.router, prefix="/cia_report", tags=["auth"])
# router.include_router(convocation_report.router, prefix="/convocation_report", tags=["auth"])
# router.include_router(grade_card_ack_report.router, prefix="/grade_card_ack_report", tags=["auth"])
# router.include_router(search_student.router, prefix="/search_student", tags=["auth"])
# router.include_router(student_list_report.router, prefix="/student_list_report", tags=["auth"])
# router.include_router(transcript.router, prefix="/transcript", tags=["auth"])
# router.include_router(student_promotion.router, prefix="/student_promotion", tags=["auth"])
# router.include_router(result_sheet.router, prefix="/result_sheet", tags=["auth"])
# router.include_router(nad_report.router, prefix="/nad_report", tags=["auth"])
# router.include_router(hall_ticket.router, prefix="/hall_ticket", tags=["auth"])
# router.include_router(grade_report.router, prefix="/grade_report", tags=["auth"])
# router.include_router(caste_wise_analysis.router, prefix="/caste_wise_analysis", tags=["auth"])
# router.include_router(provisional_grade_card.router, prefix="/provisional_grade_card", tags=["auth"])
# router.include_router(student_track_report.router, prefix="/student_track_report", tags=["auth"])
# router.include_router(eligibility_ineligibility_report.router, prefix="/eligibility_ineligibility_report", tags=["auth"])
# router.include_router(consolidated_ne_studentslist.router, prefix="/consolidated_ne_studentslist", tags=["auth"])
# router.include_router(consolidated_see_absentees_list.router, prefix="/consolidated_see_absentees_list", tags=["auth"])
# router.include_router(student_result.router, prefix="/student_result", tags=["auth"])
# router.include_router(consolidated_form_a.router, prefix="/consolidated_form_a", tags=["auth"])
# router.include_router(consolidated_course_reg_report.router, prefix="/consolidated_course_reg_report", tags=["auth"])

# # Include hostels routes
# router.include_router(get_hostels.router, prefix="/hostels", tags=["hostels"])
# router.include_router(add_hostel.router, prefix="/hostels", tags=["hostels"])
# router.include_router(edit_hostel.router, prefix="/hostels", tags=["hostels"])
# router.include_router(room_allotment_queue.router, prefix="/room_allotment", tags=["hostels"])
# router.include_router(wings_blocks.router, prefix="/wings_blocks", tags=["auth"])
# router.include_router(category.router, prefix="/category", tags=["auth"])
# router.include_router(hostel_rooms.router, prefix="/hostel_rooms", tags=["hostels"])
# router.include_router(hostel_room_tariff.router, prefix="/hostel_room_tariff", tags=["auth"])
# router.include_router(hostel_dashboard.router, prefix="/hostels", tags=["hostels"])
# router.include_router(vehicle_schedule.router, prefix="/transport", tags=['transport'])


router.include_router(login.router, prefix="/staff_student_login", tags=["Login"])

# Include routes for dashboard module
# router.include_router(
#     dashboard_info.router, prefix="/dashboard_info_route", tags=["EMS-dashboard"]
# )

# Include routes for comman function  module
# router.include_router(
#     comman_function.router, prefix="/comman_function", tags=["EMS-comman_function"]
# )

router.include_router(
    bloom_domain_router, prefix="/bloom_domain", tags=["Bloom Domain"]
)

router.include_router(
    program_mode_router, prefix="/program_mode", tags=["Program Mode"]
)

# Include routes for configuration module
# router.include_router(
#     all_master.router, prefix="/all_master", tags=["EMS-configuration"]
# )
# router.include_router(
#     user_master.router, prefix="/user_master", tags=["EMS-configuration"]
# )
# router.include_router(
#     user_roles.router, prefix="/user_roles", tags=["EMS-configuration"]
# )
# router.include_router(
#     user_access.router, prefix="/user_acccess", tags=["EMS-configuration"]
# )
# router.include_router(
#     staff_course_allocation.router, prefix="/user_courses", tags=["EMS-configuration"]
# )
router.include_router(
    department.router, prefix="/department", tags=["EMS-configuration"]
)
# router.include_router(program.router, prefix="/program", tags=["EMS-configuration"])
# router.include_router(
#     program_type.router, prefix="/program_type", tags=["EMS-configuration"]
# )

# # Include routes for academic module
# router.include_router(
#     academic_batch.router, prefix="/academic_batch", tags=["EMS-academic"]
# )
# router.include_router(
#     academic_calender.router, prefix="/academic_calender", tags=["EMS-academic"]
# )
# router.include_router(course.router, prefix="/course_type", tags=["EMS-academic"])
# router.include_router(
#     event_calender.router, prefix="/event_calender", tags=["EMS-academic"]
# )
# router.include_router(semester.router, prefix="/semester", tags=["EMS-academic"])
# router.include_router(
#     class_time_table.router, prefix="/class_time_table", tags=["EMS-academic"]
# )
# router.include_router(
#     bulk_course_import.router, prefix="/bulk_course_import", tags=["EMS-academic"]
# )

# # Include routes for registartion module
# router.include_router(
#     student_admission_lite.router,
#     prefix="/registration_std_lite",
#     tags=["EMS-registartion"],
# )
# router.include_router(
#     student_admission.router, prefix="/registration_std", tags=["EMS-registartion"]
# )
# router.include_router(
#     bulk_course_registration.router, prefix="/bulk_reg", tags=["EMS-registartion"]
# )
# router.include_router(
#     course_registration.router, prefix="/course_reg", tags=["EMS-registartion"]
# )
# router.include_router(
#     student_allocation.router, prefix="/student_alc", tags=["EMS-registartion"]
# )
# router.include_router(
#     examiner_registration.router, prefix="/examiner_reg", tags=["EMS-registartion"]
# )
# router.include_router(
#     student_exam_registration.router, prefix="/std_exam_reg", tags=["EMS-registartion"]
# )
# router.include_router(
#     open_elective_entry.router, prefix="/open_elective_entry", tags=["EMS-registartion"]
# )
# router.include_router(
#     backlog_registration.router,
#     prefix="/backlog_registration",
#     tags=["EMS-registartion"],
# )
# router.include_router(
#     supplimentary_registration.router,
#     prefix="/supplimentary_registration",
#     tags=["EMS-registartion"],
# )
# router.include_router(
#     makeup_registration.router, prefix="/makeup_registration", tags=["EMS-registartion"]
# )
# router.include_router(
#     re_evaluation_registration.router,
#     prefix="/re_evaluation_registration",
#     tags=["EMS-registartion"],
# )
# router.include_router(
#     fasttrack_registration.router,
#     prefix="/fasttrack_registration",
#     tags=["EMS-registartion"],
# )
# router.include_router(
#     department_change.router, prefix="/department_change", tags=["EMS-registartion"]
# )


# # Include routes for exam eligibility module
# router.include_router(
#     attendence.router, prefix="/attendence", tags=["EMS-exam eligibility"]
# )
# router.include_router(
#     cia_process.router, prefix="/cia_process", tags=["EMS-exam eligibility"]
# )
# router.include_router(
#     elgibility_list.router, prefix="/elgibility_list", tags=["EMS-exam eligibility"]
# )
# router.include_router(
#     grace_attendence.router, prefix="/grace_attendence", tags=["EMS-exam eligibility"]
# )
# router.include_router(
#     sub_occasions_lab_theroy_cia.router,
#     prefix="/lab_theroy_cia",
#     tags=["EMS-exam eligibility"],
# )


# # Include routes for examination module
# router.include_router(
#     lab_batch_allocation.router,
#     prefix="/lab_batch_allocation",
#     tags=["EMS-examination"],
# )
# router.include_router(
#     examiner_lab_batch_allocation.router,
#     prefix="/examiner_lab_batch_allocation",
#     tags=["EMS-examination"],
# )
# router.include_router(
#     exam_hall_allocation.router,
#     prefix="/exam_hall_allocation",
#     tags=["EMS-examination"],
# )
# router.include_router(
#     examiner_lab_batch_marks.router,
#     prefix="/examiner_lab_exam_marks",
#     tags=["EMS-examination"],
# )
# router.include_router(
#     transitional_grade.router, prefix="/transitional_grade", tags=["EMS-examination"]
# )
# router.include_router(rollback.router, prefix="/rollback", tags=["EMS-examination"])
# router.include_router(
#     exam_time_table.router, prefix="/exam_time_table", tags=["EMS-examination"]
# )


# # Include routes for evaluation module
# router.include_router(
#     grade_processing.router, prefix="/grade_processing", tags=["EMS-evaluation"]
# )
# router.include_router(exam_marks.router, prefix="/exam_marks", tags=["EMS-evaluation"])
# router.include_router(
#     grace_marks_see.router, prefix="/grace_marks_see", tags=["EMS-evaluation"]
# )
# router.include_router(
#     exam_attendence.router, prefix="/exam_attendence", tags=["EMS-evaluation"]
# )
# router.include_router(
#     re_evaluation_grade.router, prefix="/re_evaluation_grade", tags=["EMS-evaluation"]
# )
# router.include_router(
#     re_evaluation_marks.router, prefix="/re_evaluation_marks", tags=["EMS-evaluation"]
# )
# router.include_router(
#     vertical_progression.router, prefix="/vertical_progression", tags=["EMS-evaluation"]
# )


# # Include routes for report module
# router.include_router(grade_card.router, prefix="/grade_card", tags=["EMS-report"])
# router.include_router(
#     eligibilty_list_report.router, prefix="/eligibilty_list_report", tags=["EMS-report"]
# )
# router.include_router(
#     analysis_report.router, prefix="/analysis_report", tags=["EMS-report"]
# )
# router.include_router(
#     annual_report.router, prefix="/annual_report", tags=["EMS-report"]
# )
# router.include_router(
#     award_of_degree.router, prefix="/award_of_degree", tags=["EMS-report"]
# )
# router.include_router(cia_report.router, prefix="/cia_report", tags=["EMS-report"])
# router.include_router(
#     convocation_report.router, prefix="/convocation_report", tags=["EMS-report"]
# )
# router.include_router(
#     grade_card_ack_report.router, prefix="/grade_card_ack_report", tags=["EMS-report"]
# )
# router.include_router(
#     search_student.router, prefix="/search_student", tags=["EMS-report"]
# )
# router.include_router(
#     student_list_report.router, prefix="/student_list_report", tags=["EMS-report"]
# )
# router.include_router(transcript.router, prefix="/transcript", tags=["EMS-report"])
# router.include_router(
#     student_promotion.router, prefix="/student_promotion", tags=["EMS-report"]
# )
# router.include_router(result_sheet.router, prefix="/result_sheet", tags=["EMS-report"])
# router.include_router(nad_report.router, prefix="/nad_report", tags=["EMS-report"])
# router.include_router(hall_ticket.router, prefix="/hall_ticket", tags=["EMS-report"])
# router.include_router(grade_report.router, prefix="/grade_report", tags=["EMS-report"])
# router.include_router(
#     caste_wise_analysis.router, prefix="/caste_wise_analysis", tags=["EMS-report"]
# )
# router.include_router(
#     provisional_grade_card.router, prefix="/provisional_grade_card", tags=["EMS-report"]
# )
# router.include_router(
#     student_track_report.router, prefix="/student_track_report", tags=["EMS-report"]
# )
# router.include_router(
#     eligibility_ineligibility_report.router,
#     prefix="/eligibility_ineligibility_report",
#     tags=["EMS-report"],
# )
# router.include_router(
#     consolidated_ne_studentslist.router,
#     prefix="/consolidated_ne_studentslist",
#     tags=["EMS-report"],
# )
# router.include_router(
#     consolidated_see_absentees_list.router,
#     prefix="/consolidated_see_absentees_list",
#     tags=["EMS-report"],
# )
# router.include_router(
#     student_result.router, prefix="/student_result", tags=["EMS-report"]
# )
# router.include_router(
#     consolidated_form_a.router, prefix="/consolidated_form_a", tags=["EMS-report"]
# )
# router.include_router(
#     consolidated_course_reg_report.router,
#     prefix="/consolidated_course_reg_report",
#     tags=["EMS-report"],
# )



# Admission_module
# api
# router.include_router(api_router, prefix="/v1", tags=["Api router"])
# router.include_router(CRM_students_router, prefix="/v1", tags=["CRM Students"])
# router.include_router(Dashboards_router, prefix="/v1", tags=["Dashboards"])
# router.include_router(Departments_router, prefix="/v1", tags=["Departments"])
# router.include_router(Programs_router, prefix="/v1", tags=["Programs"])
# router.include_router(Schools_router, prefix="/v1", tags=["Schools"])
# router.include_router(University_organization_router, prefix="/v1", tags=["University Organization"])
# router.include_router(Users_router, prefix="/v1", tags=["Users"])


# api congigs
# router.include_router(api_configs_router, prefix="/v1", tags=["Api Configs"])


# app routes
# router.include_router(app_routes_router, prefix="/v1", tags=["App Routes"])

# cruds
# router.include_router(cruds_router, prefix="/v1", tags=["Cruds"])

# employee
# router.include_router(Manage_employee_router, prefix="/v1", tags=["Manage Employee"])

# instant fee
# router.include_router(Instant_fee_collection_router, prefix="/v1", tags=["Instant Fee Collection"])

# Manage register config
# router.include_router(Manage_register_configuration_router, prefix="/v1", tags=["Manage Register Configuaration"])

# masters
# router.include_router(Boards_or_universities_router, prefix="/v1", tags=["Boards or Universities"])
# router.include_router(Castes_router, prefix="/v1", tags=["Castes"])
# router.include_router(Citys_router, prefix="/v1", tags=["Citys"])
# router.include_router(Countries_router, prefix="/v1", tags=["Countries"])
# router.include_router(Districts_router, prefix="/v1", tags=["Districts"])
# router.include_router(Iems_academic_batches_router, prefix="/v1", tags=["Iems Academic Batches"])
# router.include_router(Iems_admission_quotas_router, prefix="/v1", tags=["Iems Admission Quotas"])
# router.include_router(Iems_candidate_type_master_router, prefix="/v1", tags=["Iems_candidate_type_master"])
# router.include_router(Iems_category_type_master_router, prefix="/v1", tags=["Iems_category_type_master"])
# router.include_router(Iems_certificate_type_master_router, prefix="/v1", tags=["Iems_certificate_type_master"])
# router.include_router(Iems_college_bank_infos_router, prefix="/v1", tags=["Iems_college_bank_infos"])
# router.include_router(Iems_degree_masters_router, prefix="/v1", tags=["Iems_degree_masters"])
# router.include_router(Iems_departments_router, prefix="/v1", tags=["Iems_departments"])
# router.include_router(Iems_higher_admission_fee_heads_router, prefix="/v1", tags=["Iems_higher_admission_fee_heads"])
# router.include_router(Iems_higher_admission_fee_types_router, prefix="/v1", tags=["Iems_higher_admission_fee_types"])
# router.include_router(Iems_org_configs_router, prefix="/v1", tags=["Iems_org_configs"])
# router.include_router(Iems_organisation_types_router, prefix="/v1", tags=["Iems_organisation_types"])
# router.include_router(Iems_organisations_router, prefix="/v1", tags=["Iems_organisations"])
# router.include_router(Iems_parent_occupation_masters_router, prefix="/v1", tags=["Iems_parent_occupation_masters"])
# router.include_router(Iems_program_types_router, prefix="/v1", tags=["Iems_program_types_masters"])
# router.include_router(Iems_programs_backup_router, prefix="/v1", tags=["Iems_programs_backup"])
# router.include_router(Iems_programs_router, prefix="/v1", tags=["Iems_programs"])
# router.include_router(Iems_qualification_subject_masters_router, prefix="/v1", tags=["Iems_qualification_subject_masters"])
# router.include_router(Iems_semesters_router, prefix="/v1", tags=["Iems_semesters"])
# router.include_router(Iems_speach_languages_router, prefix="/v1", tags=["Iems_speach_languages"])
# router.include_router(Iems_universities_router, prefix="/v1", tags=["Iems_universities"])
# router.include_router(Iems_user_orgs_router, prefix="/v1", tags=["Iems_user_orgs"])
# router.include_router(Program_mode_router, prefix="/v1", tags=["Program_mode"])
# router.include_router(Referrals_router, prefix="/v1", tags=["Referrals"])
# router.include_router(Refund_type_router, prefix="/v1", tags=["Refund_type"])
# router.include_router(Religions_router, prefix="/v1", tags=["Religions"])
# router.include_router(Sections_router, prefix="/v1", tags=["Sections"])
# router.include_router(States_router, prefix="/v1", tags=["States"])

# menus
# router.include_router(Menus_router, prefix="/v1", tags=["Menus"])

# rbac
# router.include_router(delegated_roles_router, prefix="/v1", tags=["delegated_roles"])
# router.include_router(Erp_rbac_roles_router, prefix="/v1", tags=["Erp_rbac_roles"])
# router.include_router(Erp_Rbac_users_router, prefix="/v1", tags=["Erp_Rbac_users"])
# router.include_router(Manage_staffs_router, prefix="/v1", tags=["Manage_staffs"])
# router.include_router(rbac_actions_router, prefix="/v1", tags=["rbac_actions"])
# router.include_router(rbac_custom_permission_router, prefix="/v1", tags=["rbac_custom_permission"])
# router.include_router(Rbac_menus_router, prefix="/v1", tags=["Rbac_menus"])
# router.include_router(Rbac_modules_router, prefix="/v1", tags=["Rbac_modules"])
# router.include_router(Rbac_permissions_router, prefix="/v1", tags=["Rbac_permissions"])
# router.include_router(Rbac_role_permissions_router, prefix="/v1", tags=["Rbac_role_permissions"])

# repots
# router.include_router(Admission_report_summary_router, prefix="/v1", tags=["Admission_report_summary"])
# router.include_router(Branch_wise_report_router, prefix="/v1", tags=["Branch_wise_report"])
# router.include_router(Cancel_student_list_report_router, prefix="/v1", tags=["Cancel_student_list_report"])
# router.include_router(Category_wise_report_router, prefix="/v1", tags=["Category_wise_report"])
# router.include_router(Consolidate_admission_report_router, prefix="/v1", tags=["Consolidate_admission_report"])
# # router.include_router(Cut_off_rank_report_router, prefix="/v1", tags=["Cut_off_rank_report"])
# router.include_router(Fees_collection_category_wise_report_report_router, prefix="/v1", tags=["Fees_collection_category_wise_report_report"])
# router.include_router(Full_transaction_report_router, prefix="/v1", tags=["Full_transaction_report"])
# # router.include_router(Ioncudos_import_router, prefix="/v1", tags=["Ioncudos_import"])
# router.include_router(Ionems_import_router, prefix="/v1", tags=["Ionems_import"])
# router.include_router(Quota_wise_report_router, prefix="/v1", tags=["Quota_wise_report"])
# # router.include_router(Sales_management_app_report_router, prefix="/v1", tags=["Sales_management_app_report"])
# # router.include_router(Scholarship_refund_report_router, prefix="/v1", tags=["Scholarship_refund_report"])
# router.include_router(School_admission_report_router, prefix="/v1", tags=["School_admission_report"])
# router.include_router(Student_seat_list_report_router, prefix="/v1", tags=["Student_seat_list_report"])
# router.include_router(Student_transaction_report_router, prefix="/v1", tags=["Student_transaction_report"])
# # router.include_router(Students_report_router, prefix="/v1", tags=["Students_report"])
# router.include_router(User_wise_fee_collection_report_router, prefix="/v1", tags=["User_wise_fee_collection_report"])

# seat enquiry
#router.include_router(Student_enquiry_router, prefix="/v1", tags=["Student_enquiry"])

# #seats
# router.include_router(Seats_router, prefix="/v1", tags=["Seats"])

# #students
# router.include_router(Challans_router, prefix="/v1", tags=["Challans"])
# router.include_router(Manage_students_router, prefix="/v1", tags=["Manage_students"])
# router.include_router(Registers_router, prefix="/v1", tags=["Registers"])
# router.include_router(Rename_folders_with_excel_router, prefix="/v1", tags=["Rename_folders_with_excel"])
# router.include_router(Student_generic_refund_router, prefix="/v1", tags=["Student_generic_refund"])
# router.include_router(Student_inquiries_router, prefix="/v1", tags=["Student_inquiries"])
# router.include_router(Student_next_year_admission_router, prefix="/v1", tags=["Student_next_year_admission"])
# router.include_router(Student_parent_profiles_admission_router, prefix="/v1", tags=["Student_parent_profiles_admission"])
# router.include_router(Student_profiles_router, prefix="/v1", tags=["Student_profiles"])
# router.include_router(Student_upload_usn_router, prefix="/v1", tags=["Student_upload_usn"])
# router.include_router(Student_users_router, prefix="/v1", tags=["Student_users"])
# router.include_router(Student_vertical_mobility_router, prefix="/v1", tags=["Student_vertical_mobility"])
# router.include_router(Students_bulk_import_router, prefix="/v1", tags=["Students_bulk_import"])
# router.include_router(Students_router, prefix="/v1", tags=["Students"])


# #masters
# router.include_router(board_or_universities_router, prefix="/v1", tags=["Board or Universities"])
# router.include_router(iems_parent_occupation_masters_router, prefix="/v1", tags=["Iems Parent Occupation Masters"])

# # Transport module
# router.include_router(vehicles.router, prefix="/transport")
# router.include_router(vehicle_routes.router, prefix="/transport")
# router.include_router(employee.router, prefix="/transport")
# router.include_router(employee.static_router)
# router.include_router(tariff.router, prefix="/transport")
# router.include_router(student_route.router, prefix="/transport")
# router.include_router(student_route.static_router)

# include BOARD OF STUDIES (BoS)
router.include_router(
    bos_member_router,
    prefix="/cudos/board-of-studies",
    tags=["Board Of Studies"]
)

# include DELIVERY METHOD
router.include_router(
    delivery_method_router,
    prefix="/cudos/delivery-method",
    tags=["Delivery Method"]
)

#include MAP LEVEL WEIGHTAGE
router.include_router(
    map_level_weightage_router,
    prefix="/cudos/map-level-weightage",
    tags=["Map Level Weightage"]
)

# include PROGRAM OUTCOME
router.include_router(
    program_outcome_router,
    prefix="/program_outcome",
    tags=["Program Outcome"]
)


from app.api.v1.cudo_module.knowledge_profile.api.okp_api import router as okp_router

router.include_router(
    okp_router,
    prefix="/knowledge-profile",
    tags=["Knowledge Profile"]
)


# include GENERIC PROGRAM OUTCOME
router.include_router(
    generic_program_outcome_router,
    prefix="/cudos/generic-program-outcome",
    tags=["Generic Program Outcome"]
)

# include LAB CATEGORY
router.include_router(
    lab_category_router,
    prefix="/cudos/lab-category",
    tags=["Lab Category"]
)

