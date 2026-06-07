from sqlalchemy import DECIMAL, Integer, TIMESTAMP, Numeric, PrimaryKeyConstraint, Text, Float, VARBINARY, Column, \
    Integer, SmallInteger, String, Date, ForeignKey, Boolean, CHAR, DateTime, Time, text, Enum, BigInteger
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import MEDIUMINT, TINYINT, YEAR

from datetime import datetime
from sqlalchemy.sql import func
import enum

from app.core.database import Base
# Base = declarative_base()

# Ensure PO Type model is imported so its table (`cudos_po_type`) is registered
from app.api.v1.cudo_module.program_outcome.model.po_type_model import PoType  # noqa: F401

# Fix SQLAlchemy mapper: Import CudosMapCourseToCourseInstructor early for IEMSCourses relationship
# noqa: F401


class OrgMainOccasionType(Base):
    __tablename__ = 'cudos_org_main_occasion_type'

    mot_id = Column(Integer, primary_key=True, autoincrement=True)
    mot_name = Column(String(150), nullable=False, unique=True)
    mot_description = Column(String(500), nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)


class OrgSubOccasionType(Base):
    __tablename__ = 'cudos_org_sub_occasion_type'

    sot_id = Column(Integer, primary_key=True, autoincrement=True)
    mot_id = Column(Integer, ForeignKey('cudos_org_main_occasion_type.mot_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    sot_name = Column(String(150), nullable=False)
    sot_description = Column(String(500), nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)


class Caste(Base):
    __tablename__ = 'caste'

    caste_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    status = Column(Boolean, default=True)


class City(Base):
    __tablename__ = 'city'

    city_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    state_id = Column(Integer, nullable=True)
    status = Column(Boolean, default=True)


class ClassTiming(Base):
    __tablename__ = 'class_timing'

    id = Column(Integer, primary_key=True, autoincrement=False)
    class_timing_name = Column(String(100), nullable=False, default='0')
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    is_break = Column(Integer, default=0)
    order_by = Column(String(3), nullable=False)
    period_name = Column(String(45), nullable=True)


class Country(Base):
    __tablename__ = 'country'

    country_id = Column(Integer, primary_key=True, autoincrement=False)
    sortname = Column(String(50), nullable=True)
    name = Column(String(100), nullable=True)


class FacultyTimeTable(Base):
    __tablename__ = 'faculty_time_table'

    id = Column(Integer, primary_key=True, autoincrement=False)
    faculty_id = Column(Integer, nullable=False)
    tt_id = Column(Integer, nullable=False)
    sem_time_table_id = Column(Integer, nullable=False)
    crs_code = Column(String(45), nullable=False)
    crs_id = Column(Integer, nullable=True)
    lab_course_batch_id = Column(Integer, nullable=True)


class IEMSAcademicBatch(Base):
    __tablename__ = 'iems_academic_batch'

    academic_batch_id = Column(Integer, primary_key=True, autoincrement=True)
    academic_batch_code = Column(String(25), nullable=False)
    academic_batch_desc = Column(String(255), nullable=False)
    academic_year = Column(String(45), nullable=True)
    regulation_year = Column(String(45), nullable=True)
    program_duration = Column(Integer, nullable=True)
    dept_id = Column(Integer, ForeignKey('iems_department.dept_id'), nullable=False)
    pgm_id = Column(Integer, ForeignKey('iems_program.pgm_id'), nullable=False)
    org_id = Column(Integer, nullable=True)
    total_credits = Column(Integer, default=0)
    lateral_entry_credits = Column(Integer, default=0)
    status = Column(Integer, nullable=False)
    created_by = Column(Integer, nullable=False)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    grade_type = Column(String(100), nullable=True)
    is_tw_course = Column(Integer, default=0)
    # missing data added
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    total_terms = Column(Integer, nullable=False)
    academic_batch_owner = Column(Integer, ForeignKey('iems_users.id'), nullable=False)

    cia_passing_marks = Column(Float, default=0)
    tee_passing_marks = Column(Float, default=0)

    import_ref_crclm_id = Column(Integer)
    import_type = Column(Integer)

    #ADD RELATIONSHIPS
    program = relationship("IEMProgram", foreign_keys=[pgm_id], backref="academic_batches")
    owner = relationship("IEMSUsers", foreign_keys=[academic_batch_owner])
    department = relationship("IEMSDepartment", foreign_keys=[dept_id])



class IEMSActivityStatusMgmt(Base):
    __tablename__ = 'iems_activity_status_mgmt'

    id = Column(Integer, primary_key=True, autoincrement=False)
    academic_batch_id = Column(String(45), nullable=False)
    hall_ticket_status = Column(Boolean, default=False)
    hall_ticket_download_count = Column(Integer, default=0)


class IEMSAdmissionQuota(Base):
    __tablename__ = 'iems_admission_quota'

    id = Column(Integer, primary_key=True, autoincrement=False)
    admission_quota_type = Column(String(45), nullable=True)
    status = Column(Integer, nullable=True)


class IEMSAdmissionSubType(Base):
    __tablename__ = 'iems_admission_sub_type'

    id = Column(Integer, primary_key=True, autoincrement=False)
    admission_sub_type = Column(String(45), nullable=True)
    status = Column(Integer, nullable=True)


class IEMSAdmissionType(Base):
    __tablename__ = 'iems_admission_type'

    admission_type_id = Column(Integer, primary_key=True, autoincrement=False)
    admission_type = Column(String(45), nullable=True)
    status = Column(Integer, nullable=True)
    org_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMSAppAttendanceStatus(Base):
    __tablename__ = 'iems_app_attedance_status'

    id = Column(Integer, primary_key=True, autoincrement=False)
    crs_code = Column(String(45), nullable=False)
    class_time = Column(String(45), nullable=False)
    section = Column(String(5), nullable=False)
    batch_id = Column(Integer, nullable=False)
    posted_date = Column(DateTime, default=datetime.utcnow)


class IEMSAppConfigs(Base):
    __tablename__ = 'iems_app_configs'

    id = Column(Integer, primary_key=True, autoincrement=False)
    config_type = Column(String(45), nullable=False)
    description = Column(Text, nullable=False)
    value = Column(String(100), nullable=False)
    org_id = Column(Integer, nullable=True)
    program_id = Column(Integer, nullable=True)


class IEMSAppSmsTable(Base):
    __tablename__ = 'iems_app_sms_table'

    id = Column(Integer, primary_key=True, autoincrement=False)
    message = Column(Text, nullable=False)
    send_to = Column(String(15), nullable=False)
    sms_date = Column(Date, nullable=False)


class IEMSAppVersion(Base):
    __tablename__ = 'iems_app_version'

    id = Column(Integer, primary_key=True, autoincrement=False)
    version_code = Column(Integer, nullable=True)
    version_name = Column(String(11), nullable=True)
    version_description = Column(String(500), nullable=True)
    app_name_id = Column(Integer, nullable=True)
    force_update = Column(Integer, nullable=True)
    file_path = Column(String(200), nullable=True)


# class AssessmentOccasions(Base):
#     __tablename__ = 'assessment_occasions'

#     ao_id = Column(Integer, primary_key=True, autoincrement=True)
#     ao_name = Column(String(100), nullable=True)
#     ao_description = Column(String(500), nullable=True)
#     academic_batch_id = Column(Integer, nullable=True)
#     semester_id = Column(Integer, nullable=True)
#     created_by = Column(Integer, nullable=True)
#     created_date = Column(Date, nullable=True)


class IEMSAssessmentOccasions(Base):
    __tablename__ = 'iems_assessment_occasions'

    ao_id = Column(Integer, primary_key=True, autoincrement=True)
    mte_flag = Column(Boolean, nullable=True, default=False)
    qpd_id = Column(Integer, nullable=True)
    cia_occasion_type_id = Column(Integer, ForeignKey('iems_cia_occasion_type.cia_occasion_type_id'), nullable=True)
    ise_mse_type_id = Column(Integer, ForeignKey('iems_ise_mse_type.ise_mse_type_id'), nullable=True, default=None)
    cia_occasion = Column(String(15), nullable=False)
    ao_sl_no = Column(String(100), nullable=False)
    ao_name = Column(String(2000), nullable=False)
    ao_method_id = Column(Integer, nullable=False, default=0)
    ao_type_id = Column(Integer, nullable=False, default=0)
    max_marks = Column(Integer, nullable=False)
    avg_cia_marks = Column(Float, nullable=True)
    min_marks = Column(Integer, nullable=False, default=0)
    crs_code = Column(String(15), nullable=False)
    weightage = Column(String(45), nullable=False)
    bestof = Column(Boolean, nullable=False, default=False)
    result_year = Column(Date, nullable=True)
    cia_master_id = Column(Integer, nullable=True)
    cia_map_id = Column(Integer, nullable=True)
    org_id = Column(Integer, nullable=False, default=1)
    status = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, nullable=False, default=1)
    modified_by = Column(Integer, nullable=False, default=1)
    create_date = Column(DateTime, nullable=False, default=datetime.now)
    modify_date = Column(DateTime, nullable=False, default=datetime.now)
    academic_batch_id = Column(Integer, nullable=False, default=0)
    semester_id = Column(Integer, nullable=False, default=0)
    crs_id = Column(Integer, nullable=False, default=0)
    section_id = Column(Integer, nullable=True)
    rubrics_qp_status = Column(Boolean, nullable=True)
    import_ref_ao_id = Column(Integer, nullable=True)
    direct_method = Column(Integer, nullable=False, default=1)
    co_indirect_weightage = Column(Integer, nullable=True)
    cmot_id = Column(Integer, nullable=True)
    sot_id = Column(Integer, nullable=True)
    

class IEMSAttendanceTable(Base):
    __tablename__ = 'iems_attandance_table'

    aid = Column(Integer, primary_key=True, autoincrement=False)
    regno = Column(String(20), nullable=True)
    crs_code = Column(String(25), nullable=True)
    attendance_date = Column(DateTime, nullable=True)
    sessions = Column(SmallInteger, nullable=True)
    a_status = Column(String(2), nullable=True)
    other_reason = Column(Boolean, default=False)
    org_id = Column(Integer, nullable=False)
    sem_time_table_id = Column(Integer, nullable=False)


class IEMSAttendanceDvsIntegration(Base):
    __tablename__ = 'iems_attendance_dvs_integration'

    integration_id = Column(Integer, primary_key=True, autoincrement=False)
    std_crs_id = Column(Integer, nullable=True)
    regno = Column(String(45), nullable=True)
    usno = Column(String(20), nullable=True)
    student_name = Column(String(150), nullable=True)
    org_id = Column(Integer, nullable=True)
    org_name = Column(String(500), nullable=True)
    dept_id = Column(Integer, nullable=True)
    dept_name = Column(String(100), nullable=True)
    program_id = Column(Integer, nullable=True)
    program_name = Column(String(100), nullable=True)
    batch_id = Column(Integer, nullable=True)
    batch_name = Column(String(50), nullable=True)
    semester = Column(Integer, nullable=True)
    ems_crs_code = Column(String(15), nullable=True)
    dvs_crs_code = Column(String(20), nullable=True)
    result_year = Column(Date, nullable=False)
    event_type = Column(String(45), nullable=True)
    is_see_attendance_finalized = Column(Boolean, default=False)
    is_dvs_attendance_synced = Column(Boolean, default=False)
    is_reval = Column(Boolean, default=False)
    is_reval_registration_finalised = Column(Boolean, default=True)
    is_mal_practice = Column(Boolean, default=False)
    see_absentee = Column(Boolean, default=True)
    status = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    modified_by = Column(Integer, nullable=True)
    modified_at = Column(DateTime, nullable=True)


class IEMSBacklogCourseMap(Base):
    __tablename__ = 'iems_backlog_course_map'

    backlog_map_id = Column(Integer, primary_key=True, autoincrement=False)
    crs_code = Column(String(45), nullable=False)
    map_crs_code = Column(String(45), nullable=False)
    program_id = Column(Integer, nullable=True)
    batch_cycle_id = Column(Integer, nullable=True)
    semester = Column(Integer, nullable=True)
    org_id = Column(SmallInteger, nullable=False)
    result_year = Column(String(45), nullable=False)


class IEMSBatchCycle(Base):
    __tablename__ = 'iems_batch_cycle'

    batch_cycle_id = Column(Integer, primary_key=True, autoincrement=False)
    batch_cycle_code = Column(String(45), nullable=True)
    batch_cycle_desc = Column(String(45), nullable=True)
    status = Column(Integer, nullable=True)
    org_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMSBranchMst(Base):
    __tablename__ = 'iems_branch_mst'

    name = Column(String(10), primary_key=True, nullable=False)
    full_name = Column(String(100), nullable=False)


class IEMSBulkStudentDetails(Base):
    __tablename__ = 'iems_bulk_student_details'

    id = Column(Integer, primary_key=True, autoincrement=False)
    Remarks = Column(Text, nullable=True)
    student_admission_id = Column(String(50), nullable=True)
    application_no = Column(String(50), nullable=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True)
    dob = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    email = Column(String(50), nullable=True)
    mother_tongue = Column(String(50), nullable=True)
    blood_group = Column(String(50), nullable=True)
    birth_place = Column(String(50), nullable=True)
    nationality = Column(String(50), nullable=True)
    religion = Column(String(50), nullable=True)
    caste = Column(String(50), nullable=True)
    emergency_person = Column(String(50), nullable=True)
    emergency_phone = Column(String(50), nullable=True)
    profile_image = Column(String(50), nullable=True)
    doj = Column(String(50), nullable=True)
    quota_type = Column(String(50), nullable=True)
    cet_comedk_no = Column(String(50), nullable=True)
    cet_comedk_rank = Column(String(50), nullable=True)
    batch_cycle_id = Column(String(50), nullable=True)
    usno = Column(String(50), nullable=True)
    rural_urban = Column(String(50), nullable=True)
    claimed_category = Column(String(50), nullable=True)
    allocated_category = Column(String(50), nullable=True)
    hostel = Column(String(50), nullable=True)
    transport = Column(String(50), nullable=True)
    father_name = Column(String(50), nullable=True)
    fathers_occupation = Column(String(50), nullable=True)
    fathers_income = Column(String(50), nullable=True)
    fathers_phone = Column(String(50), nullable=True)
    fathers_email = Column(String(50), nullable=True)
    mother_name = Column(String(50), nullable=True)
    mothers_occupation = Column(String(50), nullable=True)
    mothers_income = Column(String(50), nullable=True)
    mothers_phone = Column(String(50), nullable=True)
    mothers_email = Column(String(50), nullable=True)
    guardian_name = Column(String(50), nullable=True)
    guardian_occupation = Column(String(50), nullable=True)
    guardian_income = Column(String(50), nullable=True)
    guardian_phone = Column(String(50), nullable=True)
    guardian_email = Column(String(50), nullable=True)
    sslc_board_university = Column(String(50), nullable=True)
    sslc_institution = Column(String(50), nullable=True)
    sslc_prev_regno = Column(String(50), nullable=True)
    sslc_total_marks = Column(String(50), nullable=True)
    sslc_marks_obtained = Column(String(50), nullable=True)
    sslc_percentage = Column(String(50), nullable=True)
    sslc_grade = Column(String(50), nullable=True)
    sslc_year_of_passing = Column(String(50), nullable=True)
    sslc_place_of_study = Column(String(50), nullable=True)
    sslc_state = Column(String(50), nullable=True)
    pu_board_university = Column(String(50), nullable=True)
    pu_institution = Column(String(50), nullable=True)
    pu_prev_regno = Column(String(50), nullable=True)
    pu_total_marks = Column(String(50), nullable=True)
    pu_marks_obtained = Column(String(50), nullable=True)
    pu_percentage = Column(String(50), nullable=True)
    pu_grade = Column(String(50), nullable=True)
    pu_year_of_passing = Column(String(50), nullable=True)
    pu_place_of_study = Column(String(50), nullable=True)
    pu_state = Column(String(50), nullable=True)
    dip_board_university = Column(String(50), nullable=True)
    dip_institution = Column(String(50), nullable=True)
    dip_prev_regno = Column(String(50), nullable=True)
    dip_total_marks = Column(String(50), nullable=True)
    dip_marks_obtained = Column(String(50), nullable=True)
    dip_percentage = Column(String(50), nullable=True)
    dip_grade = Column(String(50), nullable=True)
    dip_year_of_passing = Column(String(50), nullable=True)
    dip_place_of_study = Column(String(50), nullable=True)
    dip_state = Column(String(50), nullable=True)
    degree_board_university = Column(String(50), nullable=True)
    degree_institution = Column(String(50), nullable=True)
    degree_prev_regno = Column(String(50), nullable=True)
    degree_total_marks = Column(String(50), nullable=True)
    degree_marks_obtained = Column(String(50), nullable=True)
    degree_percentage = Column(String(50), nullable=True)
    degree_grade = Column(String(50), nullable=True)
    degree_year_of_passing = Column(String(50), nullable=True)
    degree_place_of_study = Column(String(50), nullable=True)
    degree_state = Column(String(50), nullable=True)
    permanent_address1 = Column(String(50), nullable=True)
    permanent_city = Column(String(50), nullable=True)
    permanent_state = Column(String(50), nullable=True)
    permanent_country = Column(String(50), nullable=True)
    pincode = Column(String(50), nullable=True)
    permanent_phone = Column(String(50), nullable=True)
    correspondance_address = Column(String(50), nullable=True)
    correspondance_city = Column(String(50), nullable=True)
    correspondance_state = Column(String(50), nullable=True)
    correspondance_country = Column(String(50), nullable=True)
    correspondance_pincode = Column(String(50), nullable=True)
    correspondance_phone = Column(String(50), nullable=True)
    guardian_address = Column(String(50), nullable=True)
    guardian_city = Column(String(50), nullable=True)
    guardian_district = Column(String(50), nullable=True)
    guardian_state = Column(String(50), nullable=True)
    guardian_country = Column(String(50), nullable=True)
    guardian_pincode = Column(String(50), nullable=True)
    guardian_a_phone = Column(String(50), nullable=True)
    roll_no = Column(String(45), nullable=True)
    reg_no = Column(String(45), nullable=True)
    section = Column(String(45), nullable=True)
    is_physically_challenged = Column(SmallInteger, nullable=True)
    pc_description_id = Column(Integer, nullable=True)
    permanent_address2 = Column(String(100), nullable=True)
    permanent_landmark = Column(String(100), nullable=True)
    permanent_street = Column(String(100), nullable=True)
    correspondance_address2 = Column(String(100), nullable=True)
    correspondance_street = Column(String(100), nullable=True)
    correspondance_landmark = Column(String(100), nullable=True)


class IEMSCategoryTypeMaster(Base):
    __tablename__ = 'iems_category_type_master'

    category_id = Column(Integer, primary_key=True, autoincrement=False)
    category_code = Column(String(45), nullable=False)
    category_desc = Column(String(45), nullable=False)
    status = Column(String(45), default='1')


class IEMSCertificateTypeMaster(Base):
    __tablename__ = 'iems_certificate_type_master'

    certificate_type_master_id = Column(Integer, primary_key=True, autoincrement=False)
    certificate_code = Column(String(45), nullable=True)
    certificate_description = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=True)
    status = Column(Boolean, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMSCGPA(Base):
    __tablename__ = 'iems_cgpa'

    id = Column(Integer, primary_key=True, autoincrement=False)
    regno = Column(String(45), nullable=False)
    program_id = Column(Integer, nullable=False)
    cgpa = Column(Float, nullable=True)
    result_year = Column(Date, nullable=False)
    org_id = Column(Integer, nullable=False)


class IEMSCGPABackup(Base):
    __tablename__ = 'iems_cgpa_bck'

    id = Column(Integer, primary_key=True, autoincrement=False)
    regno = Column(String(45), nullable=False)
    program_id = Column(Integer, nullable=False)
    cgpa = Column(Float, nullable=True)
    result_year = Column(Date, nullable=False)
    org_id = Column(Integer, nullable=False)


class IEMSCGPAug(Base):
    __tablename__ = 'iems_cgpa_ug'

    pky = Column(Integer, primary_key=True, autoincrement=False)
    sl_no = Column(Integer, nullable=True)
    usno = Column(String(15), nullable=True)
    s_name = Column(String(50), nullable=True)
    test1 = Column(Integer, nullable=True)
    quiz1 = Column(Integer, nullable=True)
    test2 = Column(Integer, nullable=True)
    quiz2 = Column(Integer, nullable=True)
    test3 = Column(Integer, nullable=True)
    quiz3 = Column(Integer, nullable=True)
    tavg = Column(Integer, nullable=True)
    qavg = Column(Integer, nullable=True)
    asn = Column(Integer, nullable=True)
    cie = Column(Integer, nullable=True)
    see = Column(Integer, nullable=True)
    cie_see = Column(Integer, nullable=True)
    grd = Column(String(3), nullable=True)
    subcode = Column(String(15), nullable=True)
    sect = Column(String(3), nullable=True)
    bcde = Column(Integer, nullable=True)
    brcode = Column(String(5), nullable=True)
    crta = Column(Integer, nullable=True)
    crte = Column(Integer, nullable=True)
    crt = Column(Integer, nullable=True)
    sgpa = Column(DECIMAL(4, 2), nullable=True)
    cgpa = Column(DECIMAL(4, 2), nullable=True)
    semester = Column(Integer, nullable=True)
    academic_year = Column(Date, nullable=True)
    grdpt = Column(DECIMAL(3, 1), nullable=True)
    crtearned = Column(DECIMAL(5, 2), nullable=True)
    crtactual = Column(DECIMAL(5, 2), nullable=True)
    cigi = Column(DECIMAL(5, 2), nullable=True)
    ci = Column(DECIMAL(5, 2), nullable=True)
    see_cie_noncredit = Column(String(2), nullable=True)
    pgcode = Column(String(4), nullable=True)
    col_code = Column(String(6), nullable=True)
    phy_cyc = Column(String(1), nullable=True)
    mkup_flg = Column(String(2), nullable=True)
    grdptd = Column(DECIMAL(4, 1), nullable=True)
    normal_grace = Column(String(3), nullable=True)
    mkup_grace = Column(String(2), nullable=True)
    reval2_flg = Column(Boolean, nullable=True)
    reval3_flg = Column(Boolean, nullable=True)
    malpractice_flg = Column(Boolean, nullable=True)
    lock_cie = Column(Boolean, nullable=True)
    lock_see = Column(Boolean, nullable=True)
    lock_grd = Column(Boolean, nullable=True)
    att_elg = Column(Boolean, nullable=True)
    cie_elg = Column(Boolean, nullable=True)
    suborder = Column(Boolean, nullable=True)
    userid = Column(String(25), nullable=True)
    prm_det = Column(Boolean, nullable=True)
    lab_flag = Column(Boolean, nullable=True)
    lab_grp = Column(String(3), nullable=True)
    see1 = Column(DECIMAL(5, 2), nullable=True)
    see2 = Column(DECIMAL(5, 2), nullable=True)
    see3 = Column(DECIMAL(5, 2), nullable=True)
    packet_code = Column(String(25), nullable=True)
    pack_sel = Column(Boolean, nullable=True)
    reexamyear = Column(Date, nullable=True)
    cie_see_grace = Column(DECIMAL(5, 2), nullable=True)
    grd_grace = Column(String(3), nullable=True)
    seemkup1 = Column(DECIMAL(5, 2), nullable=True)
    seemkup_grace = Column(DECIMAL(5, 2), nullable=True)
    cie_see_mkup_grace = Column(DECIMAL(5, 2), nullable=True)
    cie_see_mkup = Column(DECIMAL(5, 2), nullable=True)
    grd_mkup = Column(String(3), nullable=True)
    grdpt_mkup = Column(DECIMAL(3, 1), nullable=True)
    crtearned_mkup = Column(DECIMAL(2, 1), nullable=True)
    grd_mkup_grace = Column(String(3), nullable=True)
    grdpt_mkup_grace = Column(DECIMAL(3, 1), nullable=True)
    seelab = Column(DECIMAL(5, 2), nullable=True)
    ntotal = Column(DECIMAL(5, 2), nullable=True)
    ngrd = Column(String(3), nullable=True)
    emkup_flg = Column(String(2), nullable=True)
    cmts = Column(String(30), nullable=True)
    seemkup1e = Column(DECIMAL(5, 2), nullable=True)
    grd_mkupe = Column(String(3), nullable=True)
    grdpt_mkupe = Column(Integer, nullable=True)
    crtearned_mkupe = Column(DECIMAL(2, 1), nullable=True)
    rtype = Column(Integer, nullable=True)
    result_year = Column(Date, nullable=True)
    see50 = Column(DECIMAL(5, 2), nullable=True)
    exam_period = Column(String(30), nullable=True)
    exam_date = Column(Date, nullable=True)
    exam_type = Column(String(6), nullable=True)
    father_name = Column(String(100), nullable=True)
    stype = Column(String(1), nullable=True)
    attempt = Column(Integer, nullable=True)
    batch = Column(String(4), nullable=True)
    gcno = Column(String(6), nullable=True)
    st_pict = Column(String(255), nullable=True)
    reg_yn = Column(Boolean, nullable=True)
    chg_br = Column(Boolean, nullable=True)
    oldusno = Column(String(10), nullable=True)
    fatname = Column(String(50), nullable=True)
    rereg = Column(String(3), nullable=True)
    backlog_yn = Column(Boolean, nullable=True)
    sem_class = Column(String(20), nullable=True)
    ett = Column(Integer, nullable=True)
    attper = Column(DECIMAL(5, 2), nullable=True)
    lattper = Column(DECIMAL(5, 2), nullable=True)
    dob = Column(Date, nullable=True)
    fname = Column(String(150), nullable=True)
    mname = Column(String(150), nullable=True)
    sex = Column(String(2), nullable=True)
    st_caste = Column(String(50), nullable=True)
    see_min = Column(DECIMAL(5, 2), nullable=True)
    v2 = Column(DECIMAL(5, 2), nullable=True)
    v3 = Column(DECIMAL(5, 2), nullable=True)
    v1 = Column(DECIMAL(5, 2), nullable=True)
    see4 = Column(DECIMAL(5, 2), nullable=True)
    attempt_flg = Column(DECIMAL(5, 2), nullable=True)


class IEMSChangeMonitor(Base):
    __tablename__ = 'iems_change_monitor'

    change_monitor_id = Column(Integer, primary_key=True, autoincrement=False)
    monitor_type = Column(String(50), nullable=False)
    usno = Column(String(50), nullable=False)
    exam_id = Column(Integer, nullable=True)
    change_occuring_time = Column(DateTime, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
    view_status = Column(Integer, default=0)


class IEMSCIAExamMapping(Base):
    __tablename__ = 'iems_cia_exam_mapping'

    cia_map_id = Column(Integer, primary_key=True, autoincrement=False)
    result_year = Column(Date, nullable=True)
    cia_master_id = Column(Integer, nullable=False)
    cia_master_name = Column(String(45), nullable=True)
    batch_id = Column(Integer, nullable=False)
    pgm_id = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    org_id = Column(Integer, nullable=True)
    status = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)


class IEMSCIAExamMaster(Base):
    __tablename__ = 'iems_cia_exam_master'

    id = Column(Integer, primary_key=True, autoincrement=False)
    result_year = Column(Date, nullable=True)
    cia_master_name = Column(String(45), nullable=False)
    cia_master_des = Column(String(45), nullable=True)
    cia_max_marks = Column(Float, nullable=False, default=0)
    cia_min_marks = Column(Float, nullable=False, default=0)
    cia_weightage = Column(Integer, nullable=True)  # tinyint(3) UNSIGNED
    exam_start_date = Column(Date, nullable=True)
    exam_end_date = Column(Date, nullable=True)
    org_id = Column(Integer, nullable=True)  # UNSIGNED
    status = Column(Integer, nullable=True)  # mediumint(8)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMSCIOccasionType(Base):
    __tablename__ = 'iems_cia_occasion_type'

    cia_occasion_type_id = Column(Integer, primary_key=True, autoincrement=True)
    cia_occasion_type_code = Column(String(45), nullable=True)
    cia_occasion_type_desc = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=True)  # UNSIGNED
    status = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMSCIAStudentCourses(Base):
    __tablename__ = 'iems_cia_student_courses'

    id = Column(Integer, primary_key=True, autoincrement=False)
    crs_code = Column(String(45), nullable=False)
    occasion_id = Column(Integer, nullable=True)  # UNSIGNED
    cia_master_id = Column(Integer, nullable=True)  # UNSIGNED
    result_year = Column(Date, nullable=False)
    regno = Column(String(45), nullable=False)
    secured_marks = Column(Float, nullable=True)
    is_bestof = Column(Boolean, nullable=True)  # tinyint(1) UNSIGNED
    compute_cia = Column(Float, nullable=True)
    std_crs_id = Column(Integer, nullable=False)
    is_absentee = Column(Boolean, default=False)  # tinyint(3) UNSIGNED
    is_approved = Column(Integer, nullable=True)
    is_eligibility = Column(Integer, nullable=True)


