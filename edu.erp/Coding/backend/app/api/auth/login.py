from hashlib import sha1
from fastapi import APIRouter

from ...utils.comman_function import all_masters_list, fetch_role_list, fetch_user_type, get_academics_event, \
    get_academics_event_status, get_admission_type, get_blood_group_list_options, get_caste_list, get_category_options, \
    get_certificate, get_coursetype_cia_marks, get_coursetype_list_options, get_coursetype_options, \
    get_education_details, get_event_status_options, get_grade_type_list, get_hall_type_list, get_occupation_list, \
    get_parents_occupation_master_list, get_physically_challenged_descriptions, get_quota, get_section_list_options, \
    get_user_designation, get_user_org_role, organization_list, priority_list, religion_list
from ...api.auth.login_schema import LoginDataRequest
from ...utils.http_return_helper import returnException, returnSuccess
from ...db.models import IEMOrganisation, IEMSUserOrg, IEMSUsers
# from app.api.v1.admission_module.models.admission_models import StudentLogin, Student
# from app.api.v1.admission_module.utils.common import c_decode
from fastapi import Depends
from sqlalchemy.orm import Session
from ...core.database import get_db
from datetime import datetime, timedelta
from jose import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS") or 24)

router = APIRouter()


# Function to create JWT token
def create_access_token(user: IEMSUsers, expires_delta: timedelta | None = None) -> str:
    to_encode = {
        "username": user.username,
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "user_type": user.user_type,
        "super_admin": user.super_admin,
        "technical_admin": user.technical_admin,
        "status": user.status,
        "exp": datetime.utcnow() + (expires_delta if expires_delta else timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_staff(username: str, password: str, db: Session):
    user = db.query(IEMSUsers).filter(IEMSUsers.username == username).first()
    if not user:
        return None
    return user


@router.post("/staff_login")
async def staff_login(login_data: LoginDataRequest, db: Session = Depends(get_db)):
    user = authenticate_staff(login_data.username, login_data.password, db)

    if user is None:
        return returnException("Incorrect username or password")
    # Get the stored salt and password hash from the user object
    stored_password_hash = user.password
    stored_salt = user.salt
    # Hash the entered password with the stored salt
    entered_password_hash = sha1(f"{stored_salt}{login_data.password}".encode()).hexdigest()
    # Compare the hashes
    if entered_password_hash != stored_password_hash:
        return returnException("Incorrect username or password")

    # Check the user's type and get their organizations
    org_data = check_user_type(login_data.username, db)

    # Create the JWT token
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(user, expires_delta=access_token_expires)

    data = {
        "access_token": access_token,
        "token_type": "bearer",
        "org_data": org_data,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "options": {
            "user_type": fetch_user_type(),
            "role_list": fetch_role_list(db),
            "designations": get_user_designation(db),
            "organisations": organization_list(db),
            "all_masters_list": all_masters_list(db),
            "get_hall_type_list": get_hall_type_list(db),
            "priority_list": priority_list(db),
            "get_academics_event_status": get_academics_event_status(db),
            "get_academics_event": get_academics_event(db),
            "get_grade_type_list": get_grade_type_list(db),
            "get_coursetype_list": get_coursetype_list_options(),
            "get_coursetype_options": get_coursetype_options(),
            "get_event_status_options": get_event_status_options(),
            "get_section_list_options": get_section_list_options(db),
            "get_category_options": get_category_options(db),
            "get_religion_list": religion_list(db),
            "get_caste_list": get_caste_list(db),
            "get_quota_list": get_quota(db),
            "get_blood_group_list_options": get_blood_group_list_options(),
            "get_admission_type_list": get_admission_type(db),
            "get_occupation_list": get_occupation_list(db),
            "get_education_details_list": get_education_details(db),
            "get_physically_cha_desc_list": get_physically_challenged_descriptions(db),
            "get_certificate_list": get_certificate(db),
            "get_coursetype_cia_marks": get_coursetype_cia_marks(db)
        }
    }
    return returnSuccess(data)


def check_user_type(username: str, db: Session):
    user = db.query(IEMSUsers).filter(IEMSUsers.username == username).first()
    if not user:
        return returnException("User not found")

    # if user.user_type == 'U':
    if user.user_type in ('U', 'O'):
        orgs = db.query(IEMOrganisation).filter(IEMOrganisation.org_id == user.org_id).all()
        org_data = [{"label": org.org_name, "value": org.org_id} for org in orgs if org.org_name]

        return org_data
    return [{'label': 'O', 'value': None}]

# @router.post("/student_login")
# async def student_login(login_data: LoginDataRequest, db: Session = Depends(get_db)):
#     user = authenticate_student(login_data.username, login_data.password, db)

#     if user is None:
#         return returnException("Incorrect username or password")

#     # Get the stored salt and password hash from the user object
#     user_password = user.password
#     # Hash the entered password with the stored salt
#     entered_password_hash = c_decode(user_password)

#     # Compare the hashes
#     if entered_password_hash != login_data.password:
#         return returnException("Incorrect username or password")

#      # Check the user's type and get their organizations
#     org_data = validate_user_type(login_data.username, db)

#     # Create the JWT token
#     access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
#     access_token = create_access_token_for_student(user,userName=login_data.username, expires_delta=access_token_expires)

#     data= {
#         "access_token": access_token,
#         "token_type": "bearer",
#         "org_data": org_data,
#         "student_id": user.student_id,
#         "username": user.email,
#         "first_name": user.first_name,
#         "last_name": user.last_name,
#         "email": user.email,
#         "options": {
#             "user_type": fetch_user_type(),
#             "role_list": fetch_role_list(db),
#             "designations": get_user_designation(db),
#             "organisations": organization_list(db),
#             "get_category_options":get_category_options(db),
#             "get_religion_list":religion_list(db),
#             "get_caste_list":get_caste_list(db),
#             "get_quota_list":get_quota(db),
#             "get_blood_group_list_options":get_blood_group_list_options(),
#             "get_admission_type_list": get_admission_type(db),
#             "get_occupation_list": get_occupation_list(db),
#             "get_education_details_list": get_education_details(db),
#             # "get_physically_cha_desc_list": get_physically_challenged_descriptions(db),
#             "get_certificate_list": get_certificate(db),
#             "get_coursetype_cia_marks": get_coursetype_cia_marks(db)
#         }
#     }
#     return returnSuccess(data)

# def authenticate_student(username: str, password: str, db: Session):
#     user = db.query(StudentLogin).filter(
#         (StudentLogin.email == username) | (StudentLogin.login_id == username)
#     ).first()
#     if not user :
#         return None
#     return user

# def validate_user_type(username: str, db: Session):
#     user = db.query(StudentLogin).filter(
#         (StudentLogin.email == username) | (StudentLogin.login_id == username)
#     ).first()
#     if not user:
#         return returnException("User not found")

#     if user.user_type != 'student':
#          return returnException("Role not matched")


#     student_data = db.query(Student).filter(Student.student_id == user.user_id).first()

#     if student_data:
#         orgs = db.query(IEMOrganisation).filter(IEMOrganisation.org_id == student_data.org_id).all()
#         org_data = [{"label": org.org_name, "value": org.org_id} for org in orgs if org.org_name]
#         return org_data
#     else:
#         return []


#     return [{'label': 'O', 'value': None}]
#     # return [{'label': 'student', 'value': None}]

# def create_access_token_for_student(user: StudentLogin,userName: any, expires_delta: timedelta | None = None) -> str:
#     to_encode = {
#         "username": userName,
#         "id": user.user_id,
#         "first_name": user.first_name,
#         "last_name": user.last_name,
#         "email": user.email,
#         "user_type": user.user_type,
#         "status": user.status,
#         "exp": datetime.utcnow() + (expires_delta if expires_delta else timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
#     }
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)