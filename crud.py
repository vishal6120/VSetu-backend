from sqlalchemy.orm import Session
import models, schemas
import security
import random

# 1. Yeh function naya booking database mein add karega
def create_booking(db: Session, booking: schemas.BookingCreate):
    # 4 digit ka random OTP generate karna (1000 se 9999 ke beech)
    otp = str(random.randint(1000, 9999))

    # Naya data tayar karna
    db_booking = models.Booking(
        **booking.dict(), 
        status="Pending", 
        completion_otp=otp
    )

    db.add(db_booking)      # Data ko add karo
    db.commit()             # Changes ko permanently save karo
    db.refresh(db_booking)  # Nayi aayi hui ID ke sath data wapas lao
    return db_booking


# 2. Saari bookings nikalne ka function
def get_bookings(db: Session, skip: int = 0, limit: int = 100):
    # Saari bookings ko latest se purani ki taraf sort karke laana
    return db.query(models.Booking).order_by(models.Booking.id.desc()).offset(skip).limit(limit).all()


# 3. Yeh function check karega ki is username se koi technician pehle se toh nahi hai
def get_technician_by_username(db: Session, username: str):
    # Yeh sahi table (models.User) mein technician ko dhoondhega
    return db.query(models.User).filter(models.User.username == username, models.User.role == "technician").first()


# 4. Yeh function naya technician database mein save karega
def create_technician(db: Session, technician: schemas.TechnicianCreate):
    # Sabse pehle user ke password ko lock (encrypt) karna
    hashed_password = security.get_password_hash(technician.password)

    # Nayi row banana (plain password ki jagah encrypted password dalna)
    db_technician = models.Technician(
        name=technician.name,
        username=technician.username,
        hashed_password=hashed_password
    )

    # Database mein add aur save karna
    db.add(db_technician)
    db.commit()
    db.refresh(db_technician)
    return db_technician