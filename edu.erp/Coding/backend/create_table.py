from app.core.database import engine
from app.db.models import Base

print("Creating all missing tables...")
Base.metadata.create_all(engine)
print("All missing tables created successfully!")
