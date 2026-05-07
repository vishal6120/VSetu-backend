from sqlalchemy import Column, Integer, String, Text
from database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    phone_number = Column(String, index=True)
    service_type = Column(String)
    address = Column(Text)
    status = Column(String, default="Pending") # Default status pending rahega
    completion_otp = Column(String, nullable=True) # Yahan hum 4-digit OTP save karenge
    # Manager Dispatch System ke naye columns
    assigned_technician = Column(String, nullable=True) # Kis ladke ko bheja (e.g., "Raju")
    final_amount = Column(Integer, nullable=True)       # Verify hone ke baad kitne paise mile

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # Isme save hoga ki yeh 'admin', 'technician', ya 'superadmin' hai

class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    username = Column(String, unique=True, index=True) # Login ke liye (jaise: tech_rahul)
    hashed_password = Column(String) # Encrypted password
    is_active = Column(Integer, default=1) # 1 = Active, 0 = Inactive