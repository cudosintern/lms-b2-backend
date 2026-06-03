# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from app.core.database import get_db
# from app.utils.set_password_helper import set_private_password

# # from app.api.v1.cudo_module.board_of_studies.model.bos_member_model import BoSMember
# from app.db.models import iems_users as BoSMember
# from app.api.v1.cudo_module.board_of_studies.schema.bos_member_schema import (
#     BoSMemberCreate,
#     BoSMemberUpdate,
#     BoSMemberResponse
# )
# from typing import List

# router = APIRouter()


# # ADD BoS MEMBER
# @router.post("/add")
# def add_bos_member(data: BoSMemberCreate, db: Session = Depends(get_db)):

#     if db.query(BoSMember).filter(BoSMember.email == data.email).first():
#         raise HTTPException(status_code=400, detail="Email already exists")

#     #  Generate password + salt
#     password_data = set_private_password(data.email)

#     member = BoSMember(
#         faculty_type=data.faculty_type,
#         title=data.title,
#         first_name=data.first_name,
#         middle_name=data.middle_name,
#         last_name=data.last_name,
#         organization=data.organization,
#         email=data.email,
#         contact_number=data.contact_number,
#         aadhaar_number=data.aadhaar_number,
#         highest_qualification=data.highest_qualification,
#         experience_years=data.experience_years,

#         password_hash=password_data["password"],  
#         salt=password_data["salt"],                

#         designation=data.designation,
#         bos_for=data.bos_for
#     )

#     db.add(member)
#     db.commit()
#     return {"status": True, "message": "BoS member added successfully"}


# # GET ALL BoS MEMBERS
# @router.get("/", response_model=List[BoSMemberResponse])
# def get_all_bos_members(db: Session = Depends(get_db)):
#     members = db.query(BoSMember).all()
#     return members


# # GET SINGLE BoS MEMBER
# @router.get("/{member_id}", response_model=BoSMemberResponse)
# def get_bos_member(member_id: int, db: Session = Depends(get_db)):
#     member = db.query(BoSMember).filter(BoSMember.id == member_id).first()
#     if not member:
#         raise HTTPException(status_code=404, detail="BoS member not found")
#     return member


# # EDIT BoS MEMBER
# @router.put("/edit/{member_id}")
# def edit_bos_member(member_id: int, data: BoSMemberUpdate, db: Session = Depends(get_db)):

#     member = db.query(BoSMember).filter(BoSMember.id == member_id).first()
#     if not member:
#         raise HTTPException(status_code=404, detail="BoS member not found")

#     for key, value in data.dict(exclude_unset=True).items():
#         setattr(member, key, value)

#     db.commit()
#     return {"status": True, "message": "BoS member updated successfully"}


# # DELETE BoS MEMBER
# @router.delete("/{member_id}")
# def delete_bos_member(member_id: int, db: Session = Depends(get_db)):
#     member = db.query(BoSMember).filter(BoSMember.id == member_id).first()
#     if not member:
#         raise HTTPException(status_code=404, detail="BoS member not found")
    
#     db.delete(member)
#     db.commit()
#     return {"status": True, "message": "BoS member deleted successfully"}


# # activation and deactivation of BoS MEMBER
# @router.put("/toggle-status/{member_id}")
# def toggle_bos_member_status(member_id: int, db: Session = Depends(get_db)):

#     member = db.query(BoSMember).filter(BoSMember.id == member_id).first()
#     if not member:
#         raise HTTPException(status_code=404, detail="BoS member not found")

#     member.status = 0 if member.status == 1 else 1
#     db.commit()

