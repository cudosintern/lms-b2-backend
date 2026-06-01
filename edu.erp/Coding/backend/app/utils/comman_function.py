
from fastapi import Depends
from sqlalchemy import update
from sqlalchemy.orm import Session
from ..utils.http_return_helper import returnException, returnSuccess
from ..db.models import Caste, IEMGrade, IEMHallTypeMaster, IEMMasters, IEMOrganisation, IEMParentsOccupationMaster, IEMPriorityMaster, IEMSAcademicBatch, IEMSAdmissionQuota, IEMSAdmissionType, IEMSCategoryTypeMaster, IEMSCertificateTypeMaster, IEMSCourseType, IEMSEducationQualificationMaster, IEMSEventStatus, IEMSEventType, IEMSEventTypeMaster, IEMSUserDesignation, IEMSUserOrg, IEMSUserRoleMaster, IEMSUserRoles, IEMSection, IEMUniversity, PhysicallyChallengedDescription, Religion 
from ..core.database import get_db
from datetime import datetime
import random
import string


def fetch_user_type():
    return [
        {"user_type": "U", "user_type_description": "University"},
        {"user_type": "O", "user_type_description": "IEMOrganisation"}
    ]
    
def fetch_role_list(db: Session):
    roles = db.query(IEMSUserRoleMaster).filter(
        IEMSUserRoleMaster.status == 1,
        IEMSUserRoleMaster.user_role_id != 3,
        IEMSUserRoleMaster.user_role_id != 5
    ).all()

    return [{"user_role_id": role.user_role_id, "user_role": role.user_role} for role in roles]

def get_user_designation(db: Session):
    designations = db.query(IEMSUserDesignation).all()
    return [{"designation_id": d.designation_id, "designation_name": d.designation_name} for d in designations]

def organization_list(db: Session):
    org_list = (
        db.query(
            IEMOrganisation.org_id,
            IEMOrganisation.org_name,
            IEMOrganisation.org_desc,
            IEMOrganisation.org_society,
            IEMOrganisation.unv_id,
            IEMUniversity.unv_name,
            IEMOrganisation.status,
            IEMOrganisation.profile_image
        )
        .join(IEMUniversity, IEMOrganisation.unv_id == IEMUniversity.unv_id)
        .all()
    )

    return [{
        'org_id': org_value.org_id,
        'org_name': org_value.org_name,
        'org_desc': org_value.org_desc,
        'org_society': org_value.org_society,
        'unv_id': org_value.unv_id,
        'unv_name': org_value.unv_name,
        'status': org_value.status,
        'profile_image': org_value.profile_image,
    } for org_value in org_list]
    

# Function to fetch user organization and role
def get_user_org_role(user_id: int, db: Session):
    user_org_list = db.query(IEMSUserOrg.org_id).filter(IEMSUserOrg.user_id == user_id).all()
    user_role_list = db.query(IEMSUserRoles.role_id).filter(IEMSUserRoles.user_id == user_id).all()

    return {
        "org": [org.org_id for org in user_org_list],
        "role": [role.role_id for role in user_role_list]
    }


def all_masters_list(
    db: Session = Depends(get_db)
):
    try:
        all_masters_list_data = process_all_masters_list(db)
        return all_masters_list_data
    except Exception as e:
        raise e


def process_all_masters_list(db: Session):
    all_masters_list = fetch_all_masters_list(db)
    all_masters_list_data = [
        {
            'master_id': master.master_id,
            'master_name': master.master_name,
            'master_description': master.master_description,
            'status': master.status,
            'org_id': master.org_id,
            'created_by': master.created_by,
            'modified_by': master.modified_by,
            'create_date': master.create_date,
            'modify_date': master.modify_date
        }
        for master in all_masters_list
    ]
    return all_masters_list_data


def fetch_all_masters_list(db: Session):
    query = db.query(IEMMasters).distinct()
    query = query.order_by(IEMMasters.master_id)
    return query.all()


def get_parents_occupation_master_list(
    db: Session = Depends(get_db)
):  
    try:
        parents_occupation_master_data = fetch_parents_occupation_master_list(db)
        return parents_occupation_master_data
    except Exception as e:
        raise e
        

def fetch_parents_occupation_master_list(db: Session):
    return db.query(IEMParentsOccupationMaster).distinct().filter(IEMParentsOccupationMaster.status == 1).order_by(IEMParentsOccupationMaster.occupation_id).all()