class IEMSClassTimings(Base):
    __tablename__ = 'iems_class_timings'

    class_timing_id = Column(Integer, primary_key=True, autoincrement=False)
    timing_set_id = Column(Integer, nullable=True)  # UNSIGNED
    period_id = Column(Integer, nullable=True)  # mediumint(8) UNSIGNED
    start_time = Column(String(45), nullable=True)
    end_time = Column(String(45), nullable=True)
    break_duration = Column(String(45), nullable=True)  # renamed for clarity
    created_at = Column(DateTime, nullable=True)
    modified_at = Column(DateTime, nullable=True)


class IEMSClassTimingSet(Base):
    __tablename__ = 'iems_class_timing_set'

    timing_set_id = Column(Integer, primary_key=True, autoincrement=False)
    timing_set_name = Column(String(450), nullable=True)
    period_count = Column(Integer, default=0)  # mediumint(8)
    default_period = Column(Boolean, nullable=True)  # tinyint(1)
    description = Column(String(4500), nullable=True)
    org_id = Column(Integer, nullable=True)  # UNSIGNED
    created_at = Column(DateTime, nullable=True)
    modified_at = Column(DateTime, nullable=True)


class IEMSCollegeDet(Base):
    __tablename__ = 'iems_college_det'

    id = Column(Integer, primary_key=True, autoincrement=False)
    collname = Column(String(3000), nullable=False)
    add1 = Column(String(3000), nullable=False)
    add2 = Column(String(3000), nullable=False)


class IEMSCombineCourse(Base):
    __tablename__ = 'iems_combine_course'

    combine_id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED
    crs_id = Column(Integer, nullable=False)  # UNSIGNED
    combine_crs_id = Column(Integer, nullable=False)  # UNSIGNED
    org_id = Column(Integer, nullable=False)  # UNSIGNED


class IEMSConsolidatedSGPACGPA(Base):
    __tablename__ = 'iems_consolidated_sgpa_cgpa'

    id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED
    regno = Column(String(45), nullable=False)
    usno = Column(String(45), nullable=False)
    program_id = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    sgpa = Column(Float, nullable=False)
    cgpa = Column(Float, nullable=False)
    org_id = Column(Integer, nullable=False)


class IEMSCourses(Base):
    __tablename__ = 'iems_courses'

    crs_id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED
    crs_code = Column(String(15), nullable=False)
    crs_event_type = Column(Integer, nullable=True)
    base_crs_code = Column(String(15), nullable=True)
    see_weightage = Column(Integer, default=0)  # tinyint(3) UNSIGNED
    cia_weightage = Column(Integer, default=0)  # tinyint(3) UNSIGNED
    viva_min_marks = Column(Float, default=0)
    viva_max_marks = Column(Float, default=0)
    viva_weightage = Column(Integer, default=0)  # tinyint(3) UNSIGNED
    tw_max_marks = Column(Float, default=0)
    tw_min_marks = Column(Float, default=0)
    tw_weightage = Column(Integer, default=0)  # tinyint(3) UNSIGNED
    tw_credit_hours = Column(Float, nullable=True)
    ise_min_marks = Column(Float, nullable=True)
    ise_max_marks = Column(Float, nullable=True)
    ise_weightage = Column(Float, nullable=True)
    mse_min_marks = Column(Float, nullable=True)
    mse_max_marks = Column(Float, nullable=True)
    mse_weightage = Column(Float, nullable=True)
    academic_year = Column(String(4), nullable=False)
    crs_title = Column(String(255), nullable=True)
    department_id = Column(Integer, nullable=True)  # UNSIGNED
    program_id = Column(Integer, ForeignKey('iems_program.pgm_id'))  # UNSIGNED
    academic_batch_id = Column(Integer, nullable=False)
    course_type_id = Column(Integer, nullable=False)  # UNSIGNED
    batch_cycle_id = Column(Integer, default=3)  # UNSIGNED
    result_year = Column(Date, nullable=True)
    credit_based = Column(Integer, nullable=False)  # UNSIGNED
    credit_hours = Column(Float, nullable=True)
    semester = Column(Integer, nullable=True)  # UNSIGNED
    lab_course = Column(String(1), nullable=False, default='0')
    crs_type = Column(String(1), nullable=True)
    crs_order = Column(Integer, nullable=False)  # UNSIGNED
    no_of_cia = Column(Integer, nullable=False)  # UNSIGNED
    no_of_ise = Column(Float, nullable=True)
    no_of_mse = Column(Float, nullable=True)
    cia_max_marks = Column(Float, nullable=False, default=0)
    cia_min_marks = Column(Float, nullable=False, default=0)
    see_max_marks = Column(Float, nullable=False, default=0)
    see_min_marks = Column(Float, nullable=False, default=0)
    cia_see_min_marks = Column(Float, default=0)
    total_classes = Column(Float, nullable=False, default=0)
    min_passing_marks = Column(Float, nullable=False, default=0)
    org_id = Column(Integer, nullable=True)  # UNSIGNED
    status = Column(Integer, nullable=True)  # mediumint(8)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    # -------------------- NEW FIELDS --------------------

    hm_crs_branch_id = Column(Integer, nullable=True)  # new field

    crs_mode = Column(Integer, nullable=False, default=0)  # new field
    crs_acronym = Column(String(30), nullable=True)  # new field
    crs_domain_id = Column(Integer, nullable=True)  # new field

    lect_credits = Column(Float, nullable=True)  # new field
    tutorial_credits = Column(Float, nullable=True)  # new field
    practical_credits = Column(Float, nullable=True)  # new field
    self_study_credits = Column(Float, nullable=True)  # new field
    total_credits = Column(Float, nullable=True)  # new field

    cia_flag = Column(Integer, default=0)  # new field
    mte_flag = Column(Integer, default=0)  # new field
    tee_flag = Column(Integer, default=0)  # new field
    mte_weightage = Column(Float, default=0.00)  # new field

    contact_hours = Column(Float, nullable=True)  # new field
    mid_term_marks = Column(Float, nullable=True)  # new field
    attendance_marks = Column(Float, default=0)  # new field
    ss_marks = Column(Float, default=0)  # new field
    total_marks = Column(Float, nullable=True)  # new field
    see_duration = Column(String(4), nullable=True)  # new field

    cognitive_domain_flag = Column(Integer, nullable=True)  # new field
    affective_domain_flag = Column(Integer, nullable=True)  # new field
    psychomotor_domain_flag = Column(Integer, nullable=True)  # new field

    state_id = Column(Integer, default=1)  # new field
    topic_publish_flag = Column(Integer, default=0)  # new field
    target_status = Column(Integer, default=1)  # new field
    target_comment = Column(Text, nullable=True)  # new field

    cia_course_minthreshhold = Column(Integer, nullable=True)  # new field
    mte_course_minthreshhold = Column(Integer, nullable=True)  # new field
    tee_course_minthreshhold = Column(Integer, nullable=True)  # new field
    course_studentthreshhold = Column(Integer, nullable=True)  # new field
    justify = Column(String(1000), nullable=True)  # new field

    clo_bl_flag = Column(Integer, nullable=False, default=0)  # new field
    edu_sys_flag = Column(Integer, default=0)  # new field
    total_stud_enroll = Column(Integer, nullable=True)  # new field
    reg_start_date = Column(DateTime, nullable=True)  # new field
    reg_end_date = Column(DateTime, nullable=True)  # new field

    crs_attainment_finalize_flag = Column(Integer, nullable=False, default=0)  # new field
    crs_stud_reg_flag = Column(Integer, nullable=False, default=0)  # new field
    sec_stud_reg_flag = Column(Integer, nullable=False, default=0)  # new field
    crs_mte_finalize_flag = Column(Integer, nullable=False, default=0)  # new field

    import_ref_crs_id = Column(Integer, nullable=True)  # new field
    elective_crs_flag = Column(Integer, default=0)  # new field
    co_attainment_observation = Column(Text, nullable=True)  # new field
    co_attainment_action_plan = Column(Text, nullable=True)  # new field
    co_attainment_hod_remarks = Column(Text, nullable=True)  # new field
    crs_bl_sugg_flag = Column(Integer, nullable=False, default=1)  # new field

    cia_course_target = Column(Integer, nullable=True)  # new field
    mte_course_target = Column(Integer, nullable=True)  # new field
    tee_course_target = Column(Integer, nullable=True)  # new field

    tutorial = Column(Integer, default=0)  # new field
    indirect_flag = Column(Integer, nullable=False, default=0)  # new field
    direct_percentage = Column(Integer, nullable=True)  # new field
    indirect_percentage = Column(Integer, nullable=True)  # new field
    avg_flag = Column(Integer, default=0)  # new field

    lms_topic_import_type_flag = Column(Integer, default=1)  # new field
    finalize_and_ready_for_ems_flag = Column(Integer, default=0)  # new field
    crs_assessment_flag = Column(Integer, default=0)  # new field
    lms_crs_attendance_finalize = Column(Integer, default=0)  # new field
    crs_ovrl_cia_finalise_flag = Column(Integer, default=0)  # new field

    # Course-Instructor Mapping
    instructors = relationship("CudosMapCoursetoCourseInstructor", back_populates="course")


class IEMSCourseMappingTable(Base):
    __tablename__ = 'iems_course_mapping_table'

    mapping_id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED
    org_id = Column(Integer, nullable=False)  # UNSIGNED
    org_name = Column(String(500), nullable=True)
    dept_id = Column(Integer, nullable=False)  # UNSIGNED
    dept_name = Column(String(100), nullable=True)
    program_id = Column(Integer, nullable=True)  # UNSIGNED
    program_name = Column(String(100), nullable=True)
    batch_id = Column(Integer, nullable=True)  # UNSIGNED
    batch_name = Column(String(50), nullable=True)
    semester = Column(Integer, nullable=False)  # UNSIGNED
    crs_title = Column(String(45), nullable=True)
    ems_crs_code = Column(String(15), nullable=False)
    dvs_crs_code = Column(String(20), nullable=False)
    result_year = Column(Date, nullable=False)
    event_type = Column(String(45), nullable=False)
    is_dvs_synced = Column(Boolean, default=False)  # tinyint(1) UNSIGNED
    status = Column(Boolean, default=True)  # tinyint(1)
    created_by = Column(Integer, nullable=False)  # UNSIGNED
    created_at = Column(DateTime, nullable=False)
    modified_by = Column(Integer, nullable=True)  # UNSIGNED
    modified_at = Column(DateTime, nullable=True)


class IEMSCourseType(Base):
    __tablename__ = 'iems_course_type'

    course_type_id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED
    course_type_code = Column(String(45), nullable=False)
    course_type_desc = Column(String(45), nullable=False)
    cia_max_marks = Column(Float, default=0)
    cia_min_marks = Column(Float, default=0)
    see_max_marks = Column(Float, default=0)
    see_min_marks = Column(Float, default=0)
    total_classes = Column(Float, nullable=False)
    total_classes_fastrack = Column(Integer, nullable=False)  # UNSIGNED
    min_passing_marks = Column(Float, nullable=False)
    org_id = Column(Integer, nullable=True)  # UNSIGNED
    status = Column(Integer, nullable=False)  # mediumint(8) UNSIGNED
    created_by = Column(Integer, nullable=False)  # mediumint(8) UNSIGNED
    modified_by = Column(Integer, nullable=False)  # mediumint(8) UNSIGNED
    create_date = Column(Integer, nullable=False)  # mediumint(8) UNSIGNED
    modify_date = Column(Integer, nullable=False)  # mediumint(8) UNSIGNED
    cia_weightage = Column(Integer, nullable=False, default=0)  # tinyint(3) UNSIGNED
    see_weightage = Column(Integer, nullable=False, default=0)  # tinyint(3) UNSIGNED
    viva_min_marks = Column(Float, default=0)
    viva_max_marks = Column(Float, default=0)
    viva_weightage = Column(Integer, default=0)  # tinyint(3) UNSIGNED


class IEMSCrclmTerm(Base):
    __tablename__ = 'iems_crclm_term'

    crclm_term_id = Column(Integer, primary_key=True, autoincrement=False)  # mediumint(8) UNSIGNED
    term_name = Column(Integer, nullable=False)  # UNSIGNED
    crclm_id = Column(Integer, nullable=False)  # mediumint(8) UNSIGNED
    term_min_credits = Column(String(2), nullable=False)
    term_max_credits = Column(String(2), nullable=False)


class IEMSCrsFaculty(Base):
    __tablename__ = 'iems_crs_faculty'

    id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED
    crs_code = Column(String(45), nullable=False)
    faculty_id = Column(Integer, nullable=True)  # UNSIGNED
    sem_time_table_id = Column(Integer, nullable=False)  # UNSIGNED
    crs_id = Column(Integer, nullable=True)  # UNSIGNED


class IEMSCurriculum(Base):
    __tablename__ = 'iems_curriculum'

    crclm_id = Column(Integer, primary_key=True, autoincrement=False)  # mediumint(8) UNSIGNED
    start_year = Column(Integer, nullable=False)  # year(4)
    pgm_id = Column(Integer, nullable=False)  # mediumint(8) UNSIGNED
    dept_id = Column(Integer, nullable=False)  # mediumint(8) UNSIGNED


class IEMSCustomTimeTable(Base):
    __tablename__ = 'iems_custom_time_table'

    id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED
    pgm_id = Column(Integer, nullable=False, default=0)  # UNSIGNED
    dept_id = Column(Integer, nullable=False, default=0)  # UNSIGNED
    academic_batch = Column(String(45), nullable=False)
    semester = Column(Integer, nullable=False)  # UNSIGNED
    section = Column(String(2), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(String(45), nullable=False)
    end_time = Column(String(45), nullable=False)
    crs_code = Column(String(45), nullable=False)
    tt_batch_id = Column(Integer, nullable=False, default=0)  # UNSIGNED
    faculty_id = Column(Integer, nullable=False)  # UNSIGNED
    status = Column(String(45), nullable=False)
    org_id = Column(Integer, nullable=False)  # UNSIGNED
    created_by = Column(Integer, nullable=False)  # UNSIGNED
    created_on = Column(DateTime, nullable=False)
    modified_by = Column(Integer, nullable=False)  # UNSIGNED
    modified_on = Column(DateTime, nullable=False)
    batch_name = Column(String(45), nullable=False)


class IEMSDailyAttendance(Base):
    __tablename__ = 'iems_daily_attendance'

    attendance_id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED
    result_year = Column(Date, nullable=True)
    crs_code = Column(String(25), nullable=True)
    student_id = Column(Integer, nullable=True)  # mediumint(8)
    regno = Column(String(45), nullable=False)
    usno = Column(String(20), nullable=True)
    section = Column(String(20), nullable=True)
    sessions = Column(String(20), nullable=True)
    start_time = Column(String(45), nullable=True)
    end_time = Column(String(45), nullable=True)
    attendance_status = Column(String(2), nullable=True)
    other_reason = Column(Boolean, default=False)  # tinyint(1)
    user_id = Column(String(100), nullable=True)
    lab_course_batch_id = Column(Integer, nullable=True)
    sem_time_table_id = Column(Integer, nullable=True)
    posted_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    org_id = Column(Integer, nullable=True)
    crs_id = Column(Integer, nullable=True)
    created_date = Column(DateTime, nullable=True)
    updated_date = Column(DateTime, nullable=True)
    is_extra_class = Column(Integer, nullable=False, default=0)  # UNSIGNED
    is_by_web = Column(Integer, nullable=False, default=0)  # UNSIGNED


class IEMSDepartment(Base):
    __tablename__ = 'iems_department'

    dept_id = Column(Integer, primary_key=True, autoincrement=True)
    dept_name = Column(String(100), nullable=False)
    dept_description = Column(String(500), nullable=True)
    dept_acronym = Column(String(20), nullable=True)
    dept_code_usn = Column(String(45), nullable=False)
    status = Column(Boolean, default=False)  # tinyint(1)
    org_id = Column(Integer, nullable=False)  # UNSIGNED
    no_batch_dept = Column(Integer, default=0)  # tinyint(2) UNSIGNED
    dept_hod_id = Column(Integer, nullable=True)  # mediumint(8) UNSIGNED
    created_by = Column(Integer, nullable=True)  # mediumint(8) UNSIGNED
    modified_by = Column(Integer, nullable=True)  # mediumint(8) UNSIGNED
    create_date = Column(Date, nullable=True)
    modify_date = Column(Date, nullable=True)

    programs = relationship("IEMProgram", back_populates="department")


class IEMSEducationQualificationMaster(Base):
    __tablename__ = 'iems_education_qualification_master'

    education_qualification_master_id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED
    education_qualification_code = Column(String(45), nullable=True)
    education_qualification_description = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=True)
    status = Column(Boolean, nullable=True)  # tinyint(1)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMSEventCalenderDetails(Base):
    __tablename__ = 'iems_event_calender_details'

    event_calender_id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED
    event_master_id = Column(Integer, nullable=True)  # UNSIGNED
    event_calender_description = Column(String(500), nullable=True)
    event_from_date = Column(Date, nullable=True)
    event_end_date = Column(Date, nullable=True)
    event_from_time = Column(String(10), nullable=True)
    event_from_time_meridian = Column(String(2), nullable=True)
    event_to_time = Column(String(10), nullable=True)
    event_to_time_meridian = Column(String(2), nullable=True)
    org_id = Column(Integer, nullable=True)
    status = Column(Boolean, nullable=True)  # tinyint(1)


class IEMSEventStatus(Base):
    __tablename__ = 'iems_event_status'

    id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED
    event_status = Column(String(45), nullable=False)


class IEMSEventType(Base):
    __tablename__ = 'iems_event_type'

    id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED
    event = Column(String(45), nullable=False)
    allow_even_sem_backlog = Column(Boolean, nullable=False)  # tinyint(1) UNSIGNED
    allow_odd_sem_backlog = Column(Boolean, nullable=False)  # tinyint(1) UNSIGNED
    carry_fwd_cia_marks = Column(Boolean, nullable=False)  # tinyint(1) UNSIGNED
    crs_limit_backlog = Column(String(2), nullable=False)


class IEMSEventTypeMaster(Base):
    __tablename__ = 'iems_event_type_master'

    event_master_id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED
    event_master_type = Column(String(100), nullable=False)
    event_master_description = Column(String(500), nullable=True)
    status = Column(Boolean, nullable=False)  # tinyint(1) UNSIGNED
    org_id = Column(Integer, nullable=False)  # UNSIGNED
    date_only = Column(Boolean, nullable=False, default=False)  # tinyint(1) UNSIGNED
    date_time = Column(Boolean, nullable=False, default=False)  # tinyint(1) UNSIGNED


class IEMSExaminerLabBatch(Base):
    __tablename__ = 'iems_examiner_lab_batch'

    examiner_batch_id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED
    examiner_id = Column(Integer, nullable=True)
    examiner_type = Column(String(10), nullable=True)
    lab_theory_type = Column(String(10), nullable=True)
    result_year = Column(Date, nullable=True)
    crs_id = Column(Integer, nullable=True)
    crs_code = Column(String(10), nullable=True)
    lab_batch = Column(String(10), nullable=True)
    status = Column(Integer, nullable=True)  # UNSIGNED
    lab_batch_id = Column(Integer, nullable=True)  # UNSIGNED


class IEMExaminerRegistration(Base):
    __tablename__ = 'iems_examiner_registration'

    examiner_registration_id = Column(Integer, primary_key=True, autoincrement=True)  # INT(11)
    labtheory = Column(String(45), nullable=True)
    name = Column(String(50), nullable=True)
    designation = Column(String(75), nullable=True)
    affiliation = Column(String(100), nullable=True)
    mobile = Column(String(10), nullable=True)
    email = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    status = Column(Integer, nullable=True)  # INT(10)
    created_by = Column(Integer, nullable=True)  # INT(10)
    modified_by = Column(Integer, nullable=True)  # INT(10)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    last_name = Column(String(45), nullable=True)
    department = Column(String(45), nullable=True)
    college = Column(String(100), nullable=True)
    qualification = Column(String(100), nullable=True)
    experience = Column(String(15), nullable=True)
    specialization = Column(String(45), nullable=True)
    examiner_type = Column(String(15), nullable=False)
    user_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    username = Column(String(40), nullable=True)


class IEMExamAppVersion(Base):
    __tablename__ = 'iems_exam_app_version'

    id = Column(Integer, primary_key=True, autoincrement=False)  # INT(11)
    version_code = Column(Integer, nullable=True)  # INT(11)
    file_path = Column(String(1000), nullable=True)


class IEMExamDateSession(Base):
    __tablename__ = 'iems_exam_date_session'

    id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED INT(11)
    exam_date = Column(Date, nullable=False)
    exam_session_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    result_year = Column(Date, nullable=False)


class IEMExamEvent(Base):
    __tablename__ = 'iems_exam_event'

    id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED INT(10)
    result_year = Column(Date, nullable=False)
    belonging_year = Column(Date, nullable=True)
    is_reduced_grade = Column(Boolean, default=False)  # TINYINT(1)
    crs_rslt_start_year = Column(Date, nullable=False)
    crs_rslt_end_year = Column(Date, nullable=False)
    status = Column(String(15), nullable=False, default='1')
    event_type = Column(String(45), nullable=False)
    is_attempt = Column(Boolean, nullable=False, default=False)  # TINYINT(1)
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    exam_fee_last_date = Column(Date, nullable=True)
    crs_withdrawl_last_date = Column(Date, nullable=True)
    re_eval_last_date = Column(Date, nullable=True)
    challenge_re_eval_last_date = Column(Date, nullable=True)
    see_start_date = Column(Date, nullable=True)
    see_end_date = Column(Date, nullable=True)
    semester_start_date = Column(Date, nullable=True)
    semester_end_date = Column(Date, nullable=True)
    reeval_start_date = Column(Date, nullable=True)
    reeval_end_date = Column(Date, nullable=True)
    reeval_result_date = Column(Date, nullable=True)
    challenge_reeval_start_date = Column(Date, nullable=True)
    challenge_reeval_end_date = Column(Date, nullable=True)
    challenge_reeval_result_date = Column(Date, nullable=True)
    event_status = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    result_year_desc = Column(String(45), nullable=True)
    last_day_for_dropping_course = Column(Date, nullable=True)
    lab_see_start_date = Column(Date, nullable=True)
    lab_see_end_date = Column(Date, nullable=True)


class IEMExamHallMaster(Base):
    __tablename__ = 'iems_exam_hall_master'

    exam_hall_master_id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED INT(11)
    hall_code = Column(String(45), nullable=False)
    hall_desc = Column(String(75), nullable=False)
    hall_location = Column(String(75), nullable=False)
    no_seats = Column(String(10), nullable=True)
    per_seats = Column(String(10), nullable=True)
    status = Column(Boolean, nullable=False)  # TINYINT(1) UNSIGNED
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    priority = Column(Integer, default=1)
    availability = Column(Integer, default=1)
    type = Column(Integer, default=1)
    created_by = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    modified_by = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)


class IEMExamSession(Base):
    __tablename__ = 'iems_exam_session'

    exam_session_id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED INT(11)
    session = Column(String(45), nullable=True)
    start_time = Column(String(10), nullable=True)
    start_time_meridiem = Column(String(2), nullable=True)
    end_time = Column(String(10), nullable=True)
    end_time_meridiem = Column(String(2), nullable=True)
    status = Column(Boolean, nullable=True)  # TINYINT(1)
    org_id = Column(Integer, nullable=True)  # INT(11)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMExamStudentCourses(Base):
    __tablename__ = 'iems_exam_student_courses'

    id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED INT(11)
    regno = Column(String(45), nullable=False)
    crs_code = Column(String(15), nullable=False)
    hall_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    exam_time_table_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    std_crs_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    status = Column(Integer, default=1)  # TINYINT(2) UNSIGNED


class IEMExamTimeTable(Base):
    __tablename__ = 'iems_exam_time_table'

    exam_time_table_id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED INT(11)
    lab_course = Column(String(1), nullable=True)
    result_year = Column(Date, nullable=True)
    department_id = Column(Integer, default=0)  # UNSIGNED INT(11)
    program_id = Column(Integer, default=0)  # UNSIGNED INT(11)
    academic_batch_id = Column(Integer, default=0)  # UNSIGNED INT(11)
    semester = Column(Integer, nullable=True)
    exam_session_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    crs_code = Column(String(15), nullable=True)
    exam_date = Column(Date, nullable=True)
    status = Column(Boolean, nullable=True)  # TINYINT(1)
    org_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    batch_cycle_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)


class IEMExamTimeTableDetail(Base):
    __tablename__ = 'iems_exam_time_table_detail'

    exam_time_table_detail_id = Column(Integer, primary_key=True, autoincrement=True)  # UNSIGNED INT(11)
    exam_time_table_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    crs_code = Column(String(25), nullable=True)
    lab_batch = Column(String(45), nullable=True)
    venue = Column(String(100), nullable=True)
    exam_session_id = Column(Integer, nullable=True)  # INT(10)
    exam_date = Column(Date, nullable=True)
    status = Column(Boolean, nullable=True)  # TINYINT(1)
    org_id = Column(Integer, nullable=True)  # INT(11)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMFacultyCourseClasses(Base):
    __tablename__ = 'iems_faculty_course_classes'

    faculty_course_classes_id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED INT(11)
    result_year = Column(Date, nullable=True)
    dept_id = Column(Integer, nullable=True)
    program_id = Column(Integer, nullable=True)  # MEDIUMINT(8)
    batch_id = Column(Integer, nullable=True)
    semester = Column(Integer, nullable=True)
    section = Column(String(10), nullable=True)
    crs_id = Column(Integer, nullable=True)
    crs_code = Column(String(15), nullable=True)
    user_id = Column(Integer, nullable=True)
    classes = Column(Integer, nullable=True)
    org_id = Column(Integer, nullable=True)
    status = Column(Integer, nullable=True)  # MEDIUMINT(8)
    created_by = Column(Integer, nullable=True)
    created_date = Column(DateTime, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(DateTime, nullable=True)
    is_finalized = Column(Boolean, default=False)  # TINYINT(3) UNSIGNED
    finalized_date = Column(DateTime, nullable=True)
    lab_course_batch_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)