#     return {
#         "status": True,
#         "message": "BoS member status updated successfully",
#         "new_status": member.status
#     }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.core.database import get_db
from app.db.models import IEMSUsers, CUDOSBoS, IEMSDepartment, IEMSUserDesignation
from app.api.v1.cudo_module.board_of_studies.schema.bos_member_schema import BoSCreate, BoSUpdate, BoSResponse, DesignationResponse, UsersByDeptReq, UserResponse, AddExistingBoS, UsersAndBoSByDeptResponse
from app.api.v1.cudo_module.board_of_studies.faculty_helper import map_faculty_type_to_id, get_faculty_type_name
from app.utils.set_password_helper import set_private_password

router = APIRouter()
# list the designation
@router.get("/designations", response_model=List[DesignationResponse])
def get_designations(db: Session = Depends(get_db)):
    designations = db.query(IEMSUserDesignation).all()
    return designations

# list the users and bos members by department
@router.post("/users_by_dept", response_model=List[UserResponse])
def get_users_by_dept(payload: UsersByDeptReq, db: Session = Depends(get_db)):
    print(f"DEBUG: users_by_dept called with dept_id: {payload.dept_id}")
    users = db.query(IEMSUsers).filter(
        IEMSUsers.user_dept_id == payload.dept_id,
        IEMSUsers.status == 1 # Active users only?
    ).all()
    print(f"DEBUG: Found {len(users)} users for dept {payload.dept_id}")
    
    response = []
    for user in users:
        response.append({
            "user_id": user.id,
            "username": user.username if user.username else "",
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        })
    return response
# @router.post("/users_by_dept",response_model=UsersAndBoSByDeptResponse)
# def get_users_and_bos_by_dept(
#     payload: UsersByDeptReq,
#     db: Session = Depends(get_db)
# ):
#     users = db.query(IEMSUsers).filter(
#         IEMSUsers.user_dept_id == payload.dept_id,
#         IEMSUsers.status == 1
#     ).all()

#     bos_members = db.query(CUDOSBoS).filter(
#         CUDOSBoS.bos_dept_id == payload.dept_id
#     ).all()

#     return {
#         "dept_id": payload.dept_id,
#         "users": [
#             {
#                 "user_id": u.id,
#                 "username": u.username,
#                 "email": u.email,
#                 "first_name": u.first_name,
#                 "last_name": u.last_name
#             }
#             for u in users
#         ],
#         "bos_members": [
#             {
#                 "bos_id": b.bos_id,
#                 "user_id": b.bos_user_id
#             }
#             for b in bos_members
#         ]
#     }


