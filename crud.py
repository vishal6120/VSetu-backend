from sqlalchemy.orm import Session
import models, schemas
import security
import random

# Yeh function naya booking database mein add karega
def create_booking(db: Session, booking: schemas.BookingCreate):

    # 4 digit ka random OTP generate karna (1000 se 9999 ke beech)
    otp = str(random.randint(1000, 9999))

    db_booking = models.Booking(
        **booking.dict(), 
        status="Pending", 
        completion_otp=otp # OTP save kar do
        
        
    )

    db.add(db_booking)      # Data ko add karo
    db.commit()             # Changes ko permanently save karo
    db.refresh(db_booking)  # Nayi aayi hui ID ke sath data wapas lao
    return db_booking

    # crud.py mein naya function add karein
def get_bookings(db: Session, skip: int = 0, limit: int = 100):
    # Saari bookings ko latest se purani ki taraf sort karke laana
    return db.query(models.Booking).order_by(models.Booking.id.desc()).offset(skip).limit(limit).all()


# crud.py mein sabse niche add karein

# 1. Yeh function check karega ki is username se koi technician pehle se toh nahi hai
def get_technician_by_username(db: Session, username: str):
    return db.query(models.Technician).filter(models.Technician.username == username).first()

# 2. Yeh function naya technician database mein save karega
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