from pydantic import BaseModel

# Yeh class check karegi ki React se jo data aa raha hai, wo sahi format mein hai ya nahi
class BookingCreate(BaseModel):
    customer_name: str
    phone_number: str
    service_type: str
    address: str

    # schemas.py mein naya code add karein

class Booking(BookingCreate):
    id: int
    status: str

    class Config:
        from_attributes = True

        # schemas.py mein sabse niche add karein

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

class Booking(BookingCreate):
    id: int
    status: str
    completion_otp: str | None = None  # Nayi line: Frontend ko OTP bhejne ke liye
    assigned_technician: str | None = None
    final_amount: int | None = None

    class Config:
        from_attributes = True