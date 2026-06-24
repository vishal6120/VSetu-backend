from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base

# (Agar upar Base = declarative_base() likha hai toh use waise hi rehne dein)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  
    trade = Column(String, nullable=True) 
    phone = Column(String, nullable=True) # <--- NAYI LINE YAHAN JODI HAI # <--- NAYI LINE YAHAN JODEIN

class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    username = Column(String, unique=True, index=True) 
    hashed_password = Column(String) 
    is_active = Column(Integer, default=1) 

# Dono ko mila kar banayi gayi ekdum sahi Booking Class
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    phone_number = Column(String, index=True)
    address = Column(Text) 
    service_name = Column(String) 
    status = Column(String, default="Pending") 
    booking_date = Column(String, nullable=True)
    booking_time = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) 
    
    # Manager aur Technician system ke liye advance columns
    completion_otp = Column(String, nullable=True) 
    assigned_technician = Column(String, nullable=True) 
    technician_phone = Column(String, nullable=True) # <--- NAYI LINE YAHAN JODI HAI
    final_amount = Column(Integer, nullable=True)