def hall_type_list(
    db: Session = Depends(get_db)
):  
    try:
        hall_type_data = get_hall_type_list(db)
        return hall_type_data
    except Exception as e:
        raise e

def get_hall_type_list(db: Session):
    hall_type_list = db.query(IEMHallTypeMaster).filter(IEMHallTypeMaster.status == 1).all()
    return [
        {
            'hall_type_id': hall_type.hall_type_id,
            'hall_type_name': hall_type.hall_type_name,
            'status': hall_type.status
        }
        for hall_type in hall_type_list
    ]
    
    
def priority_list(
    db: Session = Depends(get_db)
):
    try:
        priority_data = get_priority_list(db)
        return (priority_data)
    except Exception as e:
        raise e

def get_priority_list(db: Session):
    priority_list = db.query(IEMPriorityMaster).filter(IEMPriorityMaster.status == 1).all()
    return [
        {
            'priority_id': priority.priority_id,
            'priority_name': priority.priority_name,
            'status': priority.status
        }
        for priority in priority_list
    ]
    
    
def get_academics_event_status(
    db: Session = Depends(get_db)
):
    try:
        data = get_academics_event_status_data(db)
        return (data)
    except Exception as e:
        raise e

def get_academics_event_status_data(db: Session):
    priority_list = db.query(IEMSEventStatus).all()
    return [
        {
            'id': priority.id,
            'event_status': priority.event_status,
        }
        for priority in priority_list
    ]

def get_academics_event(db: Session = Depends(get_db)):
    try:
        return get_academics_event_data(db)
    except Exception as e:
        raise e 

def get_academics_event_data(db: Session):
    # Query the event list from the database based on the flag
    query = db.query(IEMSEventType.id, IEMSEventType.event)
    query = query.filter(IEMSEventType.id.in_([1, 2, 3, 5, 6]))
    result = query.all()
    
    event_list_data = []
    for event in result:
        event_list_data.append({
            'id': event.id,
            'event': event.event
        })
    
    return (event_list_data)



def get_grade_type_list(
    db: Session = Depends(get_db)
):  
    try:
        get_grade_type = get_grade_type_list_data(db)
        return get_grade_type
    except Exception as e:
        raise e

def get_grade_type_list_data(db: Session):
    grade_type_list = db.query(IEMGrade.grade_type).distinct().all()
    return [
        {
            'grade_type': grade_type[0] 
        }
        for grade_type in grade_type_list
    ]
    
def get_coursetype_list_options():
    options_list=['Theory','Lab','Lab-Theory']
    return [{"id": index, "value": option} for index, option in enumerate(options_list)]

def get_blood_group_list_options():
    blood_groups = [
        {"id": "0", "name": "A+ve"},
        {"id": "1", "name": "A-ve"},
        {"id": "2", "name": "B+ve"},
        {"id": "3", "name": "B-ve"},
        {"id": "4", "name": "AB+ve"},
        {"id": "5", "name": "AB-ve"},
        {"id": "6", "name": "O+ve"},
        {"id": "7", "name": "O-ve"}
    ]
    return [{"id": index, "value": blood_group["name"]} for index, blood_group in enumerate(blood_groups)]


def get_coursetype_options():
    optionstype_list=['Mandatory','Elective','Open-Elective']
    return optionstype_list

def get_department_permission(user_id: int, current_user: str, db: Session) -> bool:
    """
    Checks if the user has department-wise permissions.
    """
    # Query to check the user's roles
    result = (db.query(IEMSUserRoleMaster.department_wise)
                .join(IEMSUserRoles, IEMSUserRoles.role_id == IEMSUserRoleMaster.user_role_id)
                .filter(IEMSUserRoles.user_id == user_id)
                .first())
    
    super_admin = current_user.get('super_admin')
    technical_admin =current_user.get('technical_admin')

    if super_admin or technical_admin:
        return False  
    else:
        department_permission = result.department_wise if result else False
        return department_permission == 1 

def get_event_status_options():
    return [
        {"label": "Upcoming Events", "value": "up_coming"},
        {"label": "Completed Events", "value": "completed"}
    ]
    
def get_section_list_options(db: Session):
    section_type_list = db.query(IEMSection.section).distinct().all()
    return [
        {
            'section_list': section[0] 
        }
        for section in section_type_list
    ]
    
    
def get_category_options(db: Session):
    try:
        category_list = fetch_category_data(db)
        category_data = [{"category_code": category.category_code} for category in category_list]
        return (category_data)
    except Exception as e:
        raise e

