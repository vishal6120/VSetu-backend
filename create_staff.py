from database import SessionLocal
from models import User
from security import get_password_hash

def create_staff_accounts():
    db = SessionLocal()

    # 1. Manager ka Account
    manager_pw = get_password_hash("manager123")
    manager = User(username="manager_amit", hashed_password=manager_pw, role="admin")

    # 2. Technician (Raju) ka Account
    tech_pw = get_password_hash("raju123")
    technician = User(username="tech_raju", hashed_password=tech_pw, role="technician")

    try:
        # Dono ko database mein save kar do
        db.add(manager)
        db.add(technician)
        db.commit()
        print("✅ Badhai ho! Ek Manager aur Ek Technician hire ho gaye hain!")
    except Exception as e:
        print("⚠️ Kuch gadbad hui (Shayad accounts pehle se hain):", e)
    finally:
        db.close()

if __name__ == "__main__":
    create_staff_accounts()