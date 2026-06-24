from pydantic import BaseModel
from typing import Optional

# Yeh class check karegi ki React se jo data aa raha hai, wo sahi format mein hai ya nahi
class BookingCreate(BaseModel):
    customer_name: str
    phone_number: str
    service_name: str  # Yahan service_type ko service_name kar diya (models.py se match karne ke liye)
    address: str
    booking_date: Optional[str] = None
    booking_time: Optional[str] = None

# Jab database wapas data dega, toh yeh format hoga
class Booking(BookingCreate):
    id: int
    status: str
    completion_otp: Optional[str] = None  # Frontend ko OTP bhejne ke liye
    assigned_technician: Optional[str] = None
    final_amount: Optional[int] = None

    class Config:
        from_attributes = True

# Jab API naya technician banayegi, toh yeh data aayega (ismai password hoga)
class TechnicianCreate(BaseModel):
    name: str
    username: str
    password: str

# Jab database wapas data dega, toh yeh format hoga (ismai password nahi dikhayenge!)
class Technician(BaseModel):
    id: int
    name: str
    username: str
    is_active: int

    class Config:
        from_attributes = True