def fetch_category_data(db: Session):
    return db.query(IEMSCategoryTypeMaster.category_code).all()



def religion_list(db: Session):
    try:
        religions = db.query(Religion).order_by(Religion.religion_id).distinct().all()
        data = [{"religion_id": religion.religion_id, "name": religion.name} for religion in religions]
        return data
    except Exception as e:
        raise e
    
    
def get_caste_list(db: Session):
    query = db.query(Caste).distinct(Caste.caste_id).order_by(Caste.name)
    caste_list = query.order_by(Caste.caste_id).all()
    caste_data = [
        {
            'caste_id': caste.caste_id,
            'name': caste.name,
        }
        for caste in caste_list
    ]
    return caste_data

def get_quota(db: Session):
    try:
        quotas = db.query(IEMSAdmissionQuota).filter(IEMSAdmissionQuota.status == 1).all()
        data = [{"id": quota.id, "quota_type": quota.admission_quota_type} for quota in quotas]
        return data
    except Exception as e:
        raise e
    
def get_admission_type(db: Session):
    try:
        query = db.query(IEMSAdmissionType).filter(IEMSAdmissionType.status == 1)
        results = query.all()
        data= [{"admission_type_id": item.admission_type_id, "admission_type": item.admission_type} for item in results]
        return (data)
    except Exception as e:
        raise e
    
def get_occupation_list(db: Session):
    try:
        query = db.query(IEMParentsOccupationMaster).filter(IEMParentsOccupationMaster.status == 1)
        results = query.all()
        data= [{"occupation_id": item.occupation_id, "occupation_description": item.occupation_description} for item in results]
        return data
    except Exception as e:
        raise e
    
def get_education_details(db: Session):
    try:
        education_details = db.query(IEMSEducationQualificationMaster).filter(IEMSEducationQualificationMaster.education_qualification_code.isnot(None)).all()
        data = [{"education_qualification_code": detail.education_qualification_code} for detail in education_details]
        return data
    except Exception as e:
        raise e

# def get_physically_challenged_descriptions(db: Session):
#     try:
#         descriptions = db.query(PhysicallyChallengedDescription).all()
#         data = [{"pc_description_id": desc.pc_description_id, "description": desc.description} for desc in descriptions]
#         return data
#     except Exception as e:
#         raise e
    
def get_physically_challenged(db: Session):
    try:
        descriptions = db.query(PhysicallyChallengedDescription).all()
        data = [{"pc_description_id": desc.pc_description_id, "description": desc.description} for desc in descriptions]
        return data
    except Exception as e:
        raise e
    
def get_certificate(db: Session):
    try:
        certificates = db.query(IEMSCertificateTypeMaster).filter(IEMSCertificateTypeMaster.certificate_description.isnot(None)).all()
        data=[{"certificate_description": certificate.certificate_description} for certificate in certificates]
        return data
    except Exception as e:
        raise e
    
def get_coursetype_cia_marks(db: Session):
    try:
        data_list = fetch_coursetype_cia_marks(db)
        course_data = [{"course_type_code": category.course_type_code,"cia_max_marks": category.cia_max_marks,"cia_weightage": category.cia_weightage,"see_max_marks": category.see_max_marks,"see_min_marks": category.see_min_marks,"see_weightage": category.see_weightage,"min_passing_marks": category.min_passing_marks,"total_classes": category.total_classes} for category in data_list]
        return (course_data)
    except Exception as e:
        raise e

def fetch_coursetype_cia_marks(db: Session):
    return db.query(IEMSCourseType.course_type_code,IEMSCourseType.cia_max_marks,IEMSCourseType.cia_weightage,IEMSCourseType.cia_max_marks,
    IEMSCourseType.see_min_marks,IEMSCourseType.see_weightage,
    IEMSCourseType.see_max_marks,IEMSCourseType.total_classes,
    IEMSCourseType.min_passing_marks
    ,IEMSCourseType.cia_min_marks).all()

def academic_year() :
    """
    Generates a list of academic years from (current year - 8) to current year.
    """
    current_year = datetime.now().year
    start_year = current_year - 8
    end_year = current_year

    academic_year_list = [f"{year}-{year + 1}" for year in range(start_year, end_year + 1)]
    return academic_year_list

def generate_random_string(length: int = 10) -> str:
    """
    Generates a random alphanumeric string.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