class IEMFacultyExtraClasses(Base):
    __tablename__ = 'iems_faculty_extra_classes'

    extra_classes_id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED INT(11)
    result_year = Column(Date, nullable=True)
    crs_code = Column(String(15), nullable=True)
    section = Column(String(10), nullable=True)
    class_type = Column(String(15), nullable=True)
    class_date = Column(String(45), nullable=True)
    period = Column(String(45), nullable=True)
    user_id = Column(Integer, nullable=True)
    status = Column(Integer, nullable=True)  # MEDIUMINT(8)
    actual_user_id = Column(Integer, nullable=True)
    org_id = Column(Integer, nullable=True)
    is_approved = Column(Integer, nullable=True)  # MEDIUMINT(8)
    approved_date = Column(DateTime, nullable=True)
    lab_course_batch_id = Column(Integer, nullable=True)
    lab_batch_name = Column(String(40), nullable=True)
    sem_time_table_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)


class IEMFacultyOccasion(Base):
    __tablename__ = 'iems_faculty_occasion'

    faculty_occasion_id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED INT(10)
    faculty_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    ao_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    faculty_max_marks = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    crs_code = Column(String(45), nullable=False)
    result_year = Column(String(45), nullable=False)
    section = Column(String(10), nullable=False)
    weightage = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    org_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    is_finalized = Column(Integer, default=0)  # TINYINT(2) UNSIGNED
    academic_batch_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)


class IEMFeedbackCategory(Base):
    __tablename__ = 'iems_feedback_category'

    id = Column(Integer, primary_key=True)  # INT(11)
    category_id = Column(Integer, nullable=False)  # INT(11)
    feedback_name = Column(String(80), nullable=True)


class IEMFeedbackForm(Base):
    __tablename__ = 'iems_feedback_form'

    feedback_id = Column(Integer, primary_key=True, autoincrement=False)  # UNSIGNED INT(10)
    feedback_category = Column(Integer, nullable=True)  # INT(11)
    feedback_type = Column(Integer, nullable=False)  # INT(11)
    feedback_desc = Column(Text, nullable=False)
    regno = Column(String(45), nullable=True)
    user_id = Column(String(45), nullable=True)
    email = Column(String(45), nullable=False)
    posted_date = Column(String(45), nullable=True)
    status = Column(Integer, default=1)  # TINYINT(4)


class IEMFirebaseNotification(Base):
    __tablename__ = 'iems_firebase_notification'

    notification_id = Column(Integer, primary_key=True)  # INT(11)
    regno = Column(String(45), nullable=True)
    firebase_register_id = Column(String(200), nullable=True)
    usno = Column(String(20), nullable=True)
    faculty_id = Column(Integer, nullable=True)  # INT(11)


class IEMFlipCourseDetails(Base):
    __tablename__ = 'iems_flip_course_details'

    flip_crs_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    result_year = Column(Date, nullable=True)
    batch_id = Column(Integer, nullable=True)  # INT(11)
    batch_cycle_id = Column(Integer, nullable=True)  # TINYINT(1)
    crs_code = Column(String(15), nullable=True)
    semester = Column(Integer, nullable=True)  # TINYINT(2)
    section = Column(String(25), nullable=True)
    user_id = Column(Integer, nullable=True)  # INT(11)
    course_type_id = Column(Integer, nullable=True)  # INT(11)
    org_id = Column(Integer, nullable=True)  # INT(11)
    created_by = Column(Integer, nullable=True)  # INT(11)
    created_at = Column(DateTime, nullable=True)
    updated_by = Column(Integer, nullable=True)  # INT(11)
    updated_at = Column(DateTime, nullable=True)


class IEMGCStore(Base):
    __tablename__ = 'iems_gc_store'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    gc_code = Column(String(30, 'utf8'), nullable=False)
    usno = Column(String(20, 'utf8'), nullable=False)
    result_year = Column(Date, nullable=False)
    semester = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    regno = Column(String(20, 'utf8'), nullable=False)


class IEMGrace(Base):
    __tablename__ = 'iems_grace'

    grace_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    grace_type = Column(String(45, 'utf8'), nullable=False)
    grace_description = Column(String(45, 'utf8'), nullable=False)
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    grace_marks = Column(Float, nullable=False)  # DOUBLE
    status = Column(Integer, default=1)  # TINYINT(1) UNSIGNED
    show = Column(Integer, default=1)  # TINYINT(1) UNSIGNED


class IEMGraceMaster(Base):
    __tablename__ = 'iems_grace_master'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    grace_type = Column(String(45), nullable=False)


class IEMGracePreferences(Base):
    __tablename__ = 'iems_grace_preferences'

    preferences_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    preferences_type = Column(String(45, 'utf8'), nullable=False)
    priority = Column(String(45, 'utf8'), nullable=False)


class IEMGraceStudentCourses(Base):
    __tablename__ = 'iems_grace_student_courses'

    grace_std_crs_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    std_crs_id = Column(Integer, nullable=False)  # INT(11)
    semester = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    result_year = Column(String(45), nullable=True)
    grace_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    preferences_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    split_marks = Column(Float, nullable=False)  # DOUBLE
    regno = Column(String(45, 'utf8'), nullable=False)
    finalize = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    status = Column(Integer, default=1)  # TINYINT(1) UNSIGNED


class IEMGrade(Base):
    __tablename__ = 'iems_grade'

    grade_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    org_id = Column(Integer, nullable=True)  # INT(11)
    pgm_type = Column(String(10), nullable=False)
    is_reduced_grade = Column(Integer, default=0)  # TINYINT(1)
    grade = Column(String(10), nullable=False)
    grade_level = Column(String(100), nullable=False)
    min_operator = Column(String(5), nullable=False)
    min_range = Column(Integer, nullable=False)  # UNSIGNED TINYINT(3)
    max_range = Column(Integer, nullable=False)  # UNSIGNED TINYINT(3)
    max_operator = Column(String(5), nullable=False)
    grade_point = Column(String(2), nullable=False)
    grade_type = Column(String(100), nullable=False)
    x_cia = Column(Integer, default=60)  # UNSIGNED INT(11)


class IEMHallTypeMaster(Base):
    __tablename__ = 'iems_hall_type_master'

    hall_type_id = Column(Integer, primary_key=True)  # INT(11)
    hall_type_name = Column(String(10), nullable=False)
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    status = Column(Integer, nullable=False)  # TINYINT(1)


class IEMHODDepartments(Base):
    __tablename__ = 'iems_hod_departments'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    user_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    dept_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)


class IEMHODStaff(Base):
    __tablename__ = 'iems_hod_staff'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    hod_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    user_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    dept_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)


class IEMInSemExamDateSession(Base):
    __tablename__ = 'iems_in_sem_exam_date_session'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    exam_date = Column(Date, nullable=False)
    exam_session_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    result_year = Column(Date, nullable=False)


class IEMInSemExamStudentCourses(Base):
    __tablename__ = 'iems_in_sem_exam_student_courses'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    regno = Column(String(45, 'utf8'), nullable=False)
    crs_code = Column(String(15, 'utf8'), nullable=False)
    hall_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    exam_time_table_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    std_crs_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    status = Column(Integer, default=1)  # TINYINT(2) UNSIGNED


class IEMInSemExamTimeTable(Base):
    __tablename__ = 'iems_in_sem_exam_time_table'

    exam_time_table_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    result_year = Column(Date, nullable=True)
    department_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    program_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    academic_batch_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    batch_cycle_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    semester = Column(Integer, nullable=True)  # INT(11)
    crs_code = Column(String(15, 'utf8'), nullable=True)
    lab_course = Column(String(1, 'utf8'), nullable=True)
    cia_master_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    cia_map_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    exam_date = Column(Date, nullable=True)
    exam_session_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    bc_type = Column(Integer, nullable=False)  # UNSIGNED TINYINT(1)
    status = Column(Integer, nullable=True)  # TINYINT(1)
    org_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    created_by = Column(Integer, nullable=True)  # INT(11)
    modified_by = Column(Integer, nullable=True)  # INT(11)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMInSemExamTimeTableDetail(Base):
    __tablename__ = 'iems_in_sem_exam_time_table_detail'

    exam_time_table_detail_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    exam_time_table_id = Column(Integer, nullable=True)  # INT(11)
    crs_code = Column(String(25), nullable=True)
    lab_batch = Column(String(45), nullable=True)
    exam_date = Column(Date, nullable=True)
    exam_session_id = Column(Integer, nullable=True)  # INT(10)
    status = Column(Integer, nullable=True)  # TINYINT(1)
    org_id = Column(Integer, nullable=True)  # INT(11)
    created_by = Column(Integer, nullable=True)  # INT(11)
    modified_by = Column(Integer, nullable=True)  # INT(11)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMInSemLabExamBatchStudentCourses(Base):
    __tablename__ = 'iems_in_sem_lab_exam_batch_student_courses'

    batch_student_courses_id = Column(Integer, primary_key=True)  # INT(11)
    regno = Column(String(45), nullable=False)
    crs_code = Column(String(15), nullable=False)
    exam_time_table_detail_id = Column(Integer, nullable=False)  # INT(11)
    exam_time_table_id = Column(Integer, nullable=False)  # INT(11)
    std_crs_id = Column(Integer, nullable=False)  # INT(11)
    org_id = Column(Integer, nullable=True)  # INT(11)
    status = Column(Integer, default=1)  # TINYINT(1) UNSIGNED


class IEMISEMSEOccasions(Base):
    __tablename__ = 'iems_ise_mse_occasions'

    im_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    ise_mse_type_id = Column(Integer, nullable=False)  # INT(11)
    ise_mse_label = Column(String(15), nullable=False)
    crs_code = Column(String(15), nullable=False)
    weightage = Column(String(45), nullable=False)
    result_year = Column(Date, nullable=True)
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    program_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    batch_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    status = Column(Integer, nullable=False)  # TINYINT(1)
    created_by = Column(Integer, nullable=False)  # INT(11)
    modified_by = Column(Integer, nullable=False)  # INT(11)
    create_date = Column(DateTime, nullable=False)
    modify_date = Column(DateTime, nullable=False)


class IEMISEMSEType(Base):
    __tablename__ = 'iems_ise_mse_type'

    ise_mse_type_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    ise_mse_type_name = Column(String(45), nullable=False)


class IEMLabCourseBatch(Base):
    __tablename__ = 'iems_lab_course_batch'

    lab_course_batch_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    result_year = Column(String(45), nullable=False)
    department_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    program_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    academic_batch_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    semester = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    batch_cycle_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    lab_batch_name = Column(String(100), nullable=True)
    crs_id = Column(Integer, nullable=True)
    crs_code = Column(String(15), nullable=True)
    lab_batch_strength = Column(Integer, nullable=True)  # INT(3)
    org_id = Column(Integer, nullable=True)  # INT(11)
    is_all = Column(SmallInteger, default=0)  # TINYINT(1) UNSIGNED
    status = Column(SmallInteger, nullable=True)  # TINYINT(1)
    created_by = Column(Integer, nullable=True)  # INT(11)
    created_at = Column(DateTime, nullable=True)
    updated_by = Column(Integer, nullable=True)  # INT(11)
    updated_at = Column(DateTime, nullable=True)


class IEMLabExamBatchStudentCourses(Base):
    __tablename__ = 'iems_lab_exam_batch_student_courses'

    batch_student_courses_id = Column(Integer, primary_key=True)  # INT(11)
    regno = Column(String(45), nullable=False)
    crs_code = Column(String(15), nullable=False)
    exam_time_table_detail_id = Column(Integer, nullable=False)  # INT(11)
    exam_time_table_id = Column(Integer, nullable=False)  # INT(11)
    std_crs_id = Column(Integer, nullable=False)  # INT(11)
    org_id = Column(Integer, nullable=True)  # INT(11)
    status = Column(SmallInteger, default=1)  # TINYINT(1) UNSIGNED


class IEMLinkCourse(Base):
    __tablename__ = 'iems_link_course'

    link_id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    crs_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    link_crs_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    org_id = Column(Integer, nullable=False)  # INT(11)


class IEMMasters(Base):
    __tablename__ = 'iems_masters'

    master_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    master_name = Column(String(45), nullable=True)
    master_description = Column(String(255), nullable=True)
    status = Column(SmallInteger, default=1)  # TINYINT(1) UNSIGNED
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    created_by = Column(Integer, nullable=True)  # INT(11)
    modified_by = Column(Integer, nullable=True)  # INT(11)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMNotificationDetails(Base):
    __tablename__ = 'iems_notification_details'

    id = Column(Integer, primary_key=True)  # INT(11)
    regno = Column(String(45), nullable=True)
    usno = Column(String(20), nullable=True)
    firebase_register_id = Column(String(200), nullable=False)
    notification_title = Column(Text, nullable=False)
    notification_message = Column(Text, nullable=False)
    notification_image = Column(String(200), nullable=False)
    notification_type = Column(String(100), nullable=True)
    faculty_id = Column(String(45), nullable=True)
    is_faculty = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modified_date = Column(DateTime, nullable=True)
    status = Column(Integer, nullable=True)


class IEMNotificationTitle(Base):
    __tablename__ = 'iems_notification_title'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    notification_title = Column(String(25), nullable=True)
    notification_desc = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    status = Column(SmallInteger, default=1)  # TINYINT(1) UNSIGNED


class IEMOldCIAStudentCourses(Base):
    __tablename__ = 'iems_old_cia_student_courses'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    crs_code = Column(String(45), nullable=False)
    occasion_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    result_year = Column(Date, nullable=False)
    regno = Column(String(15), nullable=False)
    secured_marks = Column(Integer, nullable=True)  # DOUBLE can be represented as FLOAT or DECIMAL
    is_bestof = Column(SmallInteger, nullable=False)  # TINYINT(1) UNSIGNED
    compute_cia = Column(Integer, nullable=True)  # DOUBLE
    std_crs_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    is_absentee = Column(SmallInteger, default=0)  # TINYINT(2)


class IEMOldExamStudentCourses(Base):
    __tablename__ = 'iems_old_exam_student_courses'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    regno = Column(String(45), nullable=False)
    crs_code = Column(String(15), nullable=False)
    hall_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    exam_time_table_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    std_crs_id = Column(Integer, nullable=False)  # UNSIGNED INT(11)
    status = Column(SmallInteger, nullable=False, default=1)  # TINYINT(2) UNSIGNED


class IEMOldStudentCourses(Base):
    __tablename__ = 'iems_old_student_courses'

    std_crs_id = Column(Integer, primary_key=True)  # UNSIGNED INT(11)
    regno = Column(String(45), nullable=True)
    usno = Column(String(20), nullable=True)
    crs_code = Column(String(15), nullable=True)
    result_year = Column(Date, nullable=True)
    program_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    batch_id = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    batch_cycle_id = Column(SmallInteger, nullable=True)  # TINYINT(1)
    org_id = Column(Integer, nullable=True)  # INT(11)
    semester = Column(SmallInteger, nullable=True)  # TINYINT(2)
    section = Column(String(10), nullable=True)
    is_registered = Column(Integer, default=0)  # INT(11)
    is_withdrawn = Column(SmallInteger, default=0)  # TINYINT(1)
    is_drop = Column(SmallInteger, default=0)  # TINYINT(1)
    is_withheld = Column(SmallInteger, default=0)  # TINYINT(1)
    is_evaluated = Column(SmallInteger, default=0)  # TINYINT(1)
    is_sup = Column(SmallInteger, default=0)  # TINYINT(1)
    sup_type = Column(SmallInteger, nullable=True)  # TINYINT(1)
    is_backlog = Column(SmallInteger, default=0)  # TINYINT(1)
    attendance = Column(Integer, nullable=True)  # DOUBLE can be represented as FLOAT or DECIMAL
    grace_attendance = Column(Integer, nullable=True)  # DOUBLE
    grace_flag = Column(SmallInteger, nullable=True)  # TINYINT(1)
    attendance_approved = Column(SmallInteger, default=0)  # TINYINT(1)
    attendance_approved_by = Column(Integer, nullable=True)  # INT(11)
    attendance_approved_date = Column(DateTime, nullable=True)
    remarks = Column(Text, nullable=True)
    total_cia = Column(Integer, nullable=True)  # DOUBLE
    total_ise = Column(Integer, nullable=True)  # DOUBLE
    total_mse = Column(Integer, nullable=True)  # DOUBLE
    cia_approved = Column(SmallInteger, default=0)  # TINYINT(1)
    cia_approved_by = Column(Integer, nullable=True)  # INT(11)
    cia_approved_date = Column(DateTime, nullable=True)
    attendance_eligibility = Column(String(1), nullable=True)
    cia_eligibility = Column(String(1), nullable=True)
    nsar_eligibility = Column(String(1), nullable=True)
    mkp_flag = Column(SmallInteger, default=0)  # TINYINT(1)
    ftrk_flag = Column(SmallInteger, default=0)  # TINYINT(1)
    consider = Column(SmallInteger, default=1)  # TINYINT(1)
    viva_marks = Column(Integer, nullable=True)  # DOUBLE
    viva_absentee = Column(SmallInteger, default=1)  # TINYINT(1) UNSIGNED
    is_viva_finalized = Column(SmallInteger, default=0)  # TINYINT(1) UNSIGNED
    see1 = Column(Integer, nullable=True)  # DOUBLE
    see2 = Column(Integer, nullable=True)  # DOUBLE
    see3 = Column(Integer, nullable=True)  # DOUBLE
    see = Column(Integer, nullable=True)  # DOUBLE
    see_actual = Column(Integer, nullable=True)  # DOUBLE
    is_see_consolidate = Column(SmallInteger, default=0)  # TINYINT(1) UNSIGNED
    is_see_imported = Column(SmallInteger, default=0)  # TINYINT(1)
    cia_see = Column(Integer, nullable=True)  # DOUBLE
    cia_see_actual = Column(Integer, nullable=True)  # DOUBLE
    credits_earned = Column(Integer, nullable=True)  # DOUBLE
    backlog_credit_hours = Column(Integer, nullable=True)  # DOUBLE
    is_grade_evaluated = Column(SmallInteger, default=0)  # TINYINT(4)
    grade = Column(String(2), nullable=True)
    grade_point = Column(String(2), nullable=True)
    grade_actual = Column(String(2), nullable=True)
    is_rejected = Column(SmallInteger, default=0)  # TINYINT(1)
    crta = Column(Integer, nullable=True)  # DOUBLE
    see_absentee = Column(SmallInteger, default=1)  # TINYINT(1) UNSIGNED
    is_mal_practice = Column(SmallInteger, default=0)  # TINYINT(1)
    attendance_percentage = Column(Integer, nullable=True)  # DOUBLE
    is_reeval = Column(SmallInteger, default=0)  # TINYINT(1)
    rsee1 = Column(Integer, nullable=True)  # DOUBLE
    rsee2 = Column(Integer, nullable=True)  # DOUBLE
    rsee3 = Column(Integer, nullable=True)  # DOUBLE
    rsee4 = Column(Integer, nullable=True)  # DOUBLE
    rsee5 = Column(Integer, nullable=True)  # DOUBLE
    rsee = Column(Integer, nullable=True)  # DOUBLE
    rsee_actual = Column(Integer, nullable=True)  # DOUBLE
    is_challenge_reeval = Column(SmallInteger, default=0)  # TINYINT(4)
    crsee1 = Column(Integer, nullable=True)  # DOUBLE
    crsee2 = Column(Integer, nullable=True)  # DOUBLE
    crsee3 = Column(Integer, nullable=True)  # DOUBLE
    crsee4 = Column(Integer, nullable=True)  # DOUBLE
    crsee5 = Column(Integer, nullable=True)  # DOUBLE
    crsee = Column(Integer, nullable=True)  # DOUBLE
    crsee_actual = Column(Integer, nullable=True)  # DOUBLE
    updated_by = Column(Integer, nullable=True)  # UNSIGNED INT(11)
    updated_at = Column(DateTime, nullable=True)
    is_result_finalized = Column(SmallInteger, default=0)  # TINYINT(2) UNSIGNED
    reason = Column(String(255), nullable=True)


class IEMOnlineAnswerSheetsZip(Base):
    __tablename__ = 'iems_online_answer_sheets_zip'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    course_group_id = Column(String(45), nullable=False)
    answer_sheet_pdf_zip = Column(String(255), nullable=True)


class IEMOnlineAssessments(Base):
    __tablename__ = 'iems_online_assessments'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    name = Column(String(45), nullable=False)
    result_year = Column(String(45), nullable=False)
    start_date = Column(String(45), nullable=False)
    end_date = Column(String(45), nullable=False)
    description = Column(String(255), nullable=True)
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    status = Column(SmallInteger, default=1)  # TINYINT(3) UNSIGNED
    deleted_at = Column(String(255), nullable=True)
    qp_view_time = Column(Integer, default=15)  # INT(11)
    answer_upload_time = Column(Integer, default=60)  # INT(11)
    procure_image_time = Column(Integer, default=120)  # INT(11)


class IEMOnlineCourseGroup(Base):
    __tablename__ = 'iems_online_course_group'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    name = Column(String(45), nullable=False)
    result_year = Column(String(45), nullable=False)
    assessment_type = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    description = Column(String(255), nullable=False)
    deleted_at = Column(String(45), nullable=True)


class IEMOnlineCourseMapping(Base):
    __tablename__ = 'iems_online_course_mapping'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    course_group_id = Column(String(45), nullable=False)
    crs_code = Column(String(45), nullable=False)
    batch_id = Column(String(45), nullable=False)


class IEMOnlineCoInvUsers(Base):
    __tablename__ = 'iems_online_co_inv_users'

    id = Column(Integer, primary_key=True)  # INT(11)
    user_id = Column(Integer, nullable=False)  # INT(11)
    user_type = Column(String(20), nullable=False)
    registered_coordinator = Column(Integer, nullable=True)  # INT(11)
    course_group_id = Column(Integer, nullable=False)  # INT(11)
    sub_course_group_id = Column(Integer, nullable=True)  # INT(11)
    last_updated_on = Column(String(25), nullable=True)
    last_updated_by = Column(Integer, nullable=True)  # INT(11)


class IEMOnlineCoInvUsersCourseGroups(Base):
    __tablename__ = 'iems_online_co_inv_users_course_groups'

    id = Column(Integer, primary_key=True)  # INT(11)
    co_inv_id = Column(Integer, nullable=False)  # INT(11)
    course_group_id = Column(Integer, nullable=True)  # INT(11)
    stud_course_group = Column(Integer, nullable=True)  # INT(11)
    last_updated_on = Column(DateTime, nullable=True)


class IEMOnlineExamAnswerDetails(Base):
    __tablename__ = 'iems_online_exam_answer_details'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    answer_master_id = Column(String(45), nullable=False)
    answer_sheet_image = Column(String(255), nullable=False)
    answer_sheet_no = Column(Integer, nullable=False)  # UNSIGNED INT(10)


class IEMOnlineExamAnswerMaster(Base):
    __tablename__ = 'iems_online_exam_answer_master'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    exam_id = Column(String(45), nullable=False)
    student_id = Column(String(45), nullable=False)
    no_of_sheets = Column(String(255), nullable=True)
    answer_sheet_pdf = Column(String(255), nullable=True)
    is_finalized = Column(SmallInteger, default=0)  # TINYINT(1) UNSIGNED
    answer_sheet_pdf_name = Column(String(255), nullable=True)
    image_published = Column(SmallInteger, default=0)  # TINYINT(3) UNSIGNED
    pdf_generated = Column(SmallInteger, default=0)  # TINYINT(3) UNSIGNED


class IEMOnlineExamAttendance(Base):
    __tablename__ = 'iems_online_exam_attendance'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    course_group_id = Column(String(45), nullable=False)
    stud_course_group = Column(String(45), nullable=True)
    student_id = Column(String(45), nullable=False)
    regno = Column(String(255), nullable=True)
    result_year = Column(Date, nullable=True)
    attendance_status = Column(Integer, nullable=True)  # INT(2)
    org_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    is_finalized = Column(SmallInteger, default=0)  # TINYINT(1) UNSIGNED
    user_id = Column(Integer, default=0)  # INT(11)
    created_date = Column(DateTime, nullable=True)
    updated_date = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=False)  # UNSIGNED INT(5)
    updated_by = Column(Integer, nullable=False)  # UNSIGNED INT(5)


class IEMOnlineExamCompletedStudentsDetails(Base):
    __tablename__ = 'iems_online_exam_completed_students_details'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    student_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    exam_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    quiz_id = Column(Integer, nullable=True)  # UNSIGNED INT(10)
    created_at = Column(String(255), nullable=True)


class IEMOnlineExamErrorLog(Base):
    __tablename__ = 'iems_online_exam_error_log'

    id = Column(Integer, primary_key=True)  # INT(11)
    error_message = Column(String(1000), nullable=True)


class IEMOnlineExamHallDetails(Base):
    __tablename__ = 'iems_online_exam_hall_details'

    id = Column(Integer, primary_key=True)  # UNSIGNED INT(10)
    student_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    exam_id = Column(Integer, nullable=False)  # UNSIGNED INT(10)
    hall_image = Column(String(255), nullable=False)
    hall_desc = Column(String(255), nullable=False)
    created_at = Column(String(255), nullable=False)


class IEMOnlineExamManageQuiz(Base):
    __tablename__ = 'iems_online_exam_manage_quiz'

    quiz_id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_title = Column(String(500), nullable=True)
    result_year = Column(String(45), nullable=False)
    course_group_id = Column(String(45), nullable=False)
    quiz_instruction = Column(Text, nullable=True)
    quiz_description = Column(Text, nullable=True)
    crclm_id = Column(Integer, nullable=True)
    crclm_term_id = Column(Integer, nullable=True)
    crs_id = Column(Integer, nullable=True)
    quiz_date = Column(String(45), nullable=True)
    quiz_time = Column(String(45), nullable=True)
    duration = Column(String(45), nullable=True)
    file_name = Column(String(1000), nullable=True)
    file_path = Column(String(5000), nullable=True)
    marks_flag = Column(SmallInteger, nullable=True)
    co_map_flag = Column(SmallInteger, nullable=True)
    bl_map_flag = Column(SmallInteger, nullable=True)
    practice_quiz = Column(SmallInteger, nullable=True)
    shuffle_questions = Column(SmallInteger, nullable=True)
    shuffle_options = Column(SmallInteger, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_date = Column(String(45), nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(String(45), nullable=True)
    exam_id = Column(String(45), nullable=True)


class IEMOnlineExamPapers(Base):
    __tablename__ = 'iems_online_exam_papers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(String(45), nullable=False)
    qp_link = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=True)
    deleted_at = Column(String(45), nullable=True)
    published_at = Column(String(45), nullable=True)
    qp_type = Column(Integer, nullable=False, default=0)


class IEMOnlineExamPaperStudents(Base):
    __tablename__ = 'iems_online_exam_paper_students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(String(45), nullable=False)
    student_id = Column(String(45), nullable=False)
    view_date = Column(String(255), nullable=False)


class IEMOnlineExamProcureDetails(Base):
    __tablename__ = 'iems_online_exam_procure_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    exam_id = Column(Integer, nullable=False)
    procure_image = Column(String(255), nullable=False)
    created_at = Column(String(255), nullable=False)


class IEMOnlineExamQuizQuestions(Base):
    __tablename__ = 'iems_online_exam_quiz_questions'

    qq_id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, nullable=True)
    main_que_code = Column(String(45), nullable=True)
    sub_que_code = Column(String(45), nullable=True)
    question = Column(Text, nullable=True)
    question_type = Column(SmallInteger, nullable=True)
    marks = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_date = Column(String(45), nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(String(45), nullable=True)


class IEMOnlineExamQuizQueOptions(Base):
    __tablename__ = 'iems_online_exam_quiz_que_options'

    qq_option_id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, nullable=True)
    qq_id = Column(Integer, nullable=True)
    question_type = Column(SmallInteger, nullable=True)
    option_value = Column(String(500), nullable=True)
    is_answer = Column(SmallInteger, default=0)


