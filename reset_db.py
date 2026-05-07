from database import engine, Base
import models 

print("⏳ Purani tables delete ho rahi hain...")
Base.metadata.drop_all(bind=engine)

print("🛠️ Nayi tables naye columns ke sath ban rahi hain...")
Base.metadata.create_all(bind=engine)

print("✅ Database ekdum fresh aur ready hai! Ab error nahi aayega.")