"""
Test cases for Program Outcome CRUD APIs
This file demonstrates how to test the Program Outcome endpoints
"""

import requests
import json

# Base API URL (adjust based on your environment)
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/program_outcome"

# Sample test data
def test_create_program_outcome():
    """Test creating a new Program Outcome"""
    headers = {
        "Content-Type": "application/json",
        # Include your auth token here
    }
    
    payload = {
        "po_type": "Knowledge",
        "po_description": "Students will have knowledge of fundamental concepts",
        "status": 1
    }
    
    response = requests.post(
        API_ENDPOINT,
        headers=headers,
        json=payload
    )
    
    print("CREATE Response Status:", response.status_code)
    print("CREATE Response:", json.dumps(response.json(), indent=2))
    return response.json()


def test_list_program_outcomes():
    """Test listing all Program Outcomes"""
    params = {
        "skip": 0,
        "limit": 100,
        "status": 1  # Optional: filter by status
    }
    
    response = requests.get(
        API_ENDPOINT,
        params=params
    )
    
    print("LIST Response Status:", response.status_code)
    print("LIST Response:", json.dumps(response.json(), indent=2))
    return response.json()


def test_get_program_outcome_detail(po_id):
    """Test fetching a single Program Outcome"""
    response = requests.get(f"{API_ENDPOINT}/{po_id}")
    
    print(f"GET Detail Response Status:", response.status_code)
    print(f"GET Detail Response:", json.dumps(response.json(), indent=2))
    return response.json()


def test_update_program_outcome(po_id):
    """Test updating a Program Outcome"""
    headers = {
        "Content-Type": "application/json",
        # Include your auth token here
    }
    
    payload = {
        "po_type": "Knowledge (Updated)",
        "po_description": "Updated description for Program Outcome",
        "status": 1
    }
    
    response = requests.put(
        f"{API_ENDPOINT}/{po_id}",
        headers=headers,
        json=payload
    )
    
    print(f"UPDATE Response Status:", response.status_code)
    print(f"UPDATE Response:", json.dumps(response.json(), indent=2))
    return response.json()


def test_delete_program_outcome(po_id):
    """Test deleting a Program Outcome (soft delete)"""
    headers = {
        "Content-Type": "application/json",
        # Include your auth token here
    }
    
    response = requests.delete(
        f"{API_ENDPOINT}/{po_id}",
        headers=headers
    )
    
    print(f"DELETE Response Status:", response.status_code)
    print(f"DELETE Response:", json.dumps(response.json(), indent=2))
    return response.json()


if __name__ == "__main__":
    print("=" * 60)
    print("Program Outcome API Testing")
    print("=" * 60)
    
    # Test Create
    print("\n1. Testing CREATE...")
    create_result = test_create_program_outcome()
    po_id = create_result.get('data', {}).get('po_id') if create_result.get('status') else None
    
    if po_id:
        # Test List
        print("\n2. Testing LIST...")
        test_list_program_outcomes()
        
        # Test Get Detail
        print(f"\n3. Testing GET DETAIL (po_id={po_id})...")
        test_get_program_outcome_detail(po_id)
        
        # Test Update
        print(f"\n4. Testing UPDATE (po_id={po_id})...")
        test_update_program_outcome(po_id)
        
        # Test Delete
        print(f"\n5. Testing DELETE (po_id={po_id})...")
        test_delete_program_outcome(po_id)
    
    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)