class IEMOnlineExamQuizStudentAnswer(Base):
    __tablename__ = 'iems_online_exam_quiz_student_answer'

    sqa_id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, nullable=True)
    qq_id = Column(Integer, nullable=True)
    qq_option_id = Column(Integer, nullable=True)
    student_id = Column(String(45), nullable=False)
    usn = Column(String(50), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_date = Column(String(45), nullable=True)


class IEMOnlineExamQuizStudentMapping(Base):
    __tablename__ = 'iems_online_exam_quiz_student_mapping'

    qs_map_id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, nullable=True)
    student_id = Column(String(45), nullable=False)
    usn = Column(String(45), nullable=True)
    q_secured_marks = Column(Integer, nullable=True)
    accept_rework_flag = Column(SmallInteger, default=0)
    rework_comment = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    viewed_on = Column(String(45), nullable=True)
    remaining_time = Column(String(50), nullable=True)
    secured_marks = Column(Integer, nullable=True)
    is_submitted = Column(SmallInteger, default=0)
    is_finalized = Column(SmallInteger, default=0)


class IEMOnlineExamRoleMenus(Base):
    __tablename__ = 'iems_online_exam_role_menus'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)
    parent = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)
    show = Column(SmallInteger, nullable=False)
    status = Column(SmallInteger, nullable=False)
    org_id = Column(Integer, default=1)


class IEMOnlineExamSchedule(Base):
    __tablename__ = 'iems_online_exam_schedule'

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_group_id = Column(Integer, nullable=False)
    exam_date = Column(String(45), nullable=False)
    start_time = Column(String(45), nullable=False)
    end_time = Column(String(45), nullable=False)
    deleted_at = Column(String(45), nullable=True)
    published_at = Column(String(45), nullable=True)
    meet_link = Column(String(255), nullable=True)


class IEMOnlineExamStartedStudentsDetails(Base):
    __tablename__ = 'iems_online_exam_started_students_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=True)
    exam_id = Column(Integer, nullable=True)
    quiz_id = Column(Integer, nullable=True)
    created_at = Column(String(255), nullable=True)


class IEMOnlineExamStudentSkipHallImage(Base):
    __tablename__ = 'iems_online_exam_student_skip_hall_image'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    exam_id = Column(Integer, nullable=False)
    skip_status = Column(SmallInteger, nullable=False)


class IEMOnlineExamStudNotificationDetails(Base):
    __tablename__ = 'iems_online_exam_stud_notification_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    exam_id = Column(Integer, nullable=False)
    message_details = Column(String(255), nullable=False)
    status = Column(SmallInteger, default=1)
    created_at = Column(String(255), nullable=False)


class IEMOnlineExamUserPermissions(Base):
    __tablename__ = 'iems_online_exam_user_permissions'

    access_id = Column(Integer, primary_key=True, autoincrement=True)
    user_role_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)
    permission_id = Column(Integer, nullable=False)
    status = Column(SmallInteger, default=1)
    org_id = Column(Integer, default=1)


class IEMOnlineExamUserRoleMaster(Base):
    __tablename__ = 'iems_online_exam_user_role_master'

    user_role_id = Column(Integer, primary_key=True, autoincrement=True)
    user_role = Column(String(45), nullable=False)
    user_role_description = Column(String(225), nullable=False)
    status = Column(SmallInteger, default=1)
    department_wise = Column(SmallInteger, default=0)
    core_role = Column(SmallInteger, default=0)


class IEMOnlineExamUserRolePermissions(Base):
    __tablename__ = 'iems_online_exam_user_role_permissions'

    access_id = Column(Integer, primary_key=True, autoincrement=True)
    user_role_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)
    permission_id = Column(Integer, nullable=False)
    status = Column(Integer, default=1)
    org_id = Column(Integer, default=1)


class IEMOnlineFirebaseNotification(Base):
    __tablename__ = 'iems_online_firebase_notification'

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(45), nullable=True)
    firebase_register_id = Column(String(200), nullable=True)


class IEMOnlineMenus(Base):
    __tablename__ = 'iems_online_menus'

    menu_id = Column(Integer, primary_key=True, autoincrement=True)
    menu_name = Column(String(45), nullable=True)
    parent = Column(SmallInteger, nullable=True)
    menu_level = Column(Integer, nullable=True)
    menu_url = Column(String(255), nullable=True)
    menu_class = Column(String(100), nullable=True)
    menu_icon = Column(String(100), nullable=True)
    menu_order = Column(Integer, nullable=True)
    show_menu = Column(SmallInteger, default=1)
    status = Column(SmallInteger, nullable=False)


class IEMOnlineNotificationDetails(Base):
    __tablename__ = 'iems_online_notification_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(45), nullable=True)
    firebase_register_id = Column(String(200), nullable=False)
    notification_title = Column(Text, nullable=False)
    notification_message = Column(Text, nullable=False)
    notification_image = Column(String(200), nullable=False)
    notification_type = Column(String(100), nullable=True)
    faculty_id = Column(String(45), nullable=True)
    is_faculty = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modified_date = Column(DateTime, nullable=True)
    status = Column(Integer, nullable=True)


class IEMOnlineStudentReUploadPermission(Base):
    __tablename__ = 'iems_online_student_re_upload_permission'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    exam_id = Column(Integer, nullable=False)
    upload_date = Column(String(255), nullable=False)
    upload_start_time = Column(String(255), nullable=False)
    upload_end_time = Column(String(255), nullable=False)
    status = Column(SmallInteger, default=0)


class IEMOnlineStudentUploadPermission(Base):
    __tablename__ = 'iems_online_student_upload_permission'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    exam_id = Column(Integer, nullable=False)
    upload_date = Column(String(255), nullable=False)
    upload_start_time = Column(String(255), nullable=False)
    upload_end_time = Column(String(255), nullable=False)
    otp = Column(Integer, nullable=True)
    otp_expiry_time = Column(String(255), nullable=True)
    status = Column(SmallInteger, default=0)
    otp_verified = Column(SmallInteger, default=0)


class IEMOnlineSubCourseGroupStudList(Base):
    __tablename__ = 'iems_online_sub_course_group_stud_list'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    std_crs_id = Column(Integer, nullable=False)
    sub_course_group_id = Column(Integer, nullable=True)
    invigilator_id = Column(Integer, nullable=True)
    deleted_at = Column(String(45), nullable=True)


class IEMOnlineSubInvigCourseGroup(Base):
    __tablename__ = 'iems_online_sub_invig_course_group'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), nullable=False)
    result_year = Column(String(45), nullable=False)
    assessment_type = Column(Integer, nullable=False)
    course_group_id = Column(Integer, nullable=False)
    description = Column(String(255), nullable=False)
    student_count = Column(Integer, nullable=False)
    deleted_at = Column(String(45), nullable=True)
    meet_link = Column(String(255), nullable=True)


class IEMOnlineUserPermissions(Base):
    __tablename__ = 'iems_online_user_permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_role = Column(String(45), nullable=False)
    user_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)
    status = Column(SmallInteger, default=1)
    org_id = Column(Integer, default=1)


class IEMOrganisation(Base):
    __tablename__ = 'iems_organisation'

    org_id = Column(Integer, primary_key=True, autoincrement=True)
    org_name = Column(String(500), nullable=False)
    org_society = Column(String(200), nullable=True)
    org_desc = Column(String(2500), nullable=True)
    unv_id = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(Date, nullable=True)
    modify_date = Column(Date, nullable=True)
    org_code = Column(String(10), nullable=True)
    org_type_id = Column(Integer, nullable=True)
    profile_image = Column(String(45), nullable=True)
    other_profile_image = Column(String(45), nullable=True)


class IEMOrganisationType(Base):
    __tablename__ = 'iems_organisation_type'

    org_type_id = Column(Integer, primary_key=True, autoincrement=True)
    org_type = Column(String(50), nullable=False)
    org_type_desc = Column(String(50), nullable=False)
    unv_id = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)


class IEMOrgConfigs(Base):
    __tablename__ = 'iems_org_configs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_type = Column(String(45), nullable=False)
    description = Column(Text, nullable=False)
    value = Column(String(100), nullable=False)
    org_id = Column(Integer, nullable=True)
    program_id = Column(Integer, nullable=True)
    crs_code = Column(String(15), nullable=True)
    db_bulk_flag = Column(String(10), nullable=False)


class IEMParentsOccupationMaster(Base):
    __tablename__ = 'iems_parents_occupation_master'

    occupation_id = Column(Integer, primary_key=True, autoincrement=True)
    occupation_description = Column(String(100), nullable=True)
    status = Column(SmallInteger, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class IEMPercentageClass(Base):
    __tablename__ = 'iems_percentage_class'

    id = Column(Integer, primary_key=True, autoincrement=True)
    regno = Column(String(45), nullable=False)
    usno = Column(String(20), nullable=False)
    sem = Column(Integer, nullable=False)
    program_id = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    grand_total = Column(Float, nullable=False)
    grand_grade = Column(String(5), default='')
    class_obtained = Column(String(100), nullable=False)
    result_year = Column(String(15), nullable=False)
    org_id = Column(Integer, nullable=False)
    consider = Column(SmallInteger, default=1)


class IEMPeriod(Base):
    __tablename__ = 'iems_period'

    period_id = Column(Integer, primary_key=True, autoincrement=True)
    period_name = Column(String(45), nullable=True)
    start_time = Column(String(45), nullable=True)
    end_time = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=True)
    is_extra = Column(Integer, default=0)
    created_by = Column(Integer, nullable=True)
    created_date = Column(DateTime, nullable=False)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Date, nullable=True)


class IEMPermissions(Base):
    __tablename__ = 'iems_permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    permission = Column(String(45), nullable=False)
    status = Column(SmallInteger, default=1)


class IEMPriorityMaster(Base):
    __tablename__ = 'iems_priority_master'

    priority_id = Column(Integer, primary_key=True, autoincrement=True)
    priority_name = Column(String(10), nullable=False)
    org_id = Column(Integer, nullable=False)
    status = Column(SmallInteger, nullable=False)


class IEMProgram(Base):
    __tablename__ = 'iems_program'

    pgm_id = Column(Integer, primary_key=True, autoincrement=True)
    pgm_title = Column(String(100), nullable=False)
    pgm_acronym = Column(String(250), nullable=False)
    pgm_specialization = Column(String(250), nullable=True)
    dept_id = Column(Integer, ForeignKey('iems_department.dept_id'), nullable=False)
    pgmtype_id = Column(Integer, ForeignKey('iems_program_type.pgmtype_id'), nullable=False)
    status = Column(SmallInteger, default=1)
    org_id = Column(Integer, nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(Date, nullable=True)
    modify_date = Column(Date, nullable=True)
    total_credits = Column(Integer, nullable=False)
    lateral_entry_credits = Column(Integer, nullable=False)
    total_terms = Column(Integer, nullable=True)
    term_min_credits = Column(Integer, nullable=True)
    term_max_credits = Column(Integer, nullable=True)
    term_min_duration = Column(Integer, nullable=True)
    term_max_duration = Column(Integer, nullable=True)

    department = relationship("IEMSDepartment", back_populates="programs")
    curriculums = relationship("Curriculum", back_populates="program")


class IEMProgramType(Base):
    __tablename__ = 'iems_program_type'

    pgmtype_id = Column(Integer, primary_key=True, autoincrement=True)
    pgmtype_name = Column(String(100), nullable=False)
    pgmtype_description = Column(String(500), nullable=True)
    program_type_code = Column(String(10), nullable=True)
    status = Column(SmallInteger, default=1)
    org_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=False)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(Integer, nullable=False)
    modify_date = Column(Integer, nullable=True)


class IEMProgressionRule(Base):
    __tablename__ = 'iems_progression_rule'

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, nullable=False)
    semester_progression = Column(SmallInteger, nullable=False)
    semester = Column(SmallInteger, nullable=False)
    academic_year = Column(String(4), nullable=False)
    semwise_max_attendance_ineligible_allowed = Column(SmallInteger, nullable=True)
    semwise_max_cia_ineligible_allowed = Column(SmallInteger, nullable=True)
    semwise_max_fail_allowed = Column(SmallInteger, nullable=True)
    program_year = Column(String(2), nullable=True)
    yearwise_max_cia_ineligible_allowed = Column(SmallInteger, nullable=True)
    yearwise_max_fail_allowed = Column(SmallInteger, nullable=True)
    overall_max_fail_allowed = Column(SmallInteger, nullable=True)
    overall_min_cgpa_required = Column(Float, nullable=True)
    org_id = Column(Integer, nullable=False)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    modified_by = Column(Integer, nullable=False)
    modified_at = Column(DateTime, nullable=False)
    progression_description = Column(Text, nullable=True)


class IEMPucSubjects(Base):
    __tablename__ = 'iems_puc_subjects'

    sub_id = Column(Integer, primary_key=True, autoincrement=True)
    regno = Column(String(45), nullable=False)
    subject = Column(String(45), nullable=False)
    max_marks = Column(Integer, nullable=False)
    marks_obtained = Column(Integer, nullable=False)
    for_cal = Column(SmallInteger, default=0)
    status = Column(String(45), default='0')


class IEMReadmissionStudentCourses(Base):
    __tablename__ = 'iems_readmission_student_courses'

    ra_id = Column(Integer, primary_key=True, autoincrement=True)
    regno = Column(String(45), nullable=False)
    crs_code = Column(String(15), nullable=False)
    result_year = Column(Date, nullable=False)
    semester = Column(SmallInteger, nullable=False)
    program_id = Column(Integer, nullable=False)
    batch_id = Column(Integer, nullable=False)
    total_cia = Column(Float, nullable=False)
    see = Column(Float, nullable=False)
    cia_see = Column(Float, nullable=False)
    constant = Column(Float, nullable=False)
    constant_x_cia_see = Column(Float, nullable=False)
    grade = Column(String(2), nullable=True)
    grade_point = Column(String(2), nullable=True)
    credits = Column(Float, nullable=True)
    credits_earned = Column(Float, nullable=True)
    year_of_passing = Column(Integer, nullable=False)


class IEMRoleMenus(Base):
    __tablename__ = 'iems_role_menus'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)
    parent = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)
    show = Column(SmallInteger, nullable=False)
    status = Column(SmallInteger, nullable=False)
    org_id = Column(Integer, default=1)


class IEMSection(Base):
    __tablename__ = 'iems_section'

    id = Column(Integer, primary_key=True, autoincrement=True)
    section = Column(String(10), nullable=False)


class IEMSemester(Base):
    __tablename__ = 'iems_semester'

    semester_id = Column(Integer, primary_key=True, autoincrement=True)
    semester_code = Column(String(45), nullable=True)
    academic_batch_id = Column(Integer, nullable=True)
    academic_year_planned = Column(Integer, nullable=True)
    program_year = Column(Integer, nullable=True)
    semester = Column(Integer, nullable=True)
    semester_desc = Column(String(45), nullable=True)
    semester_flag = Column(String(45), nullable=True)
    semester_status = Column(String(45), nullable=True)
    branch_cycle = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=True)
    status = Column(Integer, nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    sem_min_credits = Column(Integer, nullable=True)
    sem_max_credits = Column(Integer, nullable=True)
    term_name = Column(String(50), nullable=True)
    semester_duration = Column(Integer, nullable=True)
    total_theory_courses = Column(Integer, nullable=True)
    total_practical_courses = Column(Integer, nullable=True)
    academic_start_year = Column(Integer, nullable=True)
    academic_end_year = Column(Integer, nullable=True)
    enroll_start_date = Column(DateTime, nullable=True)
    enroll_start_time = Column(String(50), nullable=False, default='00:00:00')
    enroll_end_date = Column(Date, nullable=False)
    enroll_end_time = Column(String(50), nullable=False, default='00:00:00')
    unit_id = Column(Integer, nullable=False, default=3)


class IEMSemTimeTable(Base):
    __tablename__ = 'iems_sem_time_table'

    id = Column(Integer, primary_key=True, nullable=False)
    result_year = Column(String(45), nullable=False)
    section = Column(String(10), nullable=False)
    term = Column(String(2), nullable=False)
    cycle = Column(String(45), nullable=True)
    type = Column(SmallInteger, default=0, nullable=False)
    batch_id = Column(Integer, nullable=True)
    t_type = Column(Integer, nullable=True)


class IEMSGPACGPA(Base):
    __tablename__ = 'iems_sgpa_cgpa'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(45), nullable=False)
    program_id = Column(Integer, nullable=False)
    sem = Column(Integer, nullable=False)
    sgpa = Column(Float, nullable=False)
    cgpa = Column(Float, nullable=False)
    result_year = Column(Date, nullable=False)
    consider = Column(SmallInteger, default=1, nullable=False)
    org_id = Column(Integer, nullable=False)


class IEMSGPACGPABck(Base):
    __tablename__ = 'iems_sgpa_cgpa_bck'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(45), nullable=False)
    program_id = Column(Integer, nullable=False)
    sem = Column(Integer, nullable=False)
    sgpa = Column(Float, nullable=False)
    cgpa = Column(Float, nullable=False)
    result_year = Column(Date, nullable=False)
    consider = Column(SmallInteger, default=1, nullable=False)
    org_id = Column(Integer, nullable=False)


class IEMSGPACGPA_Dup_Bck(Base):
    __tablename__ = 'iems_sgpa_cgpa_dup_bck'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(45), nullable=False)
    program_id = Column(Integer, nullable=False)
    sem = Column(Integer, nullable=False)
    sgpa = Column(Float, nullable=False)
    cgpa = Column(Float, nullable=False)
    result_year = Column(Date, nullable=False)
    consider = Column(SmallInteger, default=1, nullable=False)
    org_id = Column(Integer, nullable=False)


class IEMSGPACGPA_Dup_Bck1(Base):
    __tablename__ = 'iems_sgpa_cgpa_dup_bck1'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(45), nullable=False)
    program_id = Column(Integer, nullable=False)
    sem = Column(Integer, nullable=False)
    sgpa = Column(Float, nullable=False)
    cgpa = Column(Float, nullable=False)
    result_year = Column(Date, nullable=False)
    consider = Column(SmallInteger, default=1, nullable=False)
    org_id = Column(Integer, nullable=False)


class IEMStaffSecurity(Base):
    __tablename__ = 'iems_staff_security'

    id = Column(Integer, primary_key=True, nullable=False)
    function = Column(String(15), nullable=False)


class IEMStudents(Base):
    __tablename__ = 'iems_students'

    student_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    college_id = Column(String(45), nullable=True)
    regno = Column(String(45), unique=True, nullable=True)
    usno = Column(String(20), nullable=False)
    ref_usno = Column(String(20), nullable=True)
    old_usno = Column(String(20), nullable=True)
    name = Column(String(150), nullable=True)
    first_name = Column(String(45), nullable=True)
    middle_name = Column(String(45), nullable=True)
    last_name = Column(String(45), nullable=True)
    fathers_name = Column(String(45), nullable=True)
    mothers_name = Column(String(45), nullable=True)
    dob = Column(Date, nullable=True)
    gender = Column(String(1), nullable=True)  # Using String for char(1)
    email = Column(String(45), nullable=True)
    mobile = Column(String(12), nullable=True)  # Using String for char(12)
    doj = Column(Date, nullable=True)
    org_id = Column(Integer, nullable=False)
    department_id = Column(Integer, nullable=True)
    old_department_id = Column(Integer, nullable=True)
    program_id = Column(Integer, nullable=True)
    old_program_id = Column(Integer, nullable=True)
    academic_batch_id = Column(Integer, nullable=True)
    old_academic_batch_id = Column(Integer, nullable=True)
    current_semester = Column(Integer, nullable=True)
    section = Column(String(10), nullable=True)
    admission_year = Column(Integer, nullable=True)
    result_year = Column(Date, nullable=True)
    salt = Column(String(40), nullable=True)
    password = Column(String(80), nullable=True)
    father_password = Column(String(45), nullable=True)
    father_salt = Column(String(45), nullable=True)
    mother_password = Column(String(45), nullable=True)
    mother_salt = Column(String(45), nullable=True)
    guardian_password = Column(String(45), nullable=True)
    guardian_salt = Column(String(45), nullable=True)
    status = Column(SmallInteger, default=1)  # tinyint(1) unsigned
    profile_image = Column(String(45), default='no_image.png', nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    batch_cycle_id = Column(Integer, nullable=False)
    roll_number = Column(String(20), nullable=True)
    religion = Column(String(45), nullable=True)
    claimed_category = Column(String(45), nullable=True)
    is_physically_challenged = Column(SmallInteger, nullable=True)  # tinyint(2) unsigned
    pc_description_id = Column(Integer, nullable=True)
    caste = Column(String(100), nullable=True)
    hostel = Column(SmallInteger, nullable=True)  # tinyint(3) unsigned
    fathers_occupation = Column(String(65), nullable=True)
    fathers_income = Column(Integer, nullable=True)
    fathers_phone = Column(String(65), nullable=True)
    fathers_email = Column(String(100), nullable=True)
    mothers_phone = Column(String(65), nullable=True)
    mothers_email = Column(String(100), nullable=True)
    mothers_occupation = Column(String(65), nullable=True)
    mothers_income = Column(Integer, nullable=True)
    guardian_name = Column(String(120), nullable=True)
    guardian_phone = Column(String(20), nullable=True)
    guardian_email = Column(String(80), nullable=True)
    guardian_occupation = Column(String(128), nullable=True)
    guardian_income = Column(Integer, nullable=True)
    birth_place = Column(String(128), nullable=True)
    nationality = Column(String(100), nullable=True)
    emergency_person = Column(String(100), nullable=True)
    emergency_phone = Column(Integer, nullable=True)  # Assuming this can be a number
    admission_type = Column(Integer, default=1, nullable=True)
    admission_sub_type = Column(Integer, nullable=True)
    quota_type = Column(String(50), nullable=True)
    mother_tongue = Column(String(60), nullable=True)
    blood_group = Column(String(20), nullable=True)
    application_no = Column(String(45), nullable=True)
    rural_urban = Column(String(45), nullable=True)
    cet_comedk_no = Column(String(45), nullable=True)
    cet_comedk_rank = Column(Integer, nullable=True)
    transport = Column(String(45), nullable=True)
    allocated_category = Column(String(45), nullable=True)
    adhar_no = Column(String(45), nullable=True)
    pan_no = Column(String(45), nullable=True)
    remarks = Column(String(45), nullable=True)
    online_exam_otp = Column(Integer, nullable=True)
    app_profile_image = Column(String(255), nullable=True)


class IEMStudentsBck(Base):
    __tablename__ = 'iems_students_bck'

    student_id = Column(Integer, primary_key=True, nullable=False)
    college_id = Column(String(45), nullable=True)
    regno = Column(String(45), nullable=True)
    usno = Column(String(20), nullable=False)
    ref_usno = Column(String(20), nullable=True)
    old_usno = Column(String(20), nullable=True)
    name = Column(String(150), nullable=True)
    first_name = Column(String(45), nullable=True)
    middle_name = Column(String(45), nullable=True)
    last_name = Column(String(45), nullable=True)
    fathers_name = Column(String(45), nullable=True)
    mothers_name = Column(String(45), nullable=True)
    dob = Column(Date, nullable=True)
    gender = Column(String(1), nullable=True)
    email = Column(String(45), nullable=True)
    mobile = Column(String(12), nullable=True)
    doj = Column(Date, nullable=True)
    org_id = Column(Integer, nullable=False)
    department_id = Column(Integer, nullable=True)
    old_department_id = Column(Integer, nullable=True)
    program_id = Column(Integer, nullable=True)
    old_program_id = Column(Integer, nullable=True)
    academic_batch_id = Column(Integer, nullable=True)
    old_academic_batch_id = Column(Integer, nullable=True)
    current_semester = Column(Integer, nullable=True)
    section = Column(String(10), nullable=True)
    admission_year = Column(Integer, nullable=True)
    result_year = Column(Date, nullable=True)
    salt = Column(String(40), nullable=True)
    password = Column(String(80), nullable=True)
    father_password = Column(String(45), nullable=True)
    father_salt = Column(String(45), nullable=True)
    mother_password = Column(String(45), nullable=True)
    mother_salt = Column(String(45), nullable=True)
    guardian_password = Column(String(45), nullable=True)
    guardian_salt = Column(String(45), nullable=True)
    status = Column(Boolean, default=True, nullable=True)
    profile_image = Column(String(45), default='no_image.png', nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    batch_cycle_id = Column(Integer, nullable=False)
    roll_number = Column(String(20), nullable=True)
    religion = Column(String(45), nullable=True)
    claimed_category = Column(String(45), nullable=True)
    is_physically_challenged = Column(Integer, nullable=True)
    pc_description_id = Column(Integer, nullable=True)
    caste = Column(String(100), nullable=True)
    hostel = Column(Integer, nullable=True)
    fathers_occupation = Column(String(65), nullable=True)
    fathers_income = Column(Integer, nullable=True)
    fathers_phone = Column(String(65), nullable=True)
    fathers_email = Column(String(100), nullable=True)
    mothers_phone = Column(String(65), nullable=True)
    mothers_email = Column(String(100), nullable=True)
    mothers_occupation = Column(String(65), nullable=True)
    mothers_income = Column(Integer, nullable=True)
    guardian_name = Column(String(120), nullable=True)
    guardian_phone = Column(String(20), nullable=True)
    guardian_email = Column(String(80), nullable=True)
    guardian_occupation = Column(String(128), nullable=True)
    guardian_income = Column(Integer, nullable=True)
    birth_place = Column(String(128), nullable=True)
    nationality = Column(String(100), nullable=True)
    emergency_person = Column(String(100), nullable=True)
    emergency_phone = Column(Integer, nullable=True)
    admission_type = Column(Integer, default=1, nullable=True)
    admission_sub_type = Column(Integer, nullable=True)
    quota_type = Column(String(50), nullable=True)
    mother_tongue = Column(String(60), nullable=True)
    blood_group = Column(String(20), nullable=True)
    application_no = Column(String(45), nullable=True)
    rural_urban = Column(String(45), nullable=True)
    cet_comedk_no = Column(String(45), nullable=True)
    cet_comedk_rank = Column(Integer, nullable=True)
    transport = Column(String(45), nullable=True)
    allocated_category = Column(String(45), nullable=True)
    adhar_no = Column(String(45), nullable=True)
    nodal_officer = Column(String(80), nullable=True)
    special_category = Column(String(50), nullable=True)
    special_cat_flag = Column(Boolean, nullable=True)
    created_ip = Column(String(15), nullable=True)
    modified_ip = Column(String(15), nullable=True)
    unique_id = Column(String(20), nullable=True)


class IEMSTemplate(Base):
    __tablename__ = 'iems_template'

    template_id = Column(Integer, primary_key=True, nullable=False)
    dept_id = Column(Integer, nullable=True)
    program_id = Column(Integer, nullable=True)
    sem = Column(Integer, nullable=True)
    template_name = Column(Text, nullable=False)
    template_type = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=False)


class IemsTempExamStdCrs(Base):
    __tablename__ = 'iems_temp_exam_std_crs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hall_id = Column(Integer, nullable=True)
    date_session_id = Column(Integer, nullable=True)
    crs_code = Column(String(45), nullable=True)
    limit_value = Column(String(45), nullable=True)


class IEMSTempInSemExamStdCrs(Base):
    __tablename__ = 'iems_temp_in_sem_exam_std_crs'

    id = Column(Integer, primary_key=True, autoincrement=False)
    hall_id = Column(Integer, nullable=True)
    date_session_id = Column(Integer, nullable=True)
    crs_code = Column(String(45), nullable=True)
    limit_value = Column(String(45), nullable=True)


class IEMSTempStudentDetails(Base):
    __tablename__ = 'iems_temp_student_deatils'

    id = Column(Integer, primary_key=True, nullable=False)
    usno = Column(String(45), nullable=True)
    name = Column(String(45), nullable=True)
    email = Column(String(45), nullable=True)
    mobile = Column(String(45), nullable=True)


class IEMSTempStuHead(Base):
    __tablename__ = 'iems_temp_stu_head'

    pky = Column(Integer, primary_key=True, nullable=False)
    desc_t = Column(String(75), nullable=True)
    val_t = Column(String(75), nullable=True)
    usn = Column(String(30), primary_key=True, nullable=False)
    column_name = Column(String(100), primary_key=True, nullable=False)
    table_name = Column(String(100), primary_key=True, nullable=False)


class IEMSTimeTable(Base):
    __tablename__ = 'iems_time_table'

    time_table_id = Column(Integer, primary_key=True, nullable=False)
    crs_code = Column(String(45), nullable=False)
    start_time = Column(String(45), nullable=False)
    end_time = Column(String(45), nullable=False)
    sem_time_table_id = Column(Integer, nullable=True)
    crs_id = Column(Integer, nullable=True)
    time_table_set_id = Column(Integer, nullable=True)
    class_timing_id = Column(Integer, nullable=True)


class IEMSTimeTableSet(Base):
    __tablename__ = 'iems_time_table_set'

    time_table_set_id = Column(Integer, primary_key=True, nullable=False)
    tt_days_set_id = Column(Integer, nullable=True)
    days = Column(String(45), nullable=True)
    timing_set_id = Column(Integer, nullable=True)
    status = Column(SmallInteger, nullable=True)
    created_at = Column(DateTime, nullable=True)
    modified_at = Column(DateTime, nullable=True)


class IEMSTransitionalGrades(Base):
    __tablename__ = 'iems_transitional_grades'

    id = Column(Integer, primary_key=True, nullable=False)
    grades = Column(String(45), nullable=True)


class IEMSTtDaysSet(Base):
    __tablename__ = 'iems_tt_days_set'

    tt_days_set_id = Column(Integer, primary_key=True, nullable=False)
    day_set_name = Column(String(45), nullable=True)
    day_set_desc = Column(String(100), nullable=True)
    status = Column(SmallInteger, nullable=True)
    created_at = Column(DateTime, nullable=True)
    modified_at = Column(DateTime, nullable=True)


class IEMUniversity(Base):
    __tablename__ = 'iems_university'

    unv_id = Column(Integer, primary_key=True, nullable=False)
    unv_name = Column(String(500), nullable=False)
    unv_desc = Column(Text, nullable=False)
    status = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=False)
    modified_by = Column(Integer, nullable=False)
    created_date = Column(DateTime, nullable=False)
    modified_date = Column(DateTime, nullable=False)
    unv_code = Column(String(1), nullable=False)


