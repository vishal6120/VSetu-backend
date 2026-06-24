from database import engine
import models

print("Purani tables delete kar rahe hain...")
models.Base.metadata.drop_all(bind=engine)

print("Nayi tables (Trade column ke sath) bana rahe hain...")
models.Base.metadata.create_all(bind=engine)

print("✅ Database successfully reset ho gaya!")