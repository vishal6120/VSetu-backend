from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from security import get_password_hash

# 👇 YAHAN APNA 'EXTERNAL DATABASE URL' PASTE KIJIYE 👇
EXTERNAL_URL = "postgresql://sahayak_db_719c_user:OEiUlDEOXt7DLfPNPRHU9Vp7QEPPocX1@dpg-d7uc4f67r5hc73bj0j6g-a.virginia-postgres.render.com/sahayak_db_719c"

# SQLAlchemy ka nakhra theek karne ke liye
if EXTERNAL_URL.startswith("postgres://"):
    EXTERNAL_URL = EXTERNAL_URL.replace("postgres://", "postgresql://", 1)

# Cloud Database se direct connection banana
engine = create_engine(EXTERNAL_URL)
models.Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def create_cloud_staff():
    try:
        # 1. Founder (Aapka Khazana)
        founder = models.User(username="founder", hashed_password=get_password_hash("founder123"), role="superadmin")
        db.add(founder)

        # 2. Manager (Amit)
        manager = models.User(username="manager_amit", hashed_password=get_password_hash("manager123"), role="admin")
        db.add(manager)

        # 3. Technician (Raju)
        tech = models.User(username="tech_raju", hashed_password=get_password_hash("raju123"), role="technician")
        db.add(tech)

        db.commit()
        print("✅ Badhai ho! Cloud Database mein teeno accounts (Founder, Manager, Tech) ban gaye hain!")
    except Exception as e:
        print("⚠️ Kuch gadbad hui (Shayad accounts pehle se hain):", e)
    finally:
        db.close()

if __name__ == "__main__":
    create_cloud_staff()