# class IEMSUsers(Base):
#     __tablename__ = 'iems_users'

#     id = Column(Integer, primary_key=True, nullable=False)
#     ip_address = Column(VARBINARY(16), nullable=True)
#     username = Column(String(40), nullable=True)
#     password = Column(String(80), nullable=True)
#     salt = Column(String(40), nullable=True)
#     email = Column(String(50), nullable=False)
#     activation_code = Column(String(40), nullable=True)
#     forgotten_password_code = Column(String(40), nullable=True)
#     forgotten_password_time = Column(Integer, nullable=True)
#     remember_code = Column(String(40), nullable=True)
#     created_on = Column(Integer, nullable=True)
#     last_login = Column(Integer, nullable=True)
#     active = Column(Boolean, nullable=True)
#     title = Column(String(8), nullable=True)
#     first_name = Column(String(50), nullable=True)
#     last_name = Column(String(50), nullable=True)
#     org_id = Column(Integer, nullable=True)
#     user_type = Column(String(1), nullable=False)
#     user_dept_id = Column(Integer, nullable=True)
#     created_by = Column(Integer, nullable=True)
#     modified_by = Column(Integer, nullable=True)
#     create_date = Column(DateTime, nullable=True)
#     modify_date = Column(DateTime, nullable=True)
#     designation_id = Column(Integer, nullable=True)
#     status = Column(Boolean, default=True, nullable=False)
#     super_admin = Column(Boolean, default=False, nullable=False)
#     technical_admin = Column(Boolean, default=False, nullable=False)
#     mobile = Column(String(10), nullable=True)

class IEMSUsers(Base):
    __tablename__ = "iems_users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    ip_address = Column(VARBINARY(16), nullable=True)
    username = Column(String(40), unique=True, nullable=True)
    password = Column(String(80), nullable=True)
    salt = Column(String(40), nullable=True)
    email = Column(String(50), unique=True, nullable=False)

    activation_code = Column(String(40), nullable=True)
    forgotten_password_code = Column(String(40), nullable=True)
    forgotten_password_time = Column(Integer, nullable=True)
    remember_code = Column(String(40), nullable=True)

    created_on = Column(Integer, nullable=True)
    last_login = Column(Integer, nullable=True)
    failed_login_attempts = Column(Integer, nullable=True)

    is_locked = Column(Boolean, nullable=True)
    lockout_until = Column(DateTime, nullable=True)

    active = Column(Integer, nullable=True)

    title = Column(String(8), nullable=True)
    first_name = Column(String(50), nullable=True) 
    middle_name = Column(String(50), nullable=True) # Not present in the original table, but can be added if needed
    last_name = Column(String(50), nullable=True)

    org_id = Column(Integer, nullable=True)
    user_type = Column(String(1), nullable=False)
    user_dept_id = Column(Integer, nullable=True)

    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)

    create_date = Column(Date, nullable=True)
    modify_date = Column(Date, nullable=True)

    designation_id = Column(Integer, nullable=True)

    status = Column(Integer, nullable=False, default=1)
    super_admin = Column(Integer, nullable=False, default=0)
    technical_admin = Column(Integer, nullable=False, default=0)

    student_id = Column(Integer, nullable=True)
    mobile = Column(String(10), nullable=True)

    forgot_password_check = Column(Boolean, nullable=True)

    master_password = Column(Text, nullable=True)

    alertnative_email = Column(String(50), nullable=True)
    organization_name = Column(String(40), nullable=False, default="IonCUDOS")

    base_dept_id = Column(Integer, nullable=True)
    user_qualification = Column(String(50), nullable=True)
    responsibilities = Column(Text, nullable=True)

    faculty_mode = Column(Integer, nullable=False, default=1)
    indurtrial_experiance = Column(Integer, nullable=False, default=0)
    teach_experiance = Column(Integer, nullable=False, default=0)
    user_experience = Column(Float(8), nullable=True)

    faculty_type = Column(Integer, nullable=True)
    phd_from = Column(Text, nullable=True)
    superviser = Column(Text, nullable=True)

    phd_status = Column(Integer, nullable=True, default=59)
    registration_year = Column(Date, nullable=True)
    phd_topic = Column(Text, nullable=True)
    phd_status_data = Column(Text, nullable=True)
    phd_assessment_year = Column(Date, nullable=True)

    user_specialization = Column(Text, nullable=True)
    guidance_within_org = Column(Integer, nullable=True)
    guidance_outside_org = Column(Integer, nullable=True)
    research_interrest = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)

    DOB = Column(Date, nullable=True)
    present_address = Column(Text, nullable=True)
    permanent_address = Column(Text, nullable=True)
    user_website = Column(Text, nullable=True)

    emp_no = Column(Text, nullable=True)
    faculty_serving = Column(Integer, nullable=True)

    dpdp_flag = Column(Boolean, nullable=False, default=0)
    is_student = Column(Boolean, nullable=False, default=0)

    heighest_qualification = Column(Integer, nullable=True)
    university = Column(Text, nullable=True)

    year_of_joining = Column(Date, nullable=True)
    last_promotion = Column(Date, nullable=True)

    salary_pay = Column(DECIMAL(19, 2), nullable=False, default=0.00)

    resign_date = Column(Date, nullable=True)
    retirement_date = Column(Date, nullable=True)
    year_of_graduation = Column(Date, nullable=True)

    aadhar_number = Column(String(20), nullable=True)

    login_time = Column(DateTime, nullable=True)
    logout_time = Column(DateTime, nullable=True)
    login_failed = Column(DateTime, nullable=True)

    remarks = Column(Text, nullable=True)
    user_pic = Column(Text, nullable=True)
    blood_group = Column(Text, nullable=True)
    professional_bodies = Column(Text, nullable=True)

    prevent_log_history = Column(Integer, nullable=False, default=0)

    phd_url = Column(Text, nullable=True)

    recovery_qtn_id = Column(Integer, nullable=True)
    recovery_answer = Column(Text, nullable=True)

    fp_accessed = Column(Date, nullable=True)
    fp_security_attempts = Column(Boolean, nullable=True)

    curriculums = relationship("Curriculum", foreign_keys="Curriculum.crclm_owner", back_populates="owner")

    # Course-Instructor Mapping
    assigned_courses = relationship(
    "CudosMapCoursetoCourseInstructor",
    back_populates="instructor"
)


class IEMSUserCourseMgmt(Base):
    __tablename__ = 'iems_user_course_mgmt'

    user_course_id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    result_year = Column(String(45), nullable=True)
    department_id = Column(Integer, nullable=True)
    program_id = Column(Integer, nullable=True)
    academic_batch_id = Column(Integer, nullable=True)
    semester = Column(Integer, nullable=True)
    crs_id = Column(Integer, nullable=True)
    crs_code = Column(String(45), nullable=True)
    section = Column(String(45), nullable=True)
    process_start_date = Column(DateTime, nullable=True)
    process_end_date = Column(DateTime, nullable=True)
    status = Column(Boolean, default=False, nullable=False)
    sem_time_table_id = Column(Integer, nullable=True)
    course_owner = Column(Integer, default=0, nullable=False)


class IEMSUserDesignation(Base):
    __tablename__ = 'iems_user_designation'

    designation_id = Column(Integer, primary_key=True, nullable=False)
    designation_name = Column(String(40), nullable=False)
    designation_description = Column(String(100), nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(DateTime, nullable=True)
    modified_date = Column(DateTime, nullable=True)


class IEMSUserOrg(Base):
    __tablename__ = 'iems_user_org'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    org_id = Column(Integer, nullable=False)


class IEMSUserPermissions(Base):
    __tablename__ = 'iems_user_permissions'

    access_id = Column(Integer, primary_key=True, nullable=False)
    user_role_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)
    permission_id = Column(Integer, nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)
    org_id = Column(Integer, default=1, nullable=False)


class IEMSUserRoles(Base):
    __tablename__ = 'iems_user_roles'

    userrole_id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    role_id = Column(Integer, nullable=False)
    org_id = Column(Integer, default=1, nullable=True)


class IEMSUserRoleMaster(Base):
    __tablename__ = 'iems_user_role_master'

    user_role_id = Column(Integer, primary_key=True, nullable=False)
    user_role = Column(String(45), nullable=False)
    user_role_description = Column(String(225), nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)
    department_wise = Column(SmallInteger, default=0, nullable=False)
    core_role = Column(Boolean, default=False, nullable=False)


class IEMSUserRolePermissions(Base):
    __tablename__ = 'iems_user_role_permissions'

    access_id = Column(Integer, primary_key=True, nullable=False)
    user_role_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)
    permission_id = Column(Integer, nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)
    org_id = Column(Integer, default=1, nullable=False)


class IEMSUserStaffSecurity(Base):
    __tablename__ = 'iems_user_staff_security'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    function_id = Column(Integer, nullable=False)
    sub_code = Column(String(15), nullable=False)
    section = Column(String(2), nullable=False)
    status = Column(Boolean, default=True, nullable=False)


class Menus(Base):
    __tablename__ = 'menus'

    menu_id = Column(Integer, primary_key=True, nullable=False)
    menu_name = Column(String(45), nullable=True)
    parent = Column(SmallInteger, nullable=True)
    menu_level = Column(Integer, nullable=True)
    menu_url = Column(String(255), nullable=True)
    parent_class = Column(String(255), nullable=False)
    menu_class = Column(String(100), nullable=True)
    menu_icon = Column(String(100), nullable=True)
    menu_order = Column(Integer, nullable=True)
    show_menu = Column(Boolean, default=True, nullable=False)
    child = Column(Integer, nullable=True)
    status = Column(Boolean, default=True, nullable=False)


class OtherCourses(Base):
    __tablename__ = 'other_courses'

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(45), nullable=False)


class PhysicallyChallengedDescription(Base):
    __tablename__ = 'physically_challenged_description'

    pc_description_id = Column(Integer, primary_key=True, nullable=False)
    description = Column(String(100), nullable=True)
    status = Column(SmallInteger, nullable=True)
    org_id = Column(Integer, nullable=True)


class Religion(Base):
    __tablename__ = 'religion'

    religion_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(100), nullable=True)


class Roles(Base):
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True, nullable=False)
    role_name = Column(String(30), nullable=False)


class State(Base):
    __tablename__ = 'state'

    state_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(100), nullable=True)
    country_id = Column(Integer, nullable=True)


class TempImportStudentDetails(Base):
    __tablename__ = 'temp_import_student_details'

    id = Column(Integer, primary_key=True, nullable=False)
    Remarks = Column(Text, nullable=True)
    student_admission_id = Column(String(50), nullable=True)
    application_no = Column(String(50), nullable=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True)
    dob = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    email = Column(String(50), nullable=True)
    mother_tongue = Column(String(50), nullable=True)
    blood_group = Column(String(50), nullable=True)
    birth_place = Column(String(50), nullable=True)
    nationality = Column(String(50), nullable=True)
    religion = Column(String(50), nullable=True)
    caste = Column(String(50), nullable=True)
    emergency_person = Column(String(50), nullable=True)
    emergency_phone = Column(String(50), nullable=True)
    profile_image = Column(String(50), nullable=True)
    doj = Column(String(50), nullable=True)
    quota_type = Column(String(50), nullable=True)
    cet_comedk_no = Column(String(50), nullable=True)
    cet_comedk_rank = Column(String(50), nullable=True)
    batch_cycle_id = Column(String(50), nullable=True)
    section = Column(String(50), nullable=True)
    roll_no = Column(String(50), nullable=True)
    usno = Column(String(50), nullable=True)
    rural_urban = Column(String(50), nullable=True)
    claimed_category = Column(String(50), nullable=True)
    allocated_category = Column(String(50), nullable=True)
    hostel = Column(String(50), nullable=True)
    transport = Column(String(50), nullable=True)
    father_name = Column(String(50), nullable=True)
    fathers_occupation = Column(String(50), nullable=True)
    fathers_income = Column(String(50), nullable=True)
    fathers_phone = Column(String(50), nullable=True)
    fathers_email = Column(String(50), nullable=True)
    mother_name = Column(String(50), nullable=True)
    mothers_occupation = Column(String(50), nullable=True)
    mothers_income = Column(String(50), nullable=True)
    mothers_phone = Column(String(50), nullable=True)
    mothers_email = Column(String(50), nullable=True)
    guardian_name = Column(String(50), nullable=True)
    guardian_occupation = Column(String(50), nullable=True)
    guardian_income = Column(String(50), nullable=True)
    guardian_phone = Column(String(50), nullable=True)
    guardian_email = Column(String(50), nullable=True)
    sslc_board_university = Column(String(50), nullable=True)
    sslc_institution = Column(String(50), nullable=True)
    sslc_prev_regno = Column(String(50), nullable=True)
    sslc_total_marks = Column(String(50), nullable=True)
    sslc_marks_obtained = Column(String(50), nullable=True)
    sslc_percentage = Column(String(50), nullable=True)
    sslc_grade = Column(String(50), nullable=True)
    sslc_year_of_passing = Column(String(50), nullable=True)
    sslc_place_of_study = Column(String(50), nullable=True)
    sslc_state = Column(String(50), nullable=True)
    pu_board_university = Column(String(50), nullable=True)
    pu_institution = Column(String(50), nullable=True)
    pu_prev_regno = Column(String(50), nullable=True)
    pu_total_marks = Column(String(50), nullable=True)
    pu_marks_obtained = Column(String(50), nullable=True)
    pu_percentage = Column(String(50), nullable=True)
    pu_grade = Column(String(50), nullable=True)
    pu_year_of_passing = Column(String(50), nullable=True)
    pu_place_of_study = Column(String(50), nullable=True)
    pu_state = Column(String(50), nullable=True)
    dip_board_university = Column(String(50), nullable=True)
    dip_institution = Column(String(50), nullable=True)
    dip_prev_regno = Column(String(50), nullable=True)
    dip_total_marks = Column(String(50), nullable=True)
    dip_marks_obtained = Column(String(50), nullable=True)
    dip_percentage = Column(String(50), nullable=True)
    dip_grade = Column(String(50), nullable=True)
    dip_year_of_passing = Column(String(50), nullable=True)
    dip_place_of_study = Column(String(50), nullable=True)
    dip_state = Column(String(50), nullable=True)
    degree_board_university = Column(String(50), nullable=True)
    degree_institution = Column(String(50), nullable=True)
    degree_prev_regno = Column(String(50), nullable=True)
    degree_total_marks = Column(String(50), nullable=True)
    degree_marks_obtained = Column(String(50), nullable=True)
    degree_percentage = Column(String(50), nullable=True)
    degree_grade = Column(String(50), nullable=True)
    degree_year_of_passing = Column(String(50), nullable=True)
    degree_place_of_study = Column(String(50), nullable=True)
    degree_state = Column(String(50), nullable=True)
    permanent_address1 = Column(String(50), nullable=True)
    permanent_address2 = Column(String(50), nullable=True)
    permanent_street = Column(String(50), nullable=True)
    permanent_landmark = Column(String(50), nullable=True)
    permanent_city = Column(String(50), nullable=True)
    permanent_state = Column(String(50), nullable=True)
    permanent_country = Column(String(50), nullable=True)
    pincode = Column(String(50), nullable=True)
    permanent_phone = Column(String(50), nullable=True)
    correspondance_address = Column(String(50), nullable=True)
    correspondance_address2 = Column(String(50), nullable=True)
    correspondance_street = Column(String(50), nullable=True)
    correspondance_landmark = Column(String(50), nullable=True)
    correspondance_city = Column(String(50), nullable=True)
    correspondance_state = Column(String(50), nullable=True)
    correspondance_country = Column(String(50), nullable=True)
    correspondance_pincode = Column(String(50), nullable=True)
    correspondance_phone = Column(String(50), nullable=True)
    pc_description_id = Column(String(50), nullable=True)


class TempNonProgressionList(Base):
    __tablename__ = 'temp_non_progression_list'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(50), nullable=True)
    usno = Column(String(50), nullable=True)
    program_id = Column(String(45), nullable=True)
    batch_id = Column(String(45), nullable=True)
    result_year = Column(String(45), nullable=True)
    name = Column(String(255), nullable=True)


class TempProgressionList(Base):
    __tablename__ = 'temp_progression_list'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(50), nullable=True)
    usno = Column(String(50), nullable=True)
    program_id = Column(String(45), nullable=True)
    batch_id = Column(String(45), nullable=True)
    result_year = Column(String(45), nullable=True)
    name = Column(String(255), nullable=True)


class TimeTable(Base):
    __tablename__ = 'time_table'

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(45), nullable=False)
    start = Column(String(45), nullable=False)
    end = Column(String(45), nullable=False)
    sem_time_table_id = Column(Integer, nullable=True)
    crs_id = Column(Integer, nullable=True)


class TmpAttendance(Base):
    __tablename__ = 'tmp_attendance'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(500), nullable=True)
    crs_code = Column(String(500), nullable=True)
    result_year = Column(String(500), nullable=True)
    attendance = Column(String(500), nullable=True)
    attendance_percentage = Column(String(500), nullable=True)
    usno = Column(String(500), nullable=True)
    user_id = Column(Integer, nullable=True)
    remarks = Column(String(500), nullable=True)


class TmpBckAttendance(Base):
    __tablename__ = 'tmp_bck_attendance'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(500), nullable=True)
    crs_code = Column(String(500), nullable=True)
    result_year = Column(String(500), nullable=True)
    attendance = Column(String(500), nullable=True)
    usno = Column(String(500), nullable=True)
    std_crs_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    attendance_percentage = Column(String(500), nullable=True)


class TmpCasteUpdate(Base):
    __tablename__ = 'tmp_caste_update'

    id = Column(Integer, primary_key=True, nullable=False)
    usno = Column(String(100), nullable=True)
    religion = Column(String(100), nullable=True)
    caste = Column(String(100), nullable=True)
    claimed_category = Column(String(100), nullable=True)


class TmpCia(Base):
    __tablename__ = 'tmp_cia'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(500), nullable=True)
    crs_code = Column(String(500), nullable=True)
    result_year = Column(String(500), nullable=True)
    secured_marks = Column(String(500), nullable=True)
    usno = Column(String(500), nullable=True)
    user_id = Column(Integer, nullable=True)
    remarks = Column(String(500), nullable=True)


class TmpGcStore(Base):
    __tablename__ = 'tmp_gc_store'

    id = Column(Integer, primary_key=True, nullable=False)
    gc_code = Column(String(30), nullable=False)
    usno = Column(String(20), nullable=False)
    result_year = Column(Integer, nullable=False)  # Assuming date should be changed to Integer for year
    semester = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=False)
    regno = Column(String(20), nullable=True)
    remarks = Column(Text, nullable=True)


class TmpGenderUpdate(Base):
    __tablename__ = 'tmp_gender_update'

    id = Column(Integer, primary_key=True, nullable=False)
    usno = Column(String(100), nullable=True)
    gender = Column(String(100), nullable=True)


class TmpSee(Base):
    __tablename__ = 'tmp_see'

    tmp_id = Column(Integer, primary_key=True, nullable=False)
    std_crs_id = Column(Integer, nullable=True)
    org_id = Column(Integer, nullable=True)
    result_year = Column(String(20), nullable=True)
    crs_code = Column(String(20), nullable=True)
    event_type = Column(SmallInteger, nullable=True)
    regno = Column(String(50), nullable=True)
    usno = Column(String(50), nullable=True)
    v1 = Column(String(500), nullable=True)
    v2 = Column(String(500), nullable=True)
    v3 = Column(String(500), nullable=True)
    remarks = Column(String(500), nullable=True)
    user_id = Column(Integer, nullable=True)


class TmpStdCiaOccasion(Base):
    __tablename__ = 'tmp_std_cia_occasion'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(500), nullable=True)
    occasion_id = Column(Integer, nullable=True)
    crs_code = Column(String(500), nullable=True)
    cias = Column(String(500), nullable=True)
    secured_marks = Column(String(500), nullable=True)
    std_crs_id = Column(Integer, nullable=True)
    usno = Column(String(500), nullable=True)


class TmpStudents(Base):
    __tablename__ = 'tmp_students'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(500), nullable=True)
    rollnumber = Column(String(500), nullable=True)
    name = Column(String(500), nullable=True)
    section = Column(String(500), nullable=True)
    dept_id = Column(String(45), nullable=True)
    pgm_id = Column(String(45), nullable=True)
    batch_id = Column(String(45), nullable=True)
    usno = Column(String(500), nullable=True)


class TmpStudentsSection(Base):
    __tablename__ = 'tmp_students_section'

    id = Column(Integer, primary_key=True, nullable=False)
    usno = Column(String(500), nullable=True)
    section = Column(String(100), nullable=True)


class TmpStudentCourses(Base):
    __tablename__ = 'tmp_student_courses'

    id = Column(Integer, primary_key=True, nullable=False)
    regno = Column(String(500), nullable=True)
    usno = Column(String(500), nullable=True)
    name = Column(String(500), nullable=True)
    cie = Column(String(500), nullable=True)
    see = Column(String(500), nullable=True)
    cie_see = Column(String(500), nullable=True)
    grd = Column(String(500), nullable=True)
    grdpt = Column(String(500), nullable=True)
    col_code = Column(String(45), nullable=True)
    subcode = Column(String(500), nullable=True)
    sect = Column(String(500), nullable=True)
    crtearned = Column(String(500), nullable=True)
    see1 = Column(String(45), nullable=True)
    see2 = Column(String(45), nullable=True)
    see3 = Column(String(45), nullable=True)
    cie_elg = Column(String(45), nullable=True)
    dept_id = Column(String(45), nullable=True)
    pgm_id = Column(String(45), nullable=True)
    batch_id = Column(String(45), nullable=True)


class Weekdays(Base):
    __tablename__ = 'weekdays'

    id = Column(Integer, primary_key=True, nullable=False)
    week_days = Column(String(50), nullable=False, default='0')
    short_name = Column(String(10), nullable=False)
    days_in_number = Column(SmallInteger, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False)