# add existing bos member   
@router.post("/add_existing")
def add_existing_bos_member(payload: AddExistingBoS, db: Session = Depends(get_db)):
    # Verify User exists
    user = db.query(IEMSUsers).filter(IEMSUsers.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify existing membership
    existing = db.query(CUDOSBoS).filter(
        CUDOSBoS.bos_user_id == payload.user_id,
        CUDOSBoS.bos_dept_id == payload.bos_dept_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this BoS")

    # Create mapping
    bos = CUDOSBoS(
        bos_user_id=user.id,
        bos_dept_id=payload.bos_dept_id,
        create_by=payload.user_id, # Or verified current_user if available, simplified here
        create_date=date.today()
    )

    db.add(bos)
    db.commit()
    
    return {"message": "Existing user added to BoS successfully", "bos_id": bos.bos_id}

# create new bos member
@router.post("/create")
def create_bos(payload: BoSCreate, db: Session = Depends(get_db)):

    # 🔹 Resolve department string → ID
    department = db.query(IEMSDepartment).filter(
        IEMSDepartment.dept_name == payload.bos_for
    ).first()
    
    # Try ID if name failed (fallback)
    if not department and payload.bos_for.isdigit():
         department = db.query(IEMSDepartment).filter(IEMSDepartment.dept_id == int(payload.bos_for)).first()

    if not department:
        print(f"DEBUG: Department not found for bos_for: {payload.bos_for}")
        raise HTTPException(status_code=400, detail=f"Invalid BoS For (Department not found: {payload.bos_for})")

    bos_dept_id = department.dept_id

    # 🔹 Verify designation exists
    print(f"DEBUG: Designation payload: {payload.designation}")
    try:
        designation_id = int(payload.designation)
        designation = db.query(IEMSUserDesignation).filter(IEMSUserDesignation.designation_id == designation_id).first()
        if not designation:
             print(f"DEBUG: Designation not found for ID: {designation_id}")
             raise HTTPException(status_code=400, detail="Invalid Designation ID")
    except ValueError:
         print(f"DEBUG: Designation ID ValueError: {payload.designation}")
         raise HTTPException(status_code=400, detail="Designation must be a valid ID")
    
    # 🔹 Map faculty type string → ID
    print(f"DEBUG: Mapping faculty type: {payload.faculty_type}")
    faculty_type_id = map_faculty_type_to_id(payload.faculty_type)
    
    # Check if email already exists
    print(f"DEBUG: Checking email existence: {payload.email}")
    if db.query(IEMSUsers).filter(IEMSUsers.email == payload.email).first():
        print(f"DEBUG: Email already exists: {payload.email}")
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = set_private_password(payload.password)
    
    # 🔹 Create user
    user = IEMSUsers(
        email=payload.email,
        username=payload.email,
        password=hashed_password["password"],   # ✅ string
        salt=hashed_password["salt"],
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        mobile=payload.mobile,
        aadhar_number=payload.aadhar_number,
        faculty_type=faculty_type_id,
        user_qualification=payload.highest_qualification,  # ✅ Mapped to String column
        user_experience=payload.experience,
        user_dept_id=bos_dept_id, # ✅ Assign user to the department
        designation_id=designation_id,
        user_type="B",
        org_id=None,  # ✅ Set to None to avoid FK error for external users
        organization_name=payload.organization,
        create_date=date.today(),
        status=1
    )

    db.add(user)
    db.flush()   # 👈 get user.id

    # 🔹 Create BoS mapping
    bos = CUDOSBoS(
        bos_user_id=user.id,
        bos_dept_id=bos_dept_id,
        create_by=user.id,
        create_date=date.today()
    )

    db.add(bos)
    db.commit()
    db.refresh(user)
    db.refresh(bos)

    return {
        "message": "BoS created successfully",
        "user_id": user.id,
        "bos_id": bos.bos_id
    }

# list the bos members
@router.get("/list", response_model=List[BoSResponse])
def list_bos(db: Session = Depends(get_db)):
    # Join with IEMSUserDesignation to get designation name
    results = db.query(CUDOSBoS, IEMSUsers, IEMSDepartment.dept_name, IEMSUserDesignation.designation_name)\
        .join(IEMSUsers, CUDOSBoS.bos_user_id == IEMSUsers.id)\
        .join(IEMSDepartment, CUDOSBoS.bos_dept_id == IEMSDepartment.dept_id)\
        .outerjoin(IEMSUserDesignation, IEMSUsers.designation_id == IEMSUserDesignation.designation_id)\
        .all()
        
    response = []
    for bos, user, dept_name, designation_name in results:
        response.append({
            "bos_id": bos.bos_id,
            "user_id": user.id,
            "faculty_type": get_faculty_type_name(user.faculty_type),
            "title": user.title,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "organization": user.organization_name,
            "org_id": user.org_id,
            "email": user.email,
            "mobile": user.mobile,
            "aadhar_number": user.aadhar_number,
            "highest_qualification": user.user_qualification,
            "experience": user.user_experience,
            "designation": designation_name, # Return name for display
            "designation_id": user.designation_id, # Return ID for edit
            "bos_for": dept_name,
            "status": user.status,
            "create_date": bos.create_date
        })
    return response


# get single bos member
@router.get("/{bos_id}", response_model=BoSResponse)
def get_bos(bos_id: int, db: Session = Depends(get_db)):
    result = db.query(CUDOSBoS, IEMSUsers, IEMSDepartment.dept_name, IEMSUserDesignation.designation_name)\
        .join(IEMSUsers, CUDOSBoS.bos_user_id == IEMSUsers.id)\
        .join(IEMSDepartment, CUDOSBoS.bos_dept_id == IEMSDepartment.dept_id)\
        .outerjoin(IEMSUserDesignation, IEMSUsers.designation_id == IEMSUserDesignation.designation_id)\
        .filter(CUDOSBoS.bos_id == bos_id).first()
        
    if not result:
        raise HTTPException(status_code=404, detail="BoS not found")
        
    bos, user, dept_name, designation_name = result
    
    return {
        "bos_id": bos.bos_id,
        "user_id": user.id,
        "faculty_type": get_faculty_type_name(user.faculty_type),
        "title": user.title,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "last_name": user.last_name,
        "organization": user.organization_name,
        "org_id": user.org_id,
        "email": user.email,
        "mobile": user.mobile,
        "aadhar_number": user.aadhar_number,
        "highest_qualification": user.user_qualification,
        "experience": user.user_experience,
        "designation": designation_name,
        "designation_id": user.designation_id,
        "bos_for": dept_name,
        "status": user.status,
        "create_date": bos.create_date
    }


# update bos member
@router.put("/{bos_id}")
def update_bos(bos_id: int, payload: BoSUpdate, db: Session = Depends(get_db)):
    print(f"DEBUG: update_bos payload: {payload.dict(exclude_unset=True)}")
    bos = db.query(CUDOSBoS).filter(CUDOSBoS.bos_id == bos_id).first()
    if not bos:
        raise HTTPException(status_code=404, detail="BoS not found")

    user = db.query(IEMSUsers).filter(IEMSUsers.id == bos.bos_user_id).first()
    if not user:
         raise HTTPException(status_code=404, detail="Associated User not found")

    if payload.bos_for:
        dept = db.query(IEMSDepartment).filter(
            IEMSDepartment.dept_name == payload.bos_for
        ).first()
        if not dept:
            raise HTTPException(status_code=400, detail="Invalid BoS For (Department not found)")
        bos.bos_dept_id = dept.dept_id
        user.user_dept_id = dept.dept_id # ✅ Sync user department

    if payload.designation:
        try:
            designation_id = int(payload.designation)
            designation = db.query(IEMSUserDesignation).filter(IEMSUserDesignation.designation_id == designation_id).first()
            if not designation:
                 raise HTTPException(status_code=400, detail="Invalid Designation ID")
            user.designation_id = designation_id
        except ValueError:
             # Just in case string name is sent, but we prefer ID. 
             # If we want to support both during transition? No, strict ID is safer for new model.
             pass

    if payload.faculty_type:
        user.faculty_type = map_faculty_type_to_id(payload.faculty_type)

    # Update User fields
    if payload.first_name: user.first_name = payload.first_name
    if payload.middle_name: user.middle_name = payload.middle_name
    if payload.last_name: user.last_name = payload.last_name
    if payload.email: user.email = payload.email
    if payload.mobile: user.mobile = payload.mobile
    if payload.aadhar_number: user.aadhar_number = payload.aadhar_number
    if payload.title: user.title = payload.title
    if payload.highest_qualification: user.user_qualification = payload.highest_qualification
    if payload.experience: user.user_experience = payload.experience
    if payload.organization: user.organization_name = payload.organization

    bos.modified_by = user.id
    bos.modify_date = date.today()

    db.commit()
    return {"message": "BoS updated successfully"}


# delete bos member
@router.delete("/{bos_id}")
def delete_bos(bos_id: int, db: Session = Depends(get_db)):

    bos = db.query(CUDOSBoS).filter(CUDOSBoS.bos_id == bos_id).first()
    if not bos:
        raise HTTPException(status_code=404, detail="BoS not found")

    db.delete(bos)
    db.commit()
    return {"message": "BoS deleted successfully"}

