from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.db.models import IEMSDepartment, IEMProgram, IEMSAcademicBatch, IEMSemester, IEMSCourses
from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException

from ...api.auth import login, register, refresh_token

from ...api.auth import login

from ...api.v1.ems_module.configurations.department import department

from ...api.v1.ems_module.comman_functions import comman_function

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



##LMS(Questionnaire)
from app.api.v1.lms_module.lms_mmp_questionnaire.lms_mmp_questionnaire import (
    router as lms_mmp_questionnaire_router
)

from app.api.v1.lms_module.lms_question_type.lms_question_type import (
    router as lms_question_type_router
)

from app.api.v1.lms_module.lms_questionnaire_type.lms_questionnaire_type import (
    router as lms_questionnaire_type_router
)

from app.api.v1.lms_module.lms_questionnaire_field_setting.lms_questionnaire_field_setting import (
    router as lms_questionnaire_field_setting_router
)

from app.api.v1.lms_module.lms_mentors_group.lms_mentors_group import (
    router as lms_mentors_group_router
)

from app.api.v1.lms_module.lms_mentoring_session.lms_mentoring_session import router as mentoring_session_router

from app.api.v1.lms_module.lms_issues_observations_report.lms_issues_observations_report import router as issues_observations_report_router

from app.api.v1.lms_module.lms_stud_issues_observations_report.lms_stud_issues_observations_report import router as stud_issues_observations_report_router

from app.api.v1.lms_module.lms_stud_mentoring_session.lms_stud_mentoring_session import router as stud_mentoring_session_router

from app.api.v1.lms_module.lms_mmp_report.mmp_report import router as mmp_report_router

from app.api.v1.lms_module.student_course_registration.student_course_registration import router as student_course_registration_router

from app.api.v1.lms_module.config_type import router as config_type_router 
from app.api.v1.lms_module.cross_department_mentor import router as cross_department_mentor_router
from app.api.v1.lms_module.mentor_list import router as mentor_list_router
from app.api.v1.lms_module.mentoring import router as mentoring_router
from app.api.v1.lms_module.student_details import router as student_details_router

router = APIRouter()

# Include auth routes
router.include_router(login.router, prefix="/auth", tags=["auth"])
router.include_router(register.router, prefix="/auth", tags=["auth"])
router.include_router(refresh_token.router, prefix="/auth", tags=["auth"])

# Include routes for registartion module
router.include_router(login.router, prefix="/staff_student_login", tags=["auth"])

# Include routes for comman function  module
router.include_router(comman_function.router, prefix="/comman_function", tags=["auth"])

router.include_router(department.router, prefix="/department", tags=["auth"])

router.include_router(login.router, prefix="/staff_student_login", tags=["Login"])

router.include_router(
    program_mode_router, prefix="/program_mode", tags=["Program Mode"]
)

router.include_router(
    department.router, prefix="/department", tags=["EMS-configuration"]
)

router.include_router(config_type_router, prefix="/config-type", tags=["LMS-Config Type"])
router.include_router(cross_department_mentor_router, prefix="/cross-dept-mentor", tags=["LMS-Cross Department Mentor"])
router.include_router(mentor_list_router, prefix="/mentoring", tags=["LMS-Mentor List"])
router.include_router(mentoring_router, prefix="/mentoring", tags=["LMS-Mentoring"])

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
# router.include_router(
#     bos_member_router,
#     prefix="/cudos/board-of-studies",
#     tags=["Board Of Studies"]
# )

# include DELIVERY METHOD
# router.include_router(
#     delivery_method_router,
#     prefix="/cudos/delivery-method",
#     tags=["Delivery Method"]
# )

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

#LMS Questionnaire
router.include_router(
    lms_mmp_questionnaire_router,
    prefix="/lms_mmp_questionnaire",
    tags=["LMS MMP Questionnaire"]
)

router.include_router(
    lms_question_type_router,
    prefix="/lms_question_type",
    tags=["Question Type"]
)

router.include_router(
    lms_questionnaire_type_router,
    prefix="/lms_questionnaire_type",
    tags=["Questionnaire Type"]
)

router.include_router(
    lms_questionnaire_field_setting_router,
    prefix="/lms_questionnaire_field_setting",
    tags=["Questionnaire Field Setting"]
)

router.include_router(
    lms_mentors_group_router,
    prefix="/lms_mentors_group",
    tags=["LMS Mentors Group"]
)

router.include_router(
    mentoring_session_router,
    prefix="/mentoring-session",
    tags=["Mentoring Session"]
)

router.include_router(
    issues_observations_report_router,
    prefix="/issues_observations_report",
    tags=["Issues & Observations Report"]
)
router.include_router(
    stud_issues_observations_report_router,
    prefix="/stud_issues_observations_report",
    tags=["Student Issues & Observations Report"]
)

router.include_router(
    stud_mentoring_session_router,
    prefix="/student_mentoring",
    tags=["Student Mentoring Session"]
)

router.include_router(
    student_course_registration_router,
    prefix="/student-course-registration",
    tags=["Student Course Registration"]
)

router.include_router(
    mmp_report_router,
    prefix="/mmp-report",
    tags=["MMP Report"]
)

router.include_router(
    student_details_router,
    prefix="/api/v1/student-details",
    tags=["Student Details"]
)