class StudentCourse(Base):
    __tablename__ = 'iems_student_courses'

    std_crs_id = Column(Integer, primary_key=True)
    regno = Column(String(45))
    usno = Column(String(20))
    crs_code = Column(String(15))
    result_year = Column(Date)
    program_id = Column(Integer)
    batch_id = Column(Integer)
    batch_cycle_id = Column(SmallInteger)  # tinyint(1) mapped to SmallInteger
    org_id = Column(Integer)
    semester = Column(SmallInteger)  # tinyint(2) mapped to SmallInteger
    section = Column(String(10))  # char(10) mapped to String
    is_registered = Column(Integer)
    is_withdrawn = Column(Boolean)  # tinyint(1) mapped to Boolean
    is_drop = Column(Boolean)
    is_withheld = Column(Boolean)
    is_evaluated = Column(Boolean)
    is_sup = Column(Boolean)
    sup_type = Column(SmallInteger)  # tinyint(1) mapped to SmallInteger
    is_backlog = Column(Boolean)
    attendance = Column(Float)
    grace_attendance = Column(Float)
    grace_flag = Column(Boolean)
    attendance_approved = Column(Boolean)
    attendance_approved_by = Column(Integer)
    attendance_approved_date = Column(DateTime)
    remarks = Column(Text)
    total_cia = Column(Float)
    total_ise = Column(Float)
    total_mse = Column(Float)
    cia_approved = Column(Boolean)
    cia_approved_by = Column(Integer)
    cia_approved_date = Column(DateTime)
    attendance_eligibility = Column(String(1))  # char(1) mapped to String
    cia_eligibility = Column(String(1))
    nsar_eligibility = Column(String(1))
    mkp_flag = Column(Boolean)
    ftrk_flag = Column(Boolean)
    consider = Column(Boolean)
    viva_marks = Column(Float)
    viva_absentee = Column(Boolean)
    is_viva_finalized = Column(Boolean)
    tw_marks = Column(Float)
    tw_marks_actual = Column(Float)
    tw_absentee = Column(Boolean)
    is_tw_finalized = Column(Boolean)
    tw_eligibility = Column(String(1))
    tw_entered_by = Column(Integer)
    tw_entered_date = Column(DateTime)
    see1 = Column(Float)
    see2 = Column(Float)
    see3 = Column(Float)
    see = Column(Float)
    see_actual = Column(Float)
    is_see_consolidate = Column(Boolean)
    is_see_imported = Column(Boolean)
    cia_see = Column(Float)
    cia_see_actual = Column(Float)
    credits_earned = Column(Float)
    backlog_credit_hours = Column(Float)
    is_grade_evaluated = Column(Integer)
    grade = Column(String(2))
    grade_point = Column(String(2))
    grade_actual = Column(String(2))
    tw_credits_earned = Column(Float)
    tw_grade_evaluated = Column(Integer)
    tw_grade = Column(String(2))
    tw_grade_point = Column(String(2))
    tw_grade_actual = Column(String(2))
    is_rejected = Column(Boolean)
    crta = Column(Float)
    see_absentee = Column(Boolean)
    is_mal_practice = Column(Boolean)
    attendance_percentage = Column(Float)
    is_reeval = Column(Boolean)
    rsee1 = Column(Float)
    rsee2 = Column(Float)
    rsee3 = Column(Float)
    rsee4 = Column(Float)
    rsee5 = Column(Float)
    rsee = Column(Float)
    rsee_actual = Column(Float)
    is_challenge_reeval = Column(Integer)
    crsee1 = Column(Float)
    crsee2 = Column(Float)
    crsee3 = Column(Float)
    crsee4 = Column(Float)
    crsee5 = Column(Float)
    crsee = Column(Float)
    crsee_actual = Column(Float)
    updated_by = Column(Integer)
    updated_at = Column(DateTime)
    is_result_finalized = Column(SmallInteger)


class StudentAddressDetail(Base):
    __tablename__ = 'iems_student_address_detail'

    students_address_details_id = Column(Integer, primary_key=True, autoincrement=True)
    student_details_master_id = Column(Integer, ForeignKey('iems_students.student_id'), nullable=True)
    admission_no = Column(String(45), nullable=True)
    regno = Column(String(45), nullable=True)
    usno = Column(String(45), nullable=True)
    address_type = Column(String(45), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(45), nullable=True)
    district = Column(String(45), nullable=True)
    address_state = Column(String(45), nullable=True)
    postel_code = Column(String(45), nullable=True)
    country = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(Date, nullable=True)
    modify_date = Column(Date, nullable=True)
    status = Column(SmallInteger, nullable=True)
    phone = Column(String(10), nullable=True)
    address2 = Column(String(250), nullable=True)
    street = Column(String(45), nullable=True)
    landmark = Column(String(45), nullable=True)


class StudentCertificateDetail(Base):
    __tablename__ = 'iems_student_certificate_detail'

    student_certificate_details_id = Column(Integer, primary_key=True, autoincrement=True)
    student_details_master_id = Column(Integer, ForeignKey('iems_students.student_id'), nullable=True)
    admission_no = Column(String(45), nullable=False)
    certificate_type = Column(String(45), nullable=True)
    certificate_of = Column(String(45), nullable=True)
    certificate_path = Column(String(100), nullable=True)
    org_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    regno = Column(String(45), nullable=True)
    usno = Column(String(45), nullable=True)


class StudentEducationDetail(Base):
    __tablename__ = 'iems_student_education_detail'

    student_education_details_id = Column(Integer, primary_key=True, autoincrement=True)
    student_details_master_id = Column(Integer, ForeignKey('iems_students.student_id'), nullable=True)
    admission_no = Column(String(45), nullable=True)
    regno = Column(String(45), nullable=True)
    usno = Column(String(45), nullable=True)
    education_qualification = Column(String(45), nullable=True)
    board_university = Column(String(45), nullable=True)
    institution = Column(String(150), nullable=True)
    state = Column(String(45), nullable=True)
    prev_regno = Column(String(45), nullable=True)
    total_marks = Column(String(45), nullable=True)
    percentage = Column(Numeric(5, 2), nullable=True)
    grade = Column(String(45), nullable=True)
    year_of_passing = Column(String(45), nullable=True)
    status = Column(String(45), nullable=True)
    org_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)
    place_of_study = Column(String(45), nullable=True)
    marks_obtained = Column(String(45), nullable=True)
    result_type = Column(String(45), nullable=True)
    sub_percentage = Column(String(45), nullable=True)


class IEMStudentLabBatchAllocation(Base):
    __tablename__ = 'iems_student_lab_batch_allocation'

    # Table Columns
    std_lab_batch_id = Column(Integer, primary_key=True, autoincrement=True)
    result_year = Column(Date, nullable=True)
    regno = Column(String(45), nullable=True)
    dept_id = Column(Integer, nullable=True)
    pgm_id = Column(Integer, nullable=True)
    batch_id = Column(Integer, nullable=True)
    semester = Column(Integer, nullable=True)
    section = Column(String(10), nullable=True)
    crs_id = Column(Integer, nullable=True)
    crs_code = Column(String(100), nullable=True)
    lab_course_batch_id = Column(Integer, nullable=True)
    org_id = Column(Integer, nullable=True)
    status = Column(SmallInteger, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    is_all = Column(SmallInteger, default=0)


class IEMS_Bulk_Courses_Details(Base):
    __tablename__ = 'iems_bulk_courses_details'

    Remarks = Column(Text, nullable=True)
    course_id = Column(String(50), nullable=True)
    academic_year = Column(String(50), nullable=True)
    batch_cycle_id = Column(String(50), nullable=True)  # Changed to String(50)
    crs_code = Column(String(50), nullable=True)
    crs_title = Column(String(255), nullable=True)
    crs_order = Column(Integer, nullable=False)
    credit_based = Column(String(50), nullable=True)
    credit_hours = Column(Float, nullable=True)
    crs_type = Column(String(50), nullable=True)
    lab_course = Column(String(50), nullable=True)
    no_of_cia = Column(Integer, nullable=False)
    cia_max_marks = Column(Float, default=0)
    cia_min_marks = Column(Float, default=0)
    cia_weightage = Column(Integer, default=0)
    see_max_marks = Column(Float, default=0)
    see_min_marks = Column(Float, default=0)
    see_weightage = Column(Integer, default=0)
    total_classes = Column(Float, default=0)
    min_passing_marks = Column(Float, default=0)
    course_type_code = Column(String(50), nullable=True)
    result_year = Column(Date, nullable=False)
    dept_id = Column(Integer, nullable=False, default=0)
    pgm_id = Column(Integer, nullable=False, default=0)
    academic_batch_id = Column(Integer, nullable=False, default=0)
    semester = Column(Integer, nullable=False, default=0)
    user_id = Column(Integer, nullable=False, default=0)
    org_id = Column(Integer, nullable=False, default=0)

    # Define composite primary key (crs_code, crs_title)
    __table_args__ = (
        PrimaryKeyConstraint('crs_code', 'crs_title'),
    )


class IEMSProgressionRules(Base):
    __tablename__ = 'iems_progression_rules'

    # Define columns based on the table structure
    progression_rule_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    progression_rule = Column(String(200), nullable=True)
    progression_rule_desc = Column(String(500), nullable=True)
    fail_grades = Column(String(200), nullable=True)
    is_no_rule = Column(Integer, default=0, nullable=False)
    no_of_failed_credits = Column(String(5), nullable=True)
    no_of_previous_year_failed_crs = Column(String(5), nullable=True)
    percentage_of_credits_earned = Column(String(5), nullable=True)
    min_credits_earned = Column(String(5), nullable=True)
    no_of_fy_year_failed_crs = Column(String(5), nullable=True)
    no_of_sy_year_failed_crs = Column(String(5), nullable=True)
    no_of_ty_year_failed_crs = Column(String(5), nullable=True)
    no_of_overall_failed_crs = Column(String(5), nullable=True)
    min_cgpa = Column(String(5), nullable=True)
    min_sgpa = Column(String(5), nullable=True)
    status = Column(SmallInteger, default=1, nullable=False)
    org_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=False)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True)
    modify_date = Column(DateTime, nullable=True)


class IEMSVerticalProgressionProcessedData(Base):
    __tablename__ = 'iems_vertical_progression_processed_data'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(Integer, nullable=True)
    regno = Column(String(100), nullable=True)
    usno = Column(String(40), nullable=True)
    result_year = Column(Date, nullable=True)
    program_id = Column(Integer, nullable=True)
    batch_id = Column(Integer, nullable=True)
    semester = Column(SmallInteger, nullable=True)
    section = Column(String(10), nullable=True)
    batch_cycle_id = Column(Integer, nullable=True)
    progression_rule_id = Column(Integer, nullable=True)
    org_id = Column(Integer, nullable=True)


class TmpStdRegList(Base):
    __tablename__ = 'tmp_std_reg_list'

    application_no = Column(String(450), nullable=True)
    result_year = Column(String(450), nullable=True)
    usno = Column(String(450), nullable=True)
    section = Column(String(450), nullable=True)
    batch_cycle_code = Column(String(450), nullable=True)
    roll_number = Column(String(450), nullable=True)
    doj = Column(String(450), nullable=True)
    ref_usno = Column(String(450), nullable=True)
    first_name = Column(String(450), nullable=True)
    last_name = Column(String(450), nullable=True)
    gender = Column(String(450), nullable=True)
    dob = Column(String(450), nullable=True)
    mobile = Column(String(450), nullable=True)
    email = Column(String(450), nullable=True)
    fathers_name = Column(String(450), nullable=True)
    mothers_name = Column(String(450), nullable=True)
    user_id = Column(Integer, nullable=True)
    dept_id = Column(String(450), nullable=True)
    pgm_id = Column(String(450), nullable=True)
    academic_batch_id = Column(String(450), nullable=True)
    semester = Column(String(450), nullable=True)
    org_id = Column(String(450), nullable=True)
    remarks = Column(String(450), nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('application_no', 'usno', 'roll_number'),
    )


# SQLAlchemy Models for database tables
class Hostel(Base):
    __tablename__ = "hms_hostel"

    hms_hostel_id = Column(Integer, primary_key=True, index=True)
    erp_inst_id = Column(Integer,
                         ForeignKey('erp_institute.erp_inst_id'))  # Assuming this comes from session or context
    hms_name = Column(String)
    hms_type = Column(Integer, default=1)
    hms_cheif_warden_id = Column(Integer, ForeignKey('erp_users.erp_user_id'))
    hms_for = Column(String, default="BOYS")
    hms_start_year = Column(Integer)
    hms_total_occupancy = Column(Integer)
    hms_helpline_num = Column(String)
    hms_address_v1 = Column(String)
    hms_address_v2 = Column(String)
    hms_contact_num = Column(Integer)
    hms_pin_code = Column(Integer)
    hms_fax_num = Column(Integer)
    hms_city = Column(String)
    hms_state = Column(String)
    hms_country = Column(String)
    status = Column(Integer, default=1)


class HostelAssistantWarden(Base):
    __tablename__ = "hms_hostel_ast_warden"

    hostel_warden_id = Column(Integer, primary_key=True, index=True)
    hms_hostel_id = Column(Integer, ForeignKey('hms_hostel.hms_hostel_id'))
    hms_asist_warden_id = Column(Integer)


class HMSRooms(Base):
    __tablename__ = "hms_room"

    hms_room_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hms_room_unqkey = Column(String(80), nullable=True, comment='auto generated alpha numeric')
    hms_floor_id = Column(Integer, ForeignKey('hms_floor.hms_floor_id'), nullable=True)
    hms_wing_id = Column(Integer, ForeignKey('hms_wing.hms_wing_id'), nullable=True)
    hms_hostel_id = Column(Integer, ForeignKey('hms_hostel.hms_hostel_id'), nullable=True)
    erp_inst_id = Column(Integer, nullable=True)
    hms_room_code = Column(String(50), nullable=True)
    hms_room_name = Column(String(255), nullable=True)
    hms_room_num_of_beds = Column(Integer, nullable=True)
    hms_rc_id = Column(Integer, ForeignKey('hms_room_category.hms_rc_id'), nullable=True)
    hms_rt_id = Column(Integer, ForeignKey('hms_room_type.hms_rt_id'), nullable=True)
    created_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    created_date = Column(TIMESTAMP, default=func.current_timestamp(), nullable=False)
    modified_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    modified_date = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp(),
                           nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)


class HMSRoomCategory(Base):
    __tablename__ = "hms_room_category"

    hms_rc_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hms_room_category_unqkey = Column(String(80), nullable=True, comment='auto generated alpha numeric')
    erp_inst_id = Column(Integer, ForeignKey('erp_institute.erp_inst_id'), nullable=True)
    hms_hostel_id = Column(Integer, ForeignKey('hms_hostel.hms_hostel_id'), nullable=True)
    hms_rc_name = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    created_date = Column(TIMESTAMP, default=func.current_timestamp(), nullable=False)
    modified_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    modified_date = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp(),
                           nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)


class HMSRoomCategoryBedType(Base):
    __tablename__ = "hms_room_category_bed_type"

    hms_rcbt_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hms_rcbt_unqkey = Column(String(80), nullable=True, comment='auto generated alpha numeric')
    hms_rc_id = Column(Integer, ForeignKey('hms_room_category.hms_rc_id'), nullable=True)
    hms_rcbt_beds = Column(Integer, nullable=True)
    hms_hostel_id = Column(Integer, nullable=True)
    erp_inst_id = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    created_date = Column(TIMESTAMP, default=func.current_timestamp(), nullable=False)
    modified_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    modified_date = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp(),
                           nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)


class HMSRoomType(Base):
    __tablename__ = "hms_room_type"

    hms_rt_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hms_room_type_unqkey = Column(String(80), nullable=True, comment='auto generated alpha numeric')
    hms_rt_name = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    created_date = Column(TIMESTAMP, default=func.current_timestamp(), nullable=False)
    modified_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    modified_date = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp(),
                           nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)


class LoginStatusEnum(str, enum.Enum):
    yes = 'yes'
    no = 'no'


class UserStatusEnum(int, enum.Enum):
    active = 1
    inactive = 0


class ErpUser(Base):
    __tablename__ = 'erp_users'

    erp_user_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    erp_users_unqkey = Column(String(80), nullable=True)
    title = Column(String(15), nullable=True)
    first_name = Column(String(50), nullable=True)
    middle_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    full_name = Column(String(150), nullable=True)
    email_id = Column(String(50), nullable=True)
    alternative_email_id = Column(String(50), nullable=True)
    contact = Column(String(45), nullable=True)
    username = Column(String(40), nullable=True)
    password = Column(String(80), nullable=True)
    salt = Column(String(40), nullable=True)
    login_status = Column(Enum(LoginStatusEnum), default=LoginStatusEnum.no, nullable=False)
    current_login = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    logout_time = Column(DateTime, nullable=True)
    user_active = Column(SmallInteger, default=1, nullable=False)  # Tinyint(1) -> SmallInteger
    rbac_custom_permission = Column(SmallInteger, default=0, nullable=False)
    created_by = Column(Integer, nullable=True)
    create_date = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    modified_by = Column(Integer, nullable=True)
    modify_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(),
                         nullable=False)
    deleted_date = Column(TIMESTAMP, nullable=True)
    status = Column(SmallInteger, default=1, nullable=False)  # Tinyint(1) -> SmallInteger


class ErpInstitute(Base):
    __tablename__ = 'erp_institute'

    erp_inst_id = Column(Integer, primary_key=True, index=True)
    erp_inst_unqkey = Column(String(80), nullable=True)
    erp_inst_society_name = Column(String(255), nullable=True)
    erp_inst_name = Column(String(255), nullable=True)
    erp_inst_code = Column(String(255), nullable=True)
    erp_inst_type_id = Column(Integer, ForeignKey('erp_master_type_details.erp_mt_details_id'), nullable=True)
    erp_inst_parent_id = Column(SmallInteger, default=0)
    created_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    created_date = Column(TIMESTAMP, default=func.current_timestamp(), nullable=False)
    modified_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    modified_date = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp(),
                           nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)

    # Relationships
    # erp_inst_type = relationship("ErpMasterTypeDetails", back_populates="institutes")
    created_user = relationship("ErpUser", foreign_keys=[created_by])
    modified_user = relationship("ErpUser", foreign_keys=[modified_by])


class ErpMasterTypeDetails(Base):
    __tablename__ = 'erp_master_type_details'

    erp_mt_details_id = Column(Integer, primary_key=True, index=True)
    erp_mt_details_unqkey = Column(String(80), nullable=True)
    erp_master_type_id = Column(Integer, ForeignKey('erp_master_type.erp_master_type_id'), nullable=True)
    erp_mt_details_name = Column(String(100), nullable=False)
    erp_master_type_details_alias_name = Column(String(100), nullable=True)
    created_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    created_date = Column(TIMESTAMP, default=func.current_timestamp(), nullable=False)
    modified_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    modified_date = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp(),
                           nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)

    # Relationships
    # erp_master_type = relationship("ErpMasterType", back_populates="details")
    created_user = relationship("ErpUser", foreign_keys=[created_by])
    modified_user = relationship("ErpUser", foreign_keys=[modified_by])


class ErpMasterType(Base):
    __tablename__ = 'erp_master_type'

    erp_master_type_id = Column(Integer, primary_key=True, index=True)
    erp_master_type_unqkey = Column(String(80), nullable=True)
    erp_master_type_name = Column(String(100), nullable=False)
    erp_master_type_alias_name = Column(String(100), nullable=True)
    status = Column(SmallInteger, default=1, nullable=False)


class MasterType(Base):
    __tablename__ = 'cudos_master_type'

    master_type_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    master_type_name = Column(String(100), nullable=False)
    master_type_alias_name = Column(String(100), nullable=True)



class MasterTypeDetails(Base):
    __tablename__ = 'cudos_master_type_details'

    mt_details_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    master_type_id = Column(Integer, ForeignKey('cudos_master_type.master_type_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    mt_details_name = Column(String(100), nullable=False)
    org_type = Column(Integer, nullable=True)
    parent_id = Column(Integer, default=0)
    master_type_details_alias_name = Column(String(100), nullable=True)
    mt_details_name_desc = Column(String(500), nullable=True)
    mtd_status = Column(SmallInteger, default=1, nullable=False)
    created_by = Column(Integer, nullable=True)
    created_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Aliases for Lab Category Compatibility
    lab_cat_id = synonym("mt_details_id")
    lab_cat_name = synonym("mt_details_name")
    lab_cat_description = synonym("mt_details_name_desc")
    status = synonym("mtd_status")


class HMSWing(Base):
    __tablename__ = "hms_wing"

    hms_wing_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    erp_inst_id = Column(Integer,
                         ForeignKey('erp_institute.erp_inst_id'))  # Assuming this comes from session or context
    hms_hostel_id = Column(Integer, ForeignKey('hms_hostel.hms_hostel_id'))
    hms_wing_name = Column(String(255), nullable=False)
    hms_wing_num_of_floors = Column(Integer, nullable=False)
    hms_cheif_warden_id = Column(Integer, ForeignKey('erp_users.erp_user_id'))
    hms_asist_warden_id = Column(Integer, nullable=True)
    status = Column(SmallInteger, nullable=False, default=1)


class HMSFloor(Base):
    __tablename__ = "hms_floor"

    hms_floor_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hms_hostel_id = Column(Integer, nullable=False)
    hms_wing_id = Column(Integer, ForeignKey('hms_wing.hms_wing_id'), nullable=False)
    hms_floor_name = Column(String(255), nullable=False)


class HMSAmenity(Base):
    __tablename__ = "hms_amenity"

    hms_amenity_id = Column(Integer, primary_key=True, autoincrement=True)
    hms_amenity_unqkey = Column(String(80))
    erp_inst_id = Column(Integer)
    hms_hostel_id = Column(Integer, ForeignKey("hms_hostel.hms_hostel_id"))
    hms_amenity_name = Column(String(255))
    hms_amenity_type = Column(Enum("FREE", "PAID"), default="FREE")
    status = Column(SmallInteger, nullable=False, default=1)


class HMSRoomCategoryAmenity(Base):
    __tablename__ = "hms_room_category_amenity"

    hms_rca_id = Column(Integer, primary_key=True, autoincrement=True)
    hms_rca_unqkey = Column(String(80), unique=True, comment="auto generated alpha numeric")
    hms_rc_id = Column(Integer, ForeignKey("hms_room_category.hms_rc_id"), nullable=True)
    hms_amenity_id = Column(Integer, ForeignKey("hms_amenity.hms_amenity_id"), nullable=True)
    erp_inst_id = Column(Integer, nullable=True)
    hms_hostel_id = Column(Integer, nullable=True)
    status = Column(SmallInteger, nullable=False, default=1)


class HostelTariff(Base):
    __tablename__ = "hms_room_tariff_master"

    hms_rtm_id = Column(Integer, primary_key=True, index=True)
    hms_rtm_unqkey = Column(String(80), nullable=True)
    hms_rcbt_id = Column(Integer, nullable=True)
    hms_tariff_costs = Column(Integer, nullable=True)
    hms_tariff_comments = Column(String(100), nullable=True)
    hms_additional_costs = Column(Integer, nullable=True)
    hms_additional_comments = Column(String(100), nullable=True)
    hms_academic_year = Column(String(50), nullable=True)
    hms_admission_year = Column(String(50), nullable=True)
    hms_tariff_start_date = Column(Date, nullable=True)
    hms_tariff_start_end = Column(Date, nullable=True)
    hms_tariff_status = Column(Integer, default=1)
    hms_hostel_id = Column(Integer, nullable=True)
    erp_inst_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_date = Column(Text, nullable=False)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Text, nullable=False)
    status = Column(Integer, default=1)


# admission
class StudentRoomAllotment(Base):
    __tablename__ = 'hms_student_room_allotment'
    hms_sra_id = Column(Integer, primary_key=True, index=True)
    hms_sra_unqkey = Column(String(80), nullable=True)
    erp_student_id = Column(Integer, ForeignKey("erp_student.erp_student_id"), nullable=True)
    hms_room_id = Column(Integer, ForeignKey('hms_room.hms_room_id'), nullable=True)
    hms_floor_id = Column(Integer, ForeignKey('hms_floor.hms_floor_id'), nullable=True)
    hms_wing_id = Column(Integer, ForeignKey('hms_wing.hms_wing_id'), nullable=True)
    hms_hostel_id = Column(Integer, ForeignKey('hms_hostel.hms_hostel_id'), nullable=True)
    erp_inst_id = Column(Integer, nullable=True)
    hms_stud_room_status = Column(Integer, default=1)
    hms_stud_room_remarks = Column(String(500), nullable=True)
    created_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    created_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    modified_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    modified_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    status = Column(Integer, default=1)


class Student(Base):
    __tablename__ = "erp_student"
    erp_student_id = Column(Integer, primary_key=True, index=True)
    erp_student_unqkey = Column(String(80), nullable=True)
    first_name = Column(String(50), nullable=True)
    erp_dept_id = Column(Integer, ForeignKey('erp_department.erp_dept_id'))
    title = Column(String, index=True)
    erp_student_usn = Column(String)
    full_name = Column(String)
    student_opted_hostel = Column(Integer)
    erp_crclm_id = Column(Integer)

    @property
    def full_name_usn(self):
        return f"{self.erp_student_usn} - {self.full_name if self.full_name else ''}"  # type: ignore


class Routes(Base):
    __tablename__ = "tms_route"
    tms_route_id = Column(Integer, primary_key=True, index=True)
    tms_route_unqkey = Column(String(80), nullable=True)
    erp_inst_id = Column(Integer, nullable=True)
    tms_route_name = Column(String(255), nullable=True)
    tms_route_start_name = Column(String(255), nullable=True)
    tms_route_end_name = Column(String(255), nullable=True)
    tms_route_start_time = Column(Time, nullable=True)
    tms_route_end_time = Column(Time, nullable=True)
    tms_route_boarding_flag = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    created_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    modified_by = Column(Integer, ForeignKey('erp_users.erp_user_id'), nullable=True)
    modified_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    status = Column(Integer, default=1)


class RouteVehicalEmployee:
    __tablename__ = "tms_route_vehicle_employee"
    tms_ve_id = Column(Integer, primary_key=True, index=True)
    tms_ve_unqkey = Column(String(80), nullable=True, comment="auto generated alpha numeric")
    tms_vehicle_id = Column(Integer, nullable=True)
    tms_route_id = Column(Integer, ForeignKey("tms_route.tms_route_id"), nullable=True)
    erp_inst_id = Column(Integer, nullable=True)
    tms_vehicle_driver_id = Column(Integer, nullable=True)
    tms_vehicle_driver_number = Column(Integer, nullable=True)
    tms_vehicle_cleaner_id = Column(Integer, nullable=True)
    tms_vehicle_cleaner_number = Column(Integer, nullable=True)
    tms_vehicle_helper_id = Column(Integer, nullable=True)
    tms_vehicle_helper_number = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    status = Column(Integer, default=1)


class ErpDepartment(Base):
    __tablename__ = 'erp_department'

    erp_dept_id = Column(Integer, primary_key=True, index=True)
    erp_dept_name = Column(String)
    # Add other columns as per your model


class ErpCurriculum(Base):
    __tablename__ = 'erp_curriculum'
    erp_crclm_id = Column(Integer, primary_key=True, index=True)
    erp_crclm_unqkey = Column(String(80), nullable=True, comment="auto generated alpha numeric")
    erp_crclm_name = Column(String(100), nullable=True)
    erp_crclm_start_year = Column(Integer, nullable=True)
    erp_crclm_end_year = Column(Integer, nullable=True)
    total_credits = Column(Float, nullable=True)
    total_terms = Column(Integer, nullable=True)
    erp_pgm_id = Column(Integer, nullable=True)
    erp_dept_id = Column(Integer, nullable=True)
    erp_school_id = Column(Integer, nullable=True)
    erp_inst_id = Column(Integer, nullable=True)
    create_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    status = Column(Integer, default=1)


class StudentPayment(Base):
    __tablename__ = 'hms_student_payment'

    hms_sp_id = Column(Integer, primary_key=True, index=True)
    hms_sp_unqkey = Column(String(80), nullable=True, comment="auto generated alpha numeric")
    erp_student_id = Column(Integer)
    hms_hostel_id = Column(Integer)
    hms_wing_id = Column(Integer)
    hms_floor_id = Column(Integer)
    hms_room_id = Column(Integer)
    hms_student_hostel_fee = Column(Integer)
    hms_student_mess_fee = Column(Integer)
    status = Column(Integer)
    erp_inst_id = Column(Integer)
    hms_sra_id = Column(Integer, ForeignKey('hms_student_room_allotment.hms_sra_id'))

    # Relationship with StudentRoomAllotment
    room_allotment = relationship("StudentRoomAllotment", backref="student_payment")


# class CudosMapLevelWeightage(Base):
#     __tablename__ = "cudos_map_level_weightage"

#     mlw_id = Column(Integer, primary_key=True, autoincrement=True)
#     map_level_name = Column(String(100), nullable=True)
#     map_level_name_alias = Column(String(100), nullable=True)
#     map_level_short_form = Column(String(10), nullable=True)
#     map_level = Column(Integer, nullable=True)
#     map_level_weightage = Column(Float(8, 2), nullable=True)
#     status = Column(SmallInteger, default=0)
#     created_by = Column(Integer, nullable=True)
#     created_date = Column(Date, nullable=True)
#     modified_by = Column(Integer, nullable=True)
#     modified_date = Column(Date, nullable=True)

class BloomLevel(Base):
    __tablename__ = 'cudos_bloom_level'

    bloom_id = Column(Integer, primary_key=True, autoincrement=True)
    bld_id = Column(Integer, nullable=False)
    level = Column(String(50), nullable=False)
    learning = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    bloom_actionverbs = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(DateTime, default=func.current_timestamp())
    modified_date = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class BloomDomain(Base):
    __tablename__ = 'cudos_bloom_domain'

    bld_id = Column(Integer, primary_key=True, autoincrement=True)
    bld_name = Column(String(100), nullable=False)
    bld_acronym = Column(String(50), nullable=False)
    bld_description = Column(Text, nullable=True)
    status = Column(Integer, default=1)
    bld_code = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date = Column(DateTime, default=func.current_timestamp())
    modify_date = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


# Backward-compatible alias used by older bloom level code.
CudosBloomDomain = BloomDomain


class CudosDeliveryMethod(Base):
    __tablename__ = 'cudos_delivery_method'

    delivery_mtd_id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_mtd_name = Column(String(800), nullable=False)
    delivery_mtd_desc = Column(String(2000))
    status = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer)
    created_date = Column(Date)
    modified_by = Column(Integer)
    modified_date = Column(Date)


