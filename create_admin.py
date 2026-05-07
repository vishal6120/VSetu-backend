from database import SessionLocal
from models import User
from security import get_password_hash

def create_super_admin():
    # Database ka darwaza kholo
    db = SessionLocal()

    # Check karo ki kya admin pehle se toh nahi bana hua
    existing_user = db.query(User).filter(User.username == "founder").first()

    if existing_user:
        print("⚠️ Super Admin pehle se database mein maujood hai!")
        return

    # Naya ID, Password aur Role set karo
    # IMPORTANT: 'founder123' ki jagah aap apna koi strong password rakh sakte hain
    hashed_pw = get_password_hash("founder123") 

    new_admin = User(
        username="founder", 
        hashed_password=hashed_pw, 
        role="superadmin"
    )

    # Database mein save kar do
    db.add(new_admin)
    db.commit()
    db.close()

    print("✅ Badhai ho! Pehla Super Admin account safaltapurvak ban gaya hai!")

# Script ko chalao
if __name__ == "__main__":
    create_super_admin()