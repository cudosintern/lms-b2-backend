FACULTY_TYPE_MAP = {
    "Teaching": 1,
    "Lab": 2,
    "Administration": 3,
    "Supporting": 4,
    "Visiting": 5
}

def map_faculty_type_to_id(faculty_type: str | None) -> int | None:
    if not faculty_type:
        return None
    return FACULTY_TYPE_MAP.get(faculty_type.strip())

def get_faculty_type_name(faculty_type_id: int | None) -> str | None:
    if not faculty_type_id:
        return None
    for name, id_ in FACULTY_TYPE_MAP.items():
        if id_ == faculty_type_id:
            return name
    return None