class CudosPoPeoMap(Base):
    __tablename__ = 'cudos_po_peo_map'

    pp_id = Column(Integer, primary_key=True, autoincrement=True)
    peo_id = Column(Integer, nullable=False)
    po_id = Column(Integer, nullable=False)
    academic_batch_id = Column(Integer, nullable=False)
    map_level = Column(String(15), nullable=True)
    justification = Column(Text, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Date, nullable=True, default=func.current_date(), onupdate=func.current_date())
    created_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True, default=func.current_date())


class CudosTopic(Base):
    __tablename__ = 'cudos_topic'
    __table_args__ = {"extend_existing": True}

    topic_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_code = Column(String(10), nullable=True)
    topic_title = Column(String(500), nullable=False)
    t_unit_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    topic_content = Column(Text, nullable=True)
    topic_hrs = Column(String(8), nullable=True)
    num_of_sessions = Column(Float, nullable=True)
    marks_expt = Column(Float, nullable=True)
    correlation_with_theory = Column(String(200), nullable=True)
    conduction_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, nullable=True)
    category_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    academic_batch_id = Column(Integer, nullable=False)
    semester_id = Column(Integer, nullable=False)
    crs_id = Column(Integer, nullable=False)
    state_id = Column(Integer, nullable=True, default=1)
    created_by = Column(Integer, nullable=False)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=False)
    modified_date = Column(Date, nullable=True)
    import_ref_topic_id = Column(MEDIUMINT(unsigned=True), nullable=True)


class CudosTopicDeliveryMethod(Base):
    __tablename__ = 'cudos_topic_delivery_method'

    topic_dm_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    topic_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    delivery_mtd_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)


class CudosTlo(Base):
    __tablename__ = 'cudos_tlo'

    tlo_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    tlo_code = Column(String(20), nullable=True)
    tlo_statement = Column(Text, nullable=True)
    academic_batch_id = Column(Integer, nullable=False)
    semester_id = Column(Integer, nullable=False)
    crs_id = Column(Integer, nullable=False)
    topic_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    bloom_level = Column(String(100), nullable=True)
    delivery_method = Column(String(255), nullable=True)
    delivery_approach = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)
    state_id = Column(Integer, nullable=True, default=1)


class CudosTloCloMap(Base):
    __tablename__ = 'cudos_tlo_clo_map'

    tlo_map_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    tlo_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    clo_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    outcome_element = Column(MEDIUMINT(unsigned=True), nullable=True)
    pi = Column(MEDIUMINT(unsigned=True), nullable=True)
    pi_codes = Column(String(10), nullable=True)
    justification = Column(Text, nullable=True)
    academic_batch_id = Column(Integer, nullable=False)
    semester_id = Column(Integer, nullable=True)
    crs_id = Column(Integer, nullable=False)
    topic_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)


class CudosTopicLessonSchedule(Base):
    __tablename__ = 'cudos_topic_lesson_schedule'

    lesson_schedule_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    portion_ref = Column(String(8), nullable=True)
    portion_per_hour = Column(String(2000), nullable=False)
    academic_batch_id = Column(Integer, nullable=False)
    semester_id = Column(Integer, nullable=True)
    crs_id = Column(Integer, nullable=False)
    topic_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)
    conduction_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, nullable=True)


class CudosAssessmentMethod(Base):
    __tablename__ = 'cudos_assessment_methods'

    assess_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    assess_name = Column(String(500), nullable=True)
    bloom_id = Column(MEDIUMINT(unsigned=True), nullable=False)


class CudosTopicQuestion(Base):
    __tablename__ = 'cudos_topic_question'

    question_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    review_question = Column(Text, nullable=True)
    assignment_question = Column(Text, nullable=True)
    academic_batch_id = Column(Integer, nullable=False)
    semester_id = Column(Integer, nullable=False)
    crs_id = Column(Integer, nullable=False)
    topic_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    tlo_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    bloom_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    pi_codes = Column(String(10), nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)
    que_id = Column(String(20), nullable=True)


class CudosMapLevelWeightage(Base):
    __tablename__ = 'cudos_map_level_weightage'

    mlw_id = Column(Integer, primary_key=True, autoincrement=True)
    map_level_name = Column(String(100), nullable=True)
    map_level_name_alias = Column(String(100), nullable=True)
    map_level_short_form = Column(String(10), nullable=True)
    map_level = Column(Integer, nullable=True)
    map_level_weightage = Column(Float, nullable=True)
    status = Column(Integer, default=0)
    created_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Date, nullable=True)


class CUDOSBoS(Base):
    __tablename__ = "cudos_bos"

    bos_id = Column(Integer, primary_key=True, autoincrement=True)
    bos_user_id = Column(Integer, nullable=False)
    bos_dept_id = Column(Integer, nullable=False)

    create_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)

    create_date = Column(Date, nullable=True)
    modify_date = Column(Date, nullable=True)


# class AccreditationType(Base):
#     __tablename__ = "cudos_accreditation_type"

#     atype_id = Column(Integer, primary_key=True)
#     atype_name = Column(String(100), nullable=False)
#     atype_description = Column(String(2000), nullable=False)
#     entity_id = Column(Integer, nullable=False)
#     created_by = Column(Integer)
#     modified_by = Column(Integer)
#     created_date = Column(Date)
#     modified_date = Column(Date)

# from app.db.models import Base
# class PO(Base):
#     __tablename__ = "cudos_po"

#     po_id = Column(Integer, primary_key=True)
#     po_code = Column(String(10), nullable=False)
#     po_reference = Column(String(10))
#     po_statement = Column(String(2000), nullable=False)

#     atype_id = Column(Integer, ForeignKey("cudos_accreditation_type.atype_id"))
#     po_type_id = Column(Integer, ForeignKey("cudos_po_type.po_type_id"))

#     crclm_id = Column(Integer, nullable=False)
#     created_by = Column(Integer)
#     create_date = Column(Date)


class IEMSProgramMode(Base):
    __tablename__ = 'iems_program_mode'

    prg_mode_id = Column(Integer, primary_key=True, autoincrement=True)
    prg_mode_name = Column(String(50), nullable=False)
    prg_mode_desc = Column(String(100), nullable=False)
    prg_mode_code = Column(String(50), nullable=False)
    status = Column(Integer, default=1)


class CudosProgramKnowledgeProfile(Base):
    __tablename__ = "cudos_pgm_knowledge_profiles"

    pkp_id = Column(Integer, primary_key=True, index=True)
    pgm_id = Column(Integer, ForeignKey("iems_program.pgm_id", ondelete="CASCADE"))
    pkp_attr_code = Column(String(10), nullable=False)
    pkp_attr_description = Column(String(5000), nullable=False)

    created_by = Column(Integer, ForeignKey("iems_users.id"), nullable=True)
    modified_by = Column(Integer, ForeignKey("iems_users.id"), nullable=True)

    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)


class AccreditationType(Base):
    __tablename__ = "cudos_accreditation_type"

    atype_id = Column(Integer, primary_key=True, autoincrement=True)
    atype_name = Column(String(100), nullable=False)
    atype_description = Column(String(2000), nullable=False)
    entity_id = Column(Integer, nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(DateTime, nullable=True, default=func.now())
    modified_date = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())

    details = relationship("AccreditationTypeDetails", back_populates="accreditation_type",
                           cascade="all, delete-orphan")


class AccreditationTypeDetails(Base):
    __tablename__ = 'cudos_accreditation_type_details'

    atype_details_id = Column(MEDIUMINT(8), primary_key=True, autoincrement=True)
    atype_id = Column(Integer, ForeignKey("cudos_accreditation_type.atype_id"), nullable=False)
    atype_details_name = Column(String(100), nullable=False)
    atype_details_description = Column(String(2000), nullable=False)
    po_type_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    po_code = Column(String(10), nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)

    accreditation_type = relationship("AccreditationType", back_populates="details")


class PO(Base):
    __tablename__ = "cudos_po"

    po_id = Column(Integer, primary_key=True, autoincrement=True)
    po_code = Column(String(10), nullable=False)
    po_reference = Column(String(10), nullable=True)
    pso_flag = Column(Boolean, default=False)
    po_statement = Column(String(2000), nullable=False)
    po_type_id = Column(Integer, nullable=True)
    # link to academic batch (replaces legacy crclm_id)
    academic_batch_id = Column(Integer, nullable=True)
    state_id = Column(Integer, nullable=True)
    create_date = Column(DateTime, nullable=True, default=func.now())
    created_by = Column(Integer, nullable=True)
    modify_date = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    modified_by = Column(Integer, nullable=True)
    po_minthreshhold = Column(Integer, nullable=True)
    po_studentthreshhold = Column(Integer, nullable=True)
    justify = Column(String(1000), nullable=True)
    import_ref_po_id = Column(Integer, nullable=True)
    direct_attainment = Column(Integer, nullable=True)
    indirect_attainment = Column(Integer, nullable=True)
    extra_curricular = Column(Integer, nullable=True)
    # Added academic_batch_id
    academic_batch_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    # Removed atype_id to match existing database schema
    # atype_id = Column(Integer, ForeignKey("cudos_accreditation_type.atype_id"), nullable=True)

    # Intentionally adding atype_id to match UI requirement to link PO to AccreditationType
    # This assumes the column exists or will be added to the table
    # atype_id = Column(Integer, ForeignKey("cudos_accreditation_type.atype_id"), nullable=True)

    # accreditation_type = relationship("AccreditationType", back_populates="pos")


class CurriculumDeliveryMethod(Base):
    __tablename__ = 'cudos_map_crclm_deliverymethod'

    crclm_dm_id = Column(Integer, primary_key=True, autoincrement=True)
    academic_batch_id = Column(Integer, nullable=True)
    crs_id = Column(Integer, nullable=True)
    delivery_mtd_name = Column(String(100), nullable=True)
    delivery_mtd_desc = Column(String(800), nullable=True)

    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, default=func.current_date())
    modified_date = Column(Date, default=func.current_date(), onupdate=func.current_date())
    import_ref_crclm_dm_id = Column(Integer, nullable=True)


CudosCurriculumDeliveryMethod = CurriculumDeliveryMethod
CudosMapCrclmDeliveryMethod = CurriculumDeliveryMethod


class CurriculumDeliveryBloom(Base):
    __tablename__ = 'cudos_map_crclm_dm_bloomlevel'

    map_crclm_dm_bloomlevel_id = Column(Integer, primary_key=True, autoincrement=True)
    crclm_dm_id = Column(Integer, ForeignKey('cudos_map_crclm_deliverymethod.crclm_dm_id'), nullable=True)
    bloom_id = Column(Integer, ForeignKey('cudos_bloom_level.bloom_id'), nullable=True)

    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, default=func.current_date())
    modified_date = Column(Date, default=func.current_date(), onupdate=func.current_date())


CudosMapCrclmDmBloomlevel = CurriculumDeliveryBloom


# class Curriculum(Base):
#     __tablename__ = "curriculum"

#     crclm_id = Column(Integer, primary_key=True, index=True)
#     crclm_name = Column(String(255))
#     status = Column(Integer, default=1)


# class Curriculum(Base):
#     __tablename__ = "curriculum"

#     crclm_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)

#     crclm_name = Column(String(100), nullable=False)
#     crclm_description = Column(String(2000), nullable=False)

#     start_year = Column(YEAR, nullable=False)
#     end_year = Column(YEAR, nullable=False)

#     total_credits = Column(Float, nullable=False, default=0)
#     total_terms = Column(Integer, nullable=False, default=0)

#     crclm_owner = Column(MEDIUMINT(unsigned=True), nullable=False)
#     cia_passing_marks = Column(Float, nullable=True, default=0)
#     tee_passing_marks = Column(Float, nullable=True, default=0)

#     crclm_release_status = Column(TINYINT, default=0)
#     pgm_id = Column(MEDIUMINT(unsigned=True), nullable=False)

#     first_year_flag = Column(TINYINT, default=0)
#     status = Column(TINYINT, default=1)

#     create_date = Column(Date)
#     created_by = Column(MEDIUMINT(unsigned=True))

#     modify_date = Column(Date)
#     modified_by = Column(MEDIUMINT(unsigned=True))

#     import_ref_crclm_id = Column(MEDIUMINT(unsigned=True))
#     import_type = Column(TINYINT)


class Curriculum(Base):
    __tablename__ = "curriculum"

    crclm_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)

    crclm_name = Column(String(100), nullable=False)
    crclm_description = Column(String(2000), nullable=False)

    start_year = Column(YEAR, nullable=False)
    end_year = Column(YEAR, nullable=False)

    total_credits = Column(Float, nullable=False, default=0)
    total_terms = Column(Integer, nullable=False, default=0)

    # ✅ FIX HERE
    crclm_owner = Column(
        MEDIUMINT(unsigned=True),
        ForeignKey("iems_users.id"),
        nullable=False
    )

    # ✅ FIX HERE
    pgm_id = Column(
        MEDIUMINT(unsigned=True),
        ForeignKey("iems_program.pgm_id"),
        nullable=False
    )

    cia_passing_marks = Column(Float, nullable=True, default=0)
    tee_passing_marks = Column(Float, nullable=True, default=0)

    crclm_release_status = Column(TINYINT, default=0)
    first_year_flag = Column(TINYINT, default=0)
    status = Column(TINYINT, default=1)

    create_date = Column(Date)
    created_by = Column(MEDIUMINT(unsigned=True))

    modify_date = Column(Date)
    modified_by = Column(MEDIUMINT(unsigned=True))

    import_ref_crclm_id = Column(MEDIUMINT(unsigned=True))
    import_type = Column(TINYINT)

    # ✅ ADD RELATIONSHIPS
    program = relationship("IEMProgram", back_populates="curriculums")
    owner = relationship("IEMSUsers", foreign_keys=[crclm_owner], back_populates="curriculums")


class CudosPeo(Base):
    __tablename__ = 'cudos_peo'

    peo_id = Column(Integer, primary_key=True, autoincrement=True)
    peo_reference = Column(String(10), nullable=True)
    peo_statement = Column(String(2000), nullable=False)
    peo_type_id = Column(Integer, ForeignKey('cudos_po_type.po_type_id'), nullable=True)
    # Re-added state_id (required): keeps previous default behavior
    state_id = Column(Integer, nullable=False, default=1)
    academic_batch_id = Column(Integer, ForeignKey('iems_academic_batch.academic_batch_id'), nullable=False)
    created_date = Column(Date, nullable=True)
    created_by = Column(Integer, ForeignKey('iems_users.id'), nullable=True)
    modify_date = Column(Date, nullable=True)
    modified_by = Column(Integer, ForeignKey('iems_users.id'), nullable=True)
    import_ref_peo_id = Column(Integer, nullable=True)

    academic_batch = relationship('IEMSAcademicBatch',
                                  primaryjoin='IEMSAcademicBatch.academic_batch_id==CudosPeo.academic_batch_id',
                                  viewonly=True)

    # Optional relationship for convenience
    # curriculum = relationship('Curriculum', primaryjoin='Curriculum.crclm_id==CudosPeo.crclm_id', viewonly=True)


class CudosPerformanceIndicator(Base):
    """Corresponds to Competency"""
    __tablename__ = 'cudos_performance_indicator'

    pi_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    pi_statement = Column(String(2000), nullable=False)
    po_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    created_by = Column(Integer)  # unsigned int(10)
    modified_by = Column(Integer)
    create_date = Column(Date)
    modify_date = Column(Date)
    import_ref_pi_id = Column(MEDIUMINT(unsigned=True))


class CudosMeasure(Base):
    """Corresponds to Performance Indicator (PI)"""
    __tablename__ = 'cudos_measures'

    msr_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    msr_statement = Column(Text, nullable=False)
    pi_id = Column(MEDIUMINT(unsigned=True),
                   ForeignKey('cudos_performance_indicator.pi_id', ondelete='CASCADE', onupdate='CASCADE'),
                   nullable=False)
    pi_codes = Column(String(10))
    import_ref_msr_id = Column(MEDIUMINT(unsigned=True))

    measure = relationship(
        "CudosPerformanceIndicator",
        primaryjoin="CudosMeasure.pi_id==CudosPerformanceIndicator.pi_id",
        foreign_keys=[pi_id],
        viewonly=True,
    )


class CudosComment(Base):
    """BOS Comments"""
    __tablename__ = 'cudos_comment'

    comment_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    entity_id = Column(MEDIUMINT(unsigned=True))
    actual_id = Column(MEDIUMINT(unsigned=True))
    po_id = Column(MEDIUMINT(unsigned=True))
    clo_id = Column(MEDIUMINT(unsigned=True))
    crclm_id = Column(MEDIUMINT(unsigned=True))
    cmt_statement = Column(String(2000))
    status = Column(TINYINT)
    commented_by = Column(MEDIUMINT(unsigned=True))
    in_reply_to = Column(MEDIUMINT(unsigned=True))
    created_by = Column(Integer)  # unsigned int(10)
    modified_by = Column(Integer)
    created_date = Column(DateTime)
    modified_date = Column(DateTime)


class CudosWorkflowState(Base):
    __tablename__ = 'cudos_workflow_state'

    state_id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(50), nullable=False)
    alias_name = Column(String(100))
    created_by = Column(MEDIUMINT(unsigned=True), nullable=False)
    modified_by = Column(MEDIUMINT(unsigned=True), nullable=False)
    created_date = Column(Date)
    modified_date = Column(Date)
    percent = Column(Integer, nullable=False)  # unsigned int(5)


class CudosPeoPoApprover(Base):
    __tablename__ = "cudos_peo_po_approver"

    aid = Column(Integer, primary_key=True, autoincrement=True)

    entity_id = Column(Integer, nullable=False)

    academic_batch_id = Column(
        Integer,
        ForeignKey("iems_academic_batch.academic_batch_id"),
        nullable=True
    )

    approver_id = Column(
        Integer,
        ForeignKey("iems_users.id"),
        nullable=False
    )

    dept_id = Column(
        Integer,
        ForeignKey("iems_department.dept_id"),
        nullable=False
    )

    last_date = Column(Date, nullable=False)

    created_by = Column(
        Integer,
        ForeignKey("iems_users.id"),
        nullable=True
    )

    modified_by = Column(
        Integer,
        ForeignKey("iems_users.id"),
        nullable=True
    )

    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)


class CudosEntity(Base):
    __tablename__ = 'cudos_entity'

    entity_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    entity_name = Column(String(50), nullable=False)
    alias_entity_name = Column(String(60), nullable=False)
    order_by = Column(MEDIUMINT(unsigned=True))
    display = Column(MEDIUMINT(8))
    help_display = Column(MEDIUMINT(8), nullable=False)
    history_display = Column(MEDIUMINT(unsigned=True))
    import_display = Column(TINYINT(2))
    import_dipendency = Column(TINYINT(2))
    qpf_config = Column(MEDIUMINT(8))
    qpf_config_orderby = Column(MEDIUMINT(8))
    skip_approval = Column(TINYINT(unsigned=True), default=0)
    skip_review = Column(TINYINT(unsigned=True), default=0)
    created_by = Column(Integer, nullable=False)
    modified_by = Column(Integer, nullable=False)
    created_date = Column(Date, nullable=False)
    modified_date = Column(Date, nullable=False)
    synch_entity = Column(TINYINT(unsigned=True), default=0)
    synch_entity_order = Column(TINYINT(unsigned=True), default=0)


class CudosCourseCloValidator(Base):
    __tablename__ = 'cudos_course_clo_validator'

    vid = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    academic_batch_id = Column(Integer, ForeignKey('iems_academic_batch.academic_batch_id'), nullable=False)
    semester_id = Column(Integer, nullable=False)
    crs_id = Column(Integer, nullable=False)
    validator_id = Column(Integer)
    last_date = Column(Date, nullable=False)
    dept_id = Column(Integer, nullable=False)
    created_by = Column(Integer)
    modified_by = Column(Integer)
    created_date = Column(Date)
    modified_date = Column(Date)
    academic_batch = relationship('IEMSAcademicBatch',
                                  primaryjoin='IEMSAcademicBatch.academic_batch_id==CudosCourseCloValidator.academic_batch_id',
                                  viewonly=True)


class CudosClo(Base):
    __tablename__ = 'cudos_clo'

    clo_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    clo_statement = Column(String(2000), nullable=False)
    clo_code = Column(String(10), nullable=True)

    academic_batch_id = Column(Integer, ForeignKey('iems_academic_batch.academic_batch_id'), nullable=False)
    semester_id = Column(Integer, ForeignKey('iems_semester.semester_id'), nullable=False)
    crs_id = Column(Integer, ForeignKey('iems_courses.crs_id'), nullable=False)

    created_by = Column(Integer, ForeignKey('iems_users.id'), nullable=True)
    modified_by = Column(Integer, ForeignKey('iems_users.id'), nullable=True)
    create_date = Column(Date, nullable=True)
    modify_date = Column(Date, nullable=True)

    cia_clo_minthreshhold = Column(MEDIUMINT(unsigned=True), nullable=True)
    mte_clo_minthreshhold = Column(MEDIUMINT(unsigned=True), nullable=True)
    tee_clo_minthreshhold = Column(MEDIUMINT(unsigned=True), nullable=True)
    clo_studentthreshhold = Column(MEDIUMINT(unsigned=True), nullable=True)

    justify = Column(String(1000), nullable=True)
    import_ref_clo_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    status = Column(Integer, default=1)

    # convenience relationships (optional)
    course = relationship("IEMSCourses", foreign_keys=[crs_id], viewonly=True)
    academic_batch = relationship("IEMSAcademicBatch", foreign_keys=[academic_batch_id], viewonly=True)


