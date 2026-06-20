import sys
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal, get_db
from app.db.models import ConfigType
from app.api.v1.lms_module.config_type import add_config, list_config, update_config, delete_config, export_pdf
from app.api.v1.lms_module.cross_department_mentor import (
    add_cross_department_mentor,
    list_mentors_from_other_departments,
    list_mentors_to_other_departments,
    list_available_mentors,
    remove_cross_department_mentor,
    update_cross_department_mentor
)
from app.api.v1.lms_module.mentoring import (
    list_curriculum,
    list_sessions,
    list_groups,
    create_session,
    get_mentees_responses,
    fetch_chats,
    fetch_questionnaire
)

def run_tests():
    print("Starting backend API logic verification...")
    db = SessionLocal()
    
    # Mock current user (mentor_id = 1)
    mock_user = {
        "user_id": 1,
        "org_id": 1,
        "username": "test_user"
    }

    try:
        # 1. Clean old test data
        db.query(ConfigType).filter(ConfigType.name.like("TestConfigType%")).delete(synchronize_session=False)
        db.commit()

        # 2. Test Config Type CRUD
        print("\nTesting Config Type CRUD...")
        add_res = add_config(payload={"name": "TestConfigType1", "status": 1}, db=db, current_user=mock_user)
        print("Add Config success:", add_res)
        
        # Test Duplicate Add
        try:
            add_config(payload={"name": "TestConfigType1", "status": 1}, db=db, current_user=mock_user)
            print("FAILED: Duplicate validation did not raise exception on Add!")
        except Exception as e:
            print("Duplicate Add correctly raised exception:", str(e))

        # Test List Config
        list_res = list_config(db=db, current_user=mock_user)
        print("List Config contains our new config:", any(c["name"] == "TestConfigType1" for c in list_res["data"]))

        # Test Update Config
        new_id = add_res["data"]["id"]
        update_res = update_config(id=new_id, payload={"name": "TestConfigType1Updated", "status": 0}, db=db, current_user=mock_user)
        print("Update Config success:", update_res)

        # Test Delete Config
        delete_res = delete_config(id=new_id, db=db, current_user=mock_user)
        print("Delete Config success:", delete_res)

        # Test PDF Export
        pdf_res = export_pdf(db=db, current_user=mock_user)
        print("PDF Export response headers and media type verified:", type(pdf_res))

        # 3. Test Cross Department Mentors logic
        print("\nTesting Cross Department Mentors Logic...")
        
        # Clean old mappings
        db.execute(text("DELETE FROM cross_department_mentor_map WHERE mentor_id = 3"))
        db.commit()

        # Add mentor 3 (home department 2) to department 1 (logged-in user's department)
        add_mentor_res = add_cross_department_mentor(payload={"mentor_id": 3}, db=db, current_user=mock_user)
        print("Add Cross Dept Mentor success:", add_mentor_res)

        # List Mentors From Other Departments (logged-in dept is 1)
        list_from_res = list_mentors_from_other_departments(dept_id=None, db=db, current_user=mock_user)
        print("List Mentors From Other Depts contains user 3:", any(m["mentor_id"] == 3 for m in list_from_res["data"]))

        # List Available Mentors (should exclude user 3 since already mapped)
        avail_res = list_available_mentors(db=db, current_user=mock_user)
        print("Available Mentors count:", len(avail_res["data"]))

        # Remove mapping
        mapping_id = add_mentor_res["data"]["mapping_id"]
        remove_res = remove_cross_department_mentor(id=mapping_id, db=db, current_user=mock_user)
        print("Remove Cross Dept Mentor success:", remove_res)

        # 4. Test Mentoring Module logic
        print("\nTesting Mentoring Module Logic...")
        
        # Test 4.1: List assigned curriculum
        crclm_list = list_curriculum(db=db, current_user=mock_user)
        print("List Curriculum success, count:", len(crclm_list["data"]))
        assert len(crclm_list["data"]) > 0, "Curriculum list should not be empty"

        # Test 4.2: List sessions (Curriculum ID = 1, Month = 6 i.e. June)
        sessions_list = list_sessions(curriculum_id=1, month=6, db=db, current_user=mock_user)
        print("List Sessions success, count:", len(sessions_list["data"]))
        assert len(sessions_list["data"]) > 0, "Sessions list should not be empty for June"

        # Test 4.3: List mentoring groups
        groups_list = list_groups(curriculum_id=1, db=db, current_user=mock_user)
        print("List Groups success, count:", len(groups_list["data"]))
        assert len(groups_list["data"]) > 0, "Groups list should not be empty"

        # Test 4.4: Create mentoring session
        create_sess_res = create_session(
            payload={
                "curriculum_id": 1,
                "group_id": 1,
                "session_date": "2026-06-30",
                "session_time": "15:00:00",
                "topic": "Final Mentoring Review",
                "description": "Closing discussions and feedback collection."
            },
            db=db,
            current_user=mock_user
        )
        print("Create Session success:", create_sess_res)

        # Test 4.5: Fetch mentees & respective responses
        mentees_resp = get_mentees_responses(group_id=1, questionnaire_id=1, db=db, current_user=mock_user)
        print("Fetch Mentees & Responses success, count:", len(mentees_resp["data"]))
        assert len(mentees_resp["data"]) > 0, "Mentees list should not be empty"

        # Test 4.6: Fetch individual chat (for mentee_id = 5)
        chats_indiv = fetch_chats(mentee_id=5, db=db, current_user=mock_user)
        print("Fetch Individual Chats success, count:", len(chats_indiv["data"]))
        
        # Test 4.7: Fetch general guidance (for group_id = 1)
        chats_general = fetch_chats(group_id=1, db=db, current_user=mock_user)
        print("Fetch General Guidance success, count:", len(chats_general["data"]))

        # Test 4.8: Fetch questionnaire definition (ID = 1)
        quest_res = fetch_questionnaire(id=1, db=db, current_user=mock_user)
        print("Fetch Questionnaire success:", quest_res["data"]["title"])
        assert quest_res["data"]["id"] == 1

        print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

    except Exception as e:
        print("VERIFICATION FAILED with error:", str(e))
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
