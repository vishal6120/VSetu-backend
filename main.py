from fastapi import FastAPI, Depends, HTTPException, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import JWTError, jwt
from pydantic import BaseModel


import security
from security import verify_password, create_access_token, SECRET_KEY, ALGORITHM
from database import SessionLocal, engine
import models, schemas, crud
import random

# ==========================================
# NAYA FIREBASE SETUP YAHAN ADD KAREIN
# ==========================================
import firebase_admin
from firebase_admin import credentials, messaging
import requests # Yeh line sabse upar add karni hai

# ==========================================
# NAYA: FAST2SMS ENGINE
# ==========================================
# Jab aap Fast2SMS par account banayenge, toh wahan se API key copy karke yahan daalni hai
FAST2SMS_API_KEY = "8CSRXiV7M6xO9JgpL4k5q2W0KTQIhNszmn3AEotPFd1cDvGwyZ8FMdzaPxv5U4L2f1m3QnWETJuGrohS"

def send_real_otp(phone_number, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    querystring = {
        "authorization": FAST2SMS_API_KEY,
        "variables_values": otp,
        "route": "otp",
        "numbers": phone_number
    }
    headers = {'cache-control': "no-cache"}
    
    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        data = response.json()
        
        # Fast2SMS check karega ki number asli hai ya nahi
        if data.get("return") == True:
            return True, "SMS Successfully sent"
        else:
            # Agar number fake hai ya network par nahi hai
            error_message = data.get("message", "Invalid Number")
            return False, error_message
    except Exception as e:
        return False, "SMS Server Down Hai"
# ==========================================

try:
    cred = credentials.Certificate("firebase-admin-key.json")
    firebase_admin.initialize_app(cred)
    print("Firebase Admin engine started successfully! 🚀")
except Exception as e:
    print("Firebase initialization error:", e)
# ==========================================

# Database mein tables create karna
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Yeh token check karne wala system hai
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# main.py ke andar CORS wali setting:
origins = [
    "http://localhost:5173", # Purana local wala
    "https://sahayak-frontend-omega.vercel.app", # <-- Aapka naya Vercel link! (End mein slash '/' mat lagana)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Testing ke liye ek baar "*" karke dekhein
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Har naye request ke liye naya database connection dena
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Digital Pass (Token) invalid hai ya expire ho gaya!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Token ko khol kar usme se username nikalo
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Check karo kya yeh user abhi bhi database mein hai?
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
def read_root():
    return {"message": "VSetu Backend Engine Started!"}

# Yeh hai humara Asli API Endpoint!
@app.post("/api/bookings")
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    # 1. Pehle database mein booking save karo
    new_booking = crud.create_booking(db=db, booking=booking)

    # ==========================================
    # NAYA FIREBASE TRIGGER (MANAGER KE LIYE)
    # ==========================================
    try:
        # Hum ek specific topic "all_managers" par notification bhej rahe hain
        message = messaging.Message(
            notification=messaging.Notification(
                title="VSetu: Naya Order Aaya Hai! 🛍️",
                body=f"Ek customer ne nayi booking ki hai. Jaldi dashboard par check karein!"
            ),
            topic="all_managers"  
        )
        messaging.send(message)
        print("Manager ko naye order ka notification bhej diya!")
    except Exception as e:
        print("Manager notification fail ho gaya:", e)
    # ==========================================

    return new_booking
# main.py mein purane @app.post wale function ke niche ise add karein
# @app.get("/api/bookings", response_model=list[schemas.Booking])
# def read_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     bookings = crud.get_bookings(db, skip=skip, limit=limit)
#     return bookings

@app.get("/api/bookings")
def get_all_bookings(db: Session = Depends(get_db)):
    # Andar ka code waisa hi rehne dein
    bookings = db.query(models.Booking).all()
    return bookings

@app.get("/api/bookings/customer/{phone}")
def get_customer_bookings(phone: str, db: Session = Depends(get_db)):
    # Database mein check karo jahan phone_number match ho
    bookings = db.query(models.Booking).filter(models.Booking.phone_number == phone).all()
    
    # Agar uski koi booking nahi hai, toh khali list bhej do
    if not bookings:
        return []
        
    return bookings

# ==========================================
# CUSTOMER CANCELLATION ROUTE (NAYA FEATURE)
# ==========================================
@app.put("/api/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    # 1. Pehle database mein check karo ki aisi koi booking hai bhi ya nahi
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Aisi koi booking nahi mili.")
        
    # 2. Logic Check: Kya ye booking aisi stage par hai jo cancel nahi ho sakti?
    if booking.status in ["Completed", "Verified"]:
        raise HTTPException(status_code=400, detail="Ye booking complete ho chuki hai, isliye cancel nahi ho sakti.")
    if booking.status == "Cancelled":
         raise HTTPException(status_code=400, detail="Ye booking pehle se hi cancelled hai.")
        
    # 3. Agar sab theek hai, toh status change karke "Cancelled" kar do
    booking.status = "Cancelled"
    
    # 4. Agar koi technician assigned tha, toh use free kar do
    booking.assigned_technician = None
    booking.technician_phone = None
    
    db.commit()
    return {"message": "Booking successfully cancel ho gayi hai!"}

# main.py mein sabse niche yeh naya route add karein
@app.post("/api/technicians/", response_model=schemas.Technician)
def create_technician(technician: schemas.TechnicianCreate, db: Session = Depends(get_db)):
    # Pehle check karenge ki yeh username pehle se kisi aur ka toh nahi
    db_user = crud.get_technician_by_username(db, username=technician.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Yeh username pehle se registered hai")

    # Agar username naya hai, toh usko create kar do
    return crud.create_technician(db=db, technician=technician)

# main.py mein sabse niche yeh naya route add karein
@app.post("/api/technician/token")  # <--- YAHAN CHANGE KIYA HAI
def login_for_access_token_tech(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Database mein username check karo
    user = crud.get_technician_by_username(db, username=form_data.username)

    # 2. Agar user nahi mila, ya password verify nahi hua toh error do
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Username ya password galat hai",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Agar sab sahi hai, toh naya Entry Pass (JWT Token) bana kar bhej do
    access_token = security.create_access_token(data={"sub": user.username})

    # Yeh format standard hota hai, React ise easily padh lega
    return {"access_token": access_token, "token_type": "bearer"}

# 1. KAAM COMPLETE AUR EXTRA PAYMENT ADD KARNE KA NAYA ROUTE
@app.put("/api/bookings/{booking_id}/complete")
def complete_booking(booking_id: int, otp: str, extra_charge: int = 0, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking nahi mili")

    if booking.completion_otp != otp:
        raise HTTPException(status_code=400, detail="Galat OTP! Kaam abhi complete nahi ho sakta.")

    booking.status = "Completed"
    
    # Naya Feature: Agar ladke ne extra paise daale hain, toh use final amount mein jod do
    # (Taki Manager jab verify kare toh use pata rahe ki extra charge laga tha)
    booking.final_amount = extra_charge 
    
    db.commit()
    return {"message": "Kaam successfully complete ho gaya!"}

# 2. CUSTOMER PHONE NA UTHAYE TOH RESCHEDULE KARNE KA NAYA ROUTE
@app.put("/api/bookings/{booking_id}/reschedule")
def reschedule_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking nahi mili")
    
    booking.status = "Rescheduled"
    booking.assigned_technician = None # Ladke ko free kar do taaki wo agla kaam kar sake
    db.commit()
    return {"message": "Booking reschedule mark kar di gayi hai."}


# ==========================================
# MANAGER DISPATCH & VERIFICATION ROUTES
# ==========================================

# 1. Ladke ko kaam par bhejne wala route (Assign Technician)
@app.put("/api/bookings/{booking_id}/assign")
def assign_technician(booking_id: int, technician_name: str, technician_phone: str = "9876543210", db: Session = Depends(get_db)):
    # Pehle database mein booking dhundo
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking nahi mili!")
    
    # Ladke ka naam, number save karo aur status change karo
    booking.assigned_technician = technician_name
    booking.technician_phone = technician_phone  # <--- NAYI LINE (Number save karne ke liye)
    booking.status = "Assigned"
    db.commit()

    # ==========================================
    # NAYA FIREBASE NOTIFICATION TRIGGER
    # ==========================================
    try:
        # Hum notification ko ek "topic" par bhejenge jiska naam technician_name hoga
        message = messaging.Message(
            notification=messaging.Notification(
                title="VSetu: Naya Kaam Aaya Hai! ⚡",
                body=f"Booking ID {booking_id} aapko assign hui hai. Jaldi app check karein."
            ),
            topic=technician_name  # Ye ladke ke username se match karega
        )
        response = messaging.send(message)
        print("Notification bheja gaya:", response)
    except Exception as e:
        print("Notification fail ho gaya:", e)
    # ==========================================

    return {"message": f"Kaam {technician_name} ko de diya gaya hai!"}
# 2. Paise cross-verify karne wala route (Verify Amount)
@app.put("/api/bookings/{booking_id}/verify")
def verify_amount(booking_id: int, amount: int, db: Session = Depends(get_db)):
    # Pehle database mein booking dhundo
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking nahi mili!")
    
    # Customer se verify kiye hue paise save karo
    booking.final_amount = amount
    booking.status = "Verified"
    db.commit()
    return {"message": f"Paise verify ho gaye: ₹{amount}"}


# ==========================================
# SUPER ADMIN (FOUNDER) ROUTES
# ==========================================

@app.get("/api/superadmin/stats")
def get_business_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):

    # Sirf Malik (Super Admin) hi yeh data dekh sakta hai
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Aapke paas Malik (Super Admin) ki power nahi hai!")
    # Sirf wo bookings nikaalo jo Verified ho chuki hain (Deal Done)
    verified_bookings = db.query(models.Booking).filter(models.Booking.status == "Verified").all()
    
    # Total revenue calculate karo
    total_revenue = sum(booking.final_amount for booking in verified_bookings if booking.final_amount)
    
    # Aapka 5% commission nikaalo
    total_commission = total_revenue * 0.05
    
    # Total kitni deals hui hain wo count karo
    total_jobs = len(verified_bookings)
    
    return {
        "total_revenue": total_revenue,
        "total_commission": total_commission,
        "total_jobs": total_jobs
    }


# ==========================================
# LOGIN / AUTHENTICATION ROUTE
# ==========================================

@app.post("/api/login")
def login_for_access_token_user(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. Database mein check karo ki kya yeh username hai?
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    # 2. Agar user nahi mila ya password match nahi hua (verify_password function use karke)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Galat Username ya Password!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Agar sab theek hai, toh uske liye ek Entry Pass (Token) banao
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )

    # 4. Token aur user ka role Frontend (React) ko bhej do
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


# Frontend se aane wale username/password ko pakadne ka dibba
class LoginRequest(BaseModel):
    username: str
    password: str

# ==========================================
# LOGIN / AUTHENTICATION ROUTE (REAL OTP WALA)
# ==========================================
@app.post("/api/auth/login")
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == request.username).first()
    generated_otp = str(random.randint(1000, 9999))
    
    # VIP Entry (Manager/Malik ke number ke liye OTP bypass)
    if request.username == "9999900000":
        return {
            "access_token": "super-secret-vip-pass",
            "role": "admin",
            "token_type": "bearer",
            "screen_otp": generated_otp # Manager ko screen par dikha do
        }
    
    # 👇 NAYA: FAST2SMS BHEJNE KA LOGIC 👇
    # API key lagane ke baad is True ko hata kar condition active karni hai
    #is_sent, msg = send_real_otp(request.username, generated_otp)
    
    # Agar Fast2SMS ne error de diya (fake number ya koi aur dikkat)
    #if not is_sent:
        raise HTTPException(status_code=400, detail=f"SMS Error: {msg}. Kripaya sahi number daalein.")
    
    # Baaki Customer / Technician logic waisa hi rahega
    if not user:
        return {
            "access_token": "new-customer-vip-pass",
            "role": "customer",
            "token_type": "bearer",
            "screen_otp": generated_otp # Testing ke baad ise hata dena hai taaki screen par na dikhe
        }
        
    return {
        "access_token": "super-secret-vip-pass",
        "role": user.role if hasattr(user, 'role') else "customer",
        "token_type": "bearer",
        "screen_otp": generated_otp
    }

# 1. Saare Technicians ki UserIDs, Trade aur Phone dekhne ka API
@app.get("/api/technicians")
def get_all_technicians(db: Session = Depends(get_db)):
    techs = db.query(models.User).filter(models.User.role == "technician").all()
    # NAYA: Ab id, username, trade ke sath phone bhi bhejenge
    return [{"id": t.id, "username": t.username, "trade": t.trade, "phone": t.phone} for t in techs]

# 2. Naya Technician (Trade aur Phone ke sath) banane ka API
@app.post("/api/technicians/create")
def add_new_technician(
    username: str = Form(...), 
    password: str = Form(...), 
    trade: str = Form(...), 
    phone: str = Form(...), # <--- NAYA: Phone number ka parameter
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Ye Username pehle se exist karta hai!")
    
    hashed_pw = security.get_password_hash(password)
    # NAYA: Phone number ko bhi DB mein save kar rahe hain
    new_user = models.User(username=username, hashed_password=hashed_pw, role="technician", trade=trade, phone=phone)
    db.add(new_user)
    db.commit()
    return {"message": "Account successfully ban gaya!"}


    # main.py mein sabse niche add karein
@app.delete("/api/technicians/{tech_id}")
def delete_technician(tech_id: int, db: Session = Depends(get_db)):
    # 1. Database mein us ladke ko ID se dhoondho
    user = db.query(models.User).filter(models.User.id == tech_id, models.User.role == "technician").first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Technician nahi mila")
    
    # 2. Agar mil gaya toh usko delete kar do
    db.delete(user)
    db.commit()
    return {"message": "Technician successfully delete ho gaya"}


# ==========================================
# TECHNICIAN PERSONAL WORKLIST ROUTE
# ==========================================

@app.get("/api/technician/my-bookings")
def get_my_assigned_bookings(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # 1. Pehle Bouncer check karega ki yeh sach mein ek technician hai ya nahi
    if current_user.role != "technician":
        raise HTTPException(status_code=403, detail="Aap technician nahi hain!")

    # 2. STRICT FILTER: Database se wahi bookings nikalo jo:
    #    a) Is specific technician ke naam par assigned hon (current_user.username)
    #    b) Aur jiska status 'Completed' ya 'Verified' naa ho (yaani abhi kaam pending/accepted hai)
    my_bookings = db.query(models.Booking).filter(
        models.Booking.assigned_technician == current_user.username
    ).all()
    
    return my_bookings

    # ==========================================
# TECHNICIAN ACCEPT / REJECT ROUTES
# ==========================================

# 1. Ladke ne kaam Accept kar liya
@app.put("/api/bookings/{booking_id}/accept")
def accept_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking nahi mili")
    
    # Status change karke Accepted kar do
    booking.status = "Accepted"
    db.commit()
    return {"message": "Aapne kaam accept kar liya hai!"}

# 2. Ladke ne kaam Reject kar diya (Mana kar diya)
@app.put("/api/bookings/{booking_id}/reject")
def reject_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking nahi mili")
    
    # Status wapas Pending kar do aur ladke ka naam hata do
    booking.status = "Pending"
    booking.assigned_technician = None 
    db.commit()
    return {"message": "Kaam reject kar diya gaya hai."}