class CudosCloPoMap(Base):
    __tablename__ = 'cudos_clo_po_map'

    clo_po_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    clo_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_clo.clo_id', ondelete='CASCADE', onupdate='CASCADE'),
                    nullable=False)
    po_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_po.po_id', ondelete='CASCADE', onupdate='CASCADE'),
                   nullable=False)

    academic_batch_id = Column(Integer, ForeignKey('iems_academic_batch.academic_batch_id', ondelete='CASCADE',
                                                   onupdate='CASCADE'), nullable=True)
    crs_id = Column(Integer, ForeignKey('iems_courses.crs_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)

    pi_id = Column(MEDIUMINT(unsigned=True),
                   ForeignKey('cudos_performance_indicator.pi_id', ondelete='CASCADE', onupdate='CASCADE'),
                   nullable=True)
    msr_id = Column(MEDIUMINT(unsigned=True),
                    ForeignKey('cudos_measures.msr_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)

    map_level = Column(String(15), nullable=True)
    justification = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    modified_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    create_date = Column(Date, nullable=True)
    modify_date = Column(Date, nullable=True)


class CudosNotes(Base):
    __tablename__ = "cudos_notes"

    notes_id = Column(Integer, primary_key=True, autoincrement=True)

    notes = Column(String(2000), nullable=True)

    academic_batch_id = Column(
        Integer,
        ForeignKey("iems_academic_batch.academic_batch_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )

    semester_id = Column(
        Integer,
        ForeignKey("iems_semester.semester_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True
    )

    particular_id = Column(Integer, nullable=True)

    entity_id = Column(
        Integer,
        ForeignKey("cudos_entity.entity_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True
    )

    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)

    create_date = Column(Date, server_default=func.current_date())
    modify_date = Column(Date, server_default=func.current_date(), onupdate=func.current_date())


class AOMethod(Base):
    __tablename__ = 'cudos_ao_method'

    ao_method_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    ao_method_pgm_id = Column(Integer, nullable=True)
    academic_batch_id = Column(Integer, nullable=True)
    term_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    crs_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    section_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    ao_method_name = Column(String(255), nullable=False)
    ao_method_description = Column(String(2000), nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)
    import_ref_ao_method_id = Column(MEDIUMINT(unsigned=True), nullable=True)


class QPDefinition(Base):
    __tablename__ = 'cudos_qp_definition'

    qpd_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    qpf_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    qpd_type = Column(MEDIUMINT(unsigned=True), nullable=True)
    cia_model_qp = Column(MEDIUMINT(unsigned=True), default=0)
    qp_rollout = Column(TINYINT, nullable=True)
    academic_batch_id = Column(Integer, nullable=True)
    semester_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    crs_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    lms_ciatee_stud_avg_score = Column(Float, nullable=True)
    qpd_title = Column(String(100), nullable=True)
    qpd_timing = Column(String(8), nullable=True)
    qpd_gt_marks = Column(Float, nullable=True)
    qpd_max_marks = Column(Float, nullable=True)
    qpd_notes = Column(Text, nullable=True)
    qpd_num_units = Column(MEDIUMINT, nullable=True)
    rubrics_flag = Column(Boolean, default=False)
    ao_method_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    created_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    modified_date = Column(Date, nullable=True)


class QPUnitDefinition(Base):
    __tablename__ = 'cudos_qp_unit_definition'

    qpd_unitd_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    qpd_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qp_definition.qpd_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    qp_unit_code = Column(String(50), nullable=True)
    qp_total_unitquestion = Column(MEDIUMINT, nullable=True)
    qp_attempt_unitquestion = Column(MEDIUMINT, nullable=True)
    qp_utotal_marks = Column(Float, nullable=True)
    created_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    modified_date = Column(Date, nullable=True)
    FM = Column(Integer, nullable=False)
    import_ref_qpd_unitd_id = Column(MEDIUMINT(unsigned=True), nullable=True)

    qp_definition = relationship('QPDefinition')


class QPMainQuestionDefinition(Base):
    __tablename__ = 'cudos_qp_mainquestion_definition'

    qp_mq_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    qp_unitd_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qp_unit_definition.qpd_unitd_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    qp_mq_flag = Column(MEDIUMINT, nullable=True)
    qp_mq_code = Column(String(50), nullable=True)
    qp_subq_code = Column(String(50), nullable=True)
    qp_content = Column(Text, nullable=True)
    qp_subq_marks = Column(DECIMAL(19, 2), nullable=True)
    created_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    modified_date = Column(Date, nullable=True)
    import_ref_qp_mq_id = Column(MEDIUMINT(unsigned=True), nullable=True)

    qp_unit_definition = relationship('QPUnitDefinition')


class QPMappingDefinition(Base):
    __tablename__ = 'cudos_qp_mapping_definition'

    qp_map_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    qp_mq_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qp_mainquestion_definition.qp_mq_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    entity_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    actual_mapped_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    created_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    modified_date = Column(Date, nullable=True)
    mapped_marks = Column(Float, nullable=False)
    mapped_percentage = Column(Integer, nullable=False)
    import_ref_qp_map_id = Column(MEDIUMINT(unsigned=True), nullable=True)

    qp_mainquestion = relationship('QPMainQuestionDefinition')


class QPOrMappingDefinition(Base):
    __tablename__ = 'cudos_qp_or_mapping_definition'

    qp_or_map_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    qpd_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qp_definition.qpd_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    question_one = Column(String(1000), nullable=True)
    question_two = Column(String(1000), nullable=True)
    or_type = Column(TINYINT(unsigned=True), nullable=False, default=0)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)


class QPUpload(Base):
    __tablename__ = 'cudos_qp_upload'

    doc_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    academic_batch_id = Column(Integer, ForeignKey('iems_academic_batch.academic_batch_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    semester_id = Column(Integer, ForeignKey('iems_semester.semester_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    crs_id = Column(Integer, ForeignKey('iems_courses.crs_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    qpd_type = Column(MEDIUMINT(unsigned=True), nullable=True)
    section_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    ao_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    qpd_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    file_name = Column(String(300), nullable=True)
    upload_by = Column(Integer, nullable=True)
    uplaod_date = Column(Date, nullable=True)


CudosQpDefinition = QPDefinition
CudosQpUnitDefinition = QPUnitDefinition
CudosQpMainQuestionDefinition = QPMainQuestionDefinition
CudosQpMappingDefinition = QPMappingDefinition
CudosQpUpload = QPUpload


class QPFramework(Base):
    __tablename__ = 'cudos_qp_framework'

    qpf_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    pgm_id = Column(Integer, ForeignKey('iems_program.pgm_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    qpf_type = Column(String(100), nullable=True)
    qpf_title = Column(String(100), nullable=True)
    qpf_num_units = Column(MEDIUMINT, nullable=True)
    qpf_gt_marks = Column(Float, nullable=True)
    qpf_max_marks = Column(Float, nullable=True)
    qpf_notes = Column(Text, nullable=True)
    qpf_instructions = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Date, nullable=True)


class QPFUnit(Base):
    __tablename__ = 'cudos_qpf_unit'

    qpf_unit_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    qpf_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qp_framework.qpf_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    qpf_unit_code = Column(String(50), nullable=True)
    qpf_num_mquestions = Column(MEDIUMINT, nullable=True)
    qpf_utotal_marks = Column(Float, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Date, nullable=True)


# class QPFMQuestion(Base):
#     __tablename__ = 'cudos_qpf_mquestion'

#     qpf_mq_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
#     qpf_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qp_framework.qpf_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
#     qpf_unit_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qpf_unit.qpf_unit_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
#     qpf_unit_code = Column(String(50), nullable=True)
#     qpf_mq_code = Column(String(50), nullable=True)
#     qpf_mtotal_marks = Column(Float, nullable=True)
#     course_outcome_id = Column(Integer, nullable=True)
#     clo_id = Column(Integer, nullable=True)
#     bloom_level_id = Column(Integer, nullable=True)
#     is_mandatory = Column(Integer, nullable=False, default=0)
#     main_question_no = Column(Integer, nullable=True)
#     sub_question_no = Column(Integer, nullable=True)
#     created_by = Column(Integer, nullable=True)
#     created_date = Column(Date, nullable=True)
#     modified_by = Column(Integer, nullable=True)
#     modified_date = Column(Date, nullable=True)


class QPFMQuestion(Base):
    __tablename__ = 'cudos_qpf_mquestion'

    qpf_mq_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    qpf_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qp_framework.qpf_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    qpf_unit_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qpf_unit.qpf_unit_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    qpf_unit_code = Column(String(50), nullable=True)
    qpf_mq_code = Column(String(50), nullable=True)
    qpf_mtotal_marks = Column(Float, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Date, nullable=True)


# ─────────────────────────────────────────────────────────────────────────────
# Missing models for Manage CIA QP & Rubrics module
# ─────────────────────────────────────────────────────────────────────────────


class CudosMapCoursetoCourseInstructor(Base):
    __tablename__ = 'cudos_map_courseto_course_instructor'

    mcci_id = Column(Integer, primary_key=True, autoincrement=True)
    academic_batch_id = Column(Integer, nullable=False)
    semester_id = Column(Integer, nullable=False)
    crs_id = Column(Integer, ForeignKey('iems_courses.crs_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    course_instructor_id = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    section_id = Column(Integer, nullable=True)
    student_finalize_flag = Column(Boolean, nullable=True, default=False)
    cia_finalise_flag = Column(Boolean, nullable=True, default=False)
    cia_marks_finalise_flag = Column(Boolean, nullable=True)
    tee_section_wise_marks_uploaded_flag = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)
    import_ref_mcci_id = Column(Integer, nullable=True)
    lms_section_attendance_finalize = Column(Boolean, nullable=True, default=True)
    sec_stud_reg_flag = Column(Boolean, nullable=False, default=False)


    # Relationships
    course = relationship(
        "IEMSCourses",
        back_populates="instructors"
    )

    instructor = relationship(
        "IEMSUsers",
        back_populates="assigned_courses"
    )




class CudosMapCloBloomLevel(Base):
    """Maps Course Learning Outcomes (CLOs) to Bloom taxonomy levels."""
    __tablename__ = 'cudos_map_clo_bloom_level'

    map_clo_bl_id = Column(Integer, primary_key=True, autoincrement=True)
    clo_id = Column(
        Integer,
        ForeignKey('cudos_clo.clo_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True
    )
    bloom_id = Column(
        Integer,
        ForeignKey('cudos_bloom_level.bloom_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True
    )
    created_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Date, nullable=True)


class CudosMapCloDeliveryMethod(Base):
    """Maps Course Learning Outcomes (CLOs) to Delivery Methods."""
    __tablename__ = 'cudos_map_clo_delivery_method'

    map_clo_dm_id = Column(Integer, primary_key=True, autoincrement=True)
    clo_id = Column(
        Integer,
        ForeignKey('cudos_clo.clo_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True
    )
    delivery_method_id = Column(
        Integer,
        ForeignKey('cudos_delivery_method.delivery_mtd_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True
    )
    created_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Date, nullable=True)





# class CudosTopic(Base):
#     """Curriculum topics linked to courses — used in QP question mapping."""
#     __tablename__ = 'cudos_topic'
#     __table_args__ = {"extend_existing": True}

#     topic_id = Column(Integer, primary_key=True, autoincrement=True)
#     topic_name = Column(String(500), nullable=True)
#     topic_description = Column(Text, nullable=True)
#     crs_id = Column(
#         Integer,
#         ForeignKey('iems_courses.crs_id', ondelete='CASCADE', onupdate='CASCADE'),
#         nullable=True
#     )
#     academic_batch_id = Column(
#         Integer,
#         ForeignKey('iems_academic_batch.academic_batch_id'),
#         nullable=True
#     )
#     semester_id = Column(
#         Integer,
#         ForeignKey('iems_semester.semester_id'),
#         nullable=True
#     )
#     unit_no = Column(Integer, nullable=True)
#     status = Column(Integer, default=1, nullable=True)
#     created_by = Column(Integer, nullable=True)
#     created_date = Column(Date, nullable=True)
#     modified_by = Column(Integer, nullable=True)
#     modified_date = Column(Date, nullable=True)


class CudosStudentAssessment(Base):
    __tablename__ = 'cudos_student_assessment'

    # ✅ Primary Key
    assessment_id = Column(Integer, primary_key=True, autoincrement=True)

    # ✅ Foreign Keys
    qp_mq_id = Column(Integer, ForeignKey('cudos_qp_mainquestion_definition.qp_mq_id'))
    section_id = Column(Integer, ForeignKey('cudos_master_type_details.mt_details_id'))

    # ✅ Student Details
    roll_number = Column(String(200), nullable=True)
    student_name = Column(String(100), nullable=True)
    student_usn = Column(String(50), nullable=True)

    # ✅ Marks Details
    total_marks = Column(Float, nullable=True)
    qp_mq_code = Column(String(50), nullable=True)
    qp_subq_code = Column(String(50), nullable=True)
    secured_marks = Column(Float, nullable=True)

    # ✅ Other Fields
    status_flag = Column(Integer, default=1, nullable=True)
    crclm_name = Column(String(100), nullable=True)

    modified_by = Column(Integer, nullable=True)
    modify_date = Column(DateTime, nullable=True)

    qp_mainquestion_definition = relationship('QPMainQuestionDefinition')
    master_type_details = relationship('MasterTypeDetails', foreign_keys=[section_id], viewonly=True)


class CudosMapCrsMainOccasionType(Base):
    __tablename__ = 'cudos_map_crs_main_occasion_type'

    cmot_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    mot_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_org_main_occasion_type.mot_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    crs_id = Column(Integer, ForeignKey('iems_courses.crs_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    max_mks = Column(MEDIUMINT(unsigned=True), nullable=True)
    min_mks = Column(MEDIUMINT(unsigned=True), nullable=True)
    weightage = Column(MEDIUMINT(unsigned=True), nullable=True)
    created_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    modified_by = Column(MEDIUMINT(unsigned=True), nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)


class CudosAoRubricsCriteria(Base):
    __tablename__ = 'cudos_ao_rubrics_criteria'

    rubrics_criteria_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    ao_method_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    criteria = Column(Text, nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)
    import_ref_rubrics_criteria_id = Column(MEDIUMINT(unsigned=True), nullable=True)


class CudosAoRubricsRange(Base):
    __tablename__ = 'cudos_ao_rubrics_range'

    rubrics_range_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    ao_method_id = Column(MEDIUMINT(unsigned=True), nullable=False)
    rubrics_criteria_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    criteria_range_name = Column(String(100), nullable=True)
    criteria_range = Column(String(20), nullable=False)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)
    import_ref_rubrics_range_id = Column(MEDIUMINT(unsigned=True), nullable=True)


class CudosSuStudentStakeholderDetails(Base):
    __tablename__ = 'cudos_su_student_stakeholder_details'
    
    ssd_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    stakeholder_group_id = Column(Integer, ForeignKey('cudos_su_stakeholder_groups.stakeholder_group_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    dept_id = Column(Integer, ForeignKey('iems_department.dept_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    pgm_id = Column(Integer, ForeignKey('iems_program.pgm_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    crclm_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    section_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_master_type_details.mt_details_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    user_id = Column(Integer, nullable=True)
    roll_number = Column(String(10), nullable=True)
    prev_student_usn = Column(String(50), nullable=True)
    student_usn = Column(String(50), nullable=True)
    admmission_type = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_master_type_details.mt_details_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    title = Column(String(10), nullable=True)
    first_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    contact_number = Column(BigInteger, nullable=True)
    aadhar_number = Column(String(20), nullable=True)
    dob = Column(Date, nullable=True)
    personal_email = Column(String(50), nullable=True)
    parent_name = Column(String(200), nullable=True)
    parent_gender = Column(MEDIUMINT(unsigned=True), nullable=True)
    parent_email = Column(String(200), nullable=True)
    parent_contact = Column(BigInteger, nullable=True)
    parent2_name = Column(String(200), nullable=True)
    parent2_gender = Column(MEDIUMINT(unsigned=True), nullable=True)
    parent2_email = Column(String(200), nullable=True)
    parent2_contact = Column(BigInteger, nullable=True)
    student_category = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_master_type_details.mt_details_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    student_gender = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_master_type_details.mt_details_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    student_nationality = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_master_type_details.mt_details_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    any_other_nationality = Column(String(200), nullable=True)
    student_state = Column(String(200), nullable=True)
    entrance_exam = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_master_type_details.mt_details_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    any_other_entrance_exam = Column(String(200), nullable=True)
    student_rank = Column(MEDIUMINT(unsigned=True), nullable=True)
    created_on = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_on = Column(DateTime, nullable=True)
    modified_by = Column(Integer, nullable=True)
    status_active = Column(Integer, default=1)
    department_acronym = Column(String(45), nullable=True)
    import_crclm_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    profile_image = Column(String(45), nullable=True)
    application_no = Column(String(45), nullable=True)
    sslc_percentage = Column(DECIMAL(5, 2), nullable=True)
    puc_percentage = Column(DECIMAL(5, 2), nullable=True)
    present_address = Column(String(500), nullable=True)
    permanent_address = Column(String(500), nullable=True)
    fathers_name = Column(String(45), nullable=True)
    mothers_name = Column(String(45), nullable=True)
    fathers_occupation = Column(String(65), nullable=True)
    mothers_occupation = Column(String(65), nullable=True)
    guardian_name = Column(String(120), nullable=True)
    guardian_gender = Column(MEDIUMINT(unsigned=True), nullable=True)
    guardian_phone = Column(String(20), nullable=True)
    guardian_email = Column(String(80), nullable=True)
    guardian_contact = Column(BigInteger, nullable=True)
    user_pic = Column(String(255), nullable=True)
    mother_tongue = Column(String(60), nullable=True)
    semester = Column(Integer, default=1)
    branch_cycle = Column(Integer, default=1)
    doj = Column(Date, nullable=True)
    ems_std_usno = Column(String(45), nullable=True)
    ems_std_regno = Column(String(45), nullable=True)
    ems_section = Column(String(45), nullable=True)
    stud_admission_dept_id = Column(Integer, nullable=True)
    stud_admission_pgm_id = Column(Integer, nullable=True)
    academic_batch_id = Column(Integer, ForeignKey('iems_academic_batch.academic_batch_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    active_semester = Column(Integer, nullable=True)


class CudosStudentAssessmentTotalmarks(Base):
    __tablename__ = 'cudos_student_assessment_totalmarks'
    
    sat_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    crclm_id = Column(MEDIUMINT(unsigned=True), nullable=True)  # FK to curriculum.crclm_id (table not in SA mapper)
    term_id = Column(Integer, nullable=True)  # FK to erp_crclm_terms.erp_crclm_term_id (table not in SA mapper)
    crs_id = Column(Integer, ForeignKey('iems_courses.crs_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    section_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_master_type_details.mt_details_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    ao_id = Column(MEDIUMINT(unsigned=True), nullable=True)
    qpd_type = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_master_type_details.mt_details_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    qpd_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_qp_definition.qpd_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    student_name = Column(String(100), nullable=True)
    student_usn = Column(String(50), nullable=True)
    total_marks = Column(Float(asdecimal=True), nullable=True)
    crclm_name = Column(String(100), nullable=True)
    roll_number = Column(String(200), nullable=True)
    created_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    create_date = Column(Date, nullable=True)
    modified_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    modify_date = Column(Date, nullable=True)




#Attainment Performance Level

class CudosPerformanceLevelPO(Base):
    __tablename__ = 'cudos_performance_level_po'

    plp_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    academic_batch_id = Column(Integer, ForeignKey('iems_academic_batch.academic_batch_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    po_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_po.po_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    performance_level_name = Column(String(50), nullable=True)
    performance_level_name_alias = Column(String(50), nullable=True)
    performance_level_value = Column(MEDIUMINT(unsigned=True), nullable=True)
    description = Column(String(2000), nullable=True)
    start_range = Column(Float, nullable=True)
    conditional_opr = Column(String(4), nullable=True)
    end_range = Column(Float, nullable=True)
    created_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    modified_date = Column(Date, nullable=True)

    # convenience relationships
    academic_batch = relationship('IEMSAcademicBatch', primaryjoin='IEMSAcademicBatch.academic_batch_id==CudosPerformanceLevelPO.academic_batch_id', viewonly=True)


 
class CudosIndirectAttainmentLevelCrclmPo(Base):
    __tablename__ = 'cudos_indirect_attainment_level_crclm_po'

    indirect_level_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    academic_batch_id = Column(Integer, ForeignKey('iems_academic_batch.academic_batch_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    po_id = Column(MEDIUMINT(unsigned=True), ForeignKey('cudos_po.po_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)

    attainment_level_name = Column(String(50), nullable=True)
    attainment_level_name_alias = Column(String(50), nullable=True)
    attainment_level_value = Column(MEDIUMINT(unsigned=True), nullable=True)
    conditional_opr = Column(String(4), nullable=True)
    indirect_percentage = Column(MEDIUMINT(unsigned=True), nullable=True)
    justify = Column(String(2000), nullable=True)

    created_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    modified_date = Column(Date, nullable=True)

    # convenience relationship
    academic_batch = relationship('IEMSAcademicBatch', primaryjoin='IEMSAcademicBatch.academic_batch_id==CudosIndirectAttainmentLevelCrclmPo.academic_batch_id', viewonly=True)




class CudosAttainmentLevelCourse(Base):
    __tablename__ = 'cudos_attainment_level_course'

    alp_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    academic_batch_id = Column(Integer, ForeignKey('iems_academic_batch.academic_batch_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    semester_id = Column(Integer, ForeignKey('iems_semester.semester_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    crs_id = Column(Integer, ForeignKey('iems_courses.crs_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)

    attainment_level_name = Column(String(50), nullable=True)
    attainment_level_name_alias = Column(String(50), nullable=True)
    attainment_level_value = Column(MEDIUMINT(unsigned=True), nullable=True)

    cia_direct_percentage = Column(MEDIUMINT(unsigned=True), nullable=True)
    mte_direct_percentage = Column(MEDIUMINT(unsigned=True), nullable=False)
    tee_direct_percentage = Column(MEDIUMINT(unsigned=True), nullable=True)
    indirect_percentage = Column(MEDIUMINT(unsigned=True), nullable=True)
    conditional_opr = Column(String(4), nullable=True)

    cia_target_percentage = Column(MEDIUMINT(unsigned=True), nullable=True)
    mte_target_percentage = Column(MEDIUMINT(unsigned=True), nullable=False)
    tee_target_percentage = Column(MEDIUMINT(unsigned=True), nullable=True)

    justify = Column(String(2000), nullable=True)

    created_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, ForeignKey('iems_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    modified_date = Column(Date, nullable=True)

    # convenience relationships
    academic_batch = relationship('IEMSAcademicBatch', primaryjoin='IEMSAcademicBatch.academic_batch_id==CudosAttainmentLevelCourse.academic_batch_id', viewonly=True)
    semester = relationship('IEMSemester', primaryjoin='IEMSemester.semester_id==CudosAttainmentLevelCourse.semester_id', viewonly=True)
    course = relationship('IEMSCourses', primaryjoin='IEMSCourses.crs_id==CudosAttainmentLevelCourse.crs_id', viewonly=True)
    created_user = relationship('IEMSUsers', primaryjoin='IEMSUsers.id==CudosAttainmentLevelCourse.created_by', viewonly=True)
    modified_user = relationship('IEMSUsers', primaryjoin='IEMSUsers.id==CudosAttainmentLevelCourse.modified_by', viewonly=True)


class CudosAttainmentLevelCrclm(Base):
    __tablename__ = "cudos_attainment_level_crclm"

    al_crclm_id = Column(Integer, primary_key=True, autoincrement=True)
    academic_batch_id = Column(Integer, nullable=True)

    attainment_level_name = Column(String(50), nullable=True)
    attainment_level_name_alias = Column(String(50), nullable=True)
    attainment_level_value = Column(Integer, nullable=True)

    direct_percentage = Column(Integer, nullable=True)
    indirect_percentage = Column(Integer, nullable=True)

    conditional_opr = Column(String(4), nullable=True)
    target_percentage = Column(Integer, nullable=True)

    justify = Column(String(2000), nullable=True)

    created_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(Date, nullable=True)


class CudosMapCourseBloomlevel(Base):
    __tablename__ = "cudos_map_course_bloomlevel"

    map_course_blm_id = Column(Integer, primary_key=True, autoincrement=True)
    academic_batch_id = Column(Integer, ForeignKey("iems_academic_batch.academic_batch_id"), nullable=True)
    term_id = Column(Integer, ForeignKey("iems_semester.semester_id"), nullable=False)
    crs_id = Column(Integer, ForeignKey("iems_courses.crs_id"), nullable=False)
    bld_id = Column(Integer, ForeignKey("cudos_bloom_domain.bld_id"), nullable=True)
    bloom_id = Column(Integer, ForeignKey("cudos_bloom_level.bloom_id"), nullable=False)
    
    # Thresholds
    cia_bloomlevel_minthreshhold = Column(Integer, default=50)
    mte_bloomlevel_minthreshhold = Column(Integer, default=50)
    tee_bloomlevel_minthreshhold = Column(Integer, default=50)
    bloomlevel_studentthreshhold = Column(Integer, default=70)
    
    justify = Column(String(1000), nullable=True)
    
    # Audit Fields
    created_by = Column(Integer, ForeignKey("iems_users.id"), nullable=True)
    modified_by = Column(Integer, ForeignKey("iems_users.id"), nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)

    # Relationships (Optional but helpful for joining)
    bloom_master = relationship("BloomLevel")
    

class CudosSuQuestionType(Base):
    __tablename__ = "cudos_su_question_types"
    __table_args__ = {'extend_existing': True}

    question_type_id = Column(Integer, primary_key=True, autoincrement=True)
    question_type_name = Column(String(250), nullable=False)
    description = Column(String(2000), nullable=True)
    status = Column(SmallInteger, default=1)
    modify_date = Column(Date, nullable=True)
    modified_by = Column(Integer, nullable=True)
    
class CudosSuStakeholderGroup(Base):
    __tablename__ = "cudos_su_stakeholder_groups"
    __table_args__ = {'extend_existing': True}

    stakeholder_group_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False)
    description = Column(String(2000), nullable=True)
    status = Column(SmallInteger, default=1)
    created_on = Column(DateTime, nullable=False)
    created_by = Column(Integer, nullable=False)
    modified_on = Column(DateTime, nullable=True)
    modified_by = Column(Integer, nullable=True)
    student_group = Column(SmallInteger, default=0)

class CudosSuAnswerTemplate(Base):
    __tablename__ = "cudos_su_answer_templates"
    __table_args__ = {'extend_existing': True}

    answer_template_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), nullable=False)
    status = Column(SmallInteger, default=1)
    feedbk_flag = Column(SmallInteger, default=0) # 0: Improvement, 1: Outcome Attainment
    modify_date = Column(Date, nullable=True)
    modified_by = Column(Integer, nullable=True)

    options_list = relationship("CudosSuAnswerOption", back_populates="template", cascade="all, delete-orphan")

class CudosSuAnswerOption(Base):
    __tablename__ = "cudos_su_answer_options"
    __table_args__ = {'extend_existing': True}

    answer_options_id = Column(Integer, primary_key=True, autoincrement=True)
    answer_template_id = Column(Integer, ForeignKey('cudos_su_answer_templates.answer_template_id', ondelete="CASCADE"))
    options = Column(String(200), nullable=False) # Maps to Option Label
    option_val = Column(SmallInteger, default=1)  # Maps to Weightage

    template = relationship("CudosSuAnswerTemplate", back_populates="options_list")

class CudosSuStakeholderDetail(Base):
    __tablename__ = "cudos_su_stakeholder_details"
    __table_args__ = {'extend_existing': True}

    stakeholder_detail_id = Column(Integer, primary_key=True, autoincrement=True)
    stakeholder_group_id = Column(Integer, ForeignKey('cudos_su_stakeholder_groups.stakeholder_group_id'), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(200), nullable=False)
    qualification = Column(String(45), nullable=True)
    contact = Column(BigInteger, nullable=True)
    
    created_on = Column(DateTime, nullable=False)
    created_by = Column(Integer, nullable=False)
    modified_on = Column(DateTime, nullable=True)
    modified_by = Column(Integer, nullable=True)
    status = Column(SmallInteger, default=1)
    academic_batch_id = Column(Integer, default=0) 
    student_usn = Column(String(45), default='null')
    dept_id = Column(Integer, default=0)
    pgm_id = Column(Integer, default=0)

    group = relationship("CudosSuStakeholderGroup", backref="stakeholders")
    

class CudosSuTemplate(Base):
    __tablename__ = "cudos_su_template"
    __table_args__ = {'extend_existing': True}

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=False)
    dept_id = Column(Integer, ForeignKey('iems_department.dept_id'), nullable=False)
    pgm_id = Column(Integer, ForeignKey('iems_program.pgm_id'), nullable=False)
    crs_id = Column(Integer, default=None)
    su_type_id = Column(Integer, nullable=False)
    answer_template_id = Column(Integer, ForeignKey('cudos_su_answer_templates.answer_template_id'), default=None)
    su_for = Column(Integer, nullable=False)
    status = Column(SmallInteger, default=0)
    created_on = Column(DateTime, nullable=False)
    created_by = Column(Integer, nullable=False)
    modified_on = Column(DateTime, default=None)
    modified_by = Column(Integer, default=None)

    # Relationships
    questions = relationship("CudosSuTemplateQuestions", back_populates="template", cascade="all, delete-orphan")


class CudosSuTemplateQuestions(Base):
    __tablename__ = "cudos_su_template_questions"
    __table_args__ = {'extend_existing': True}

    template_question_id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey('cudos_su_template.template_id'), nullable=False)
    question_type_id = Column(Integer, ForeignKey('cudos_su_question_types.question_type_id'), nullable=False)
    question = Column(String(2000), nullable=False)
    is_multiple_choice = Column(Integer, default=0) # 0: single, 1: multiple, 595: descriptive
    is_option_type = Column(SmallInteger, default=0)

    # Relationships
    template = relationship("CudosSuTemplate", back_populates="questions")
    options = relationship("CudosSuTemplateQstnOptions", back_populates="question", cascade="all, delete-orphan")


class CudosSuTemplateQstnOptions(Base):
    __tablename__ = "cudos_su_template_qstn_options"
    __table_args__ = {'extend_existing': True}

    template_qstn_option_id = Column(Integer, primary_key=True, autoincrement=True)
    template_question_id = Column(Integer, ForeignKey('cudos_su_template_questions.template_question_id'), nullable=False)
    template_id = Column(Integer, ForeignKey('cudos_su_template.template_id'), nullable=False)
    option = Column(String(200), nullable=False)
    option_val = Column(SmallInteger, default=1)

    # Relationships
    question = relationship("CudosSuTemplateQuestions", back_populates="options")
    