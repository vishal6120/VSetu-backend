from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from security import verify_password, create_access_token
from fastapi.middleware.cors import CORSMiddleware
import security
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import text
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from security import SECRET_KEY, ALGORITHM

# Apni files import kar rahe hain
from database import SessionLocal, engine
import models, schemas, crud

# Database mein tables create karna
models.Base.metadata.create_all(bind=engine)



app = FastAPI()

# Naya code: Yeh humara security guard hai jisko pata hai ki token kahan se milta hai
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token/")

# main.py ke andar CORS wali setting dhoondhein aur aise update karein:

origins = [
    "http://localhost:5173", # Purana local wala
    "https://sahayak-frontend-omega.vercel.app", # <-- Aapka naya Vercel link! (End mein slash '/' mat lagana)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

        # Yeh token check karne wala system hai
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

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
    return {"message": "Aapka Sahayak Backend Engine Started!"}

# Yeh hai humara Asli API Endpoint!
@app.post("/api/bookings")
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    # Data validate ho kar 'booking' variable mein aayega
    # Phir crud function usko database mein daal dega
    return crud.create_booking(db=db, booking=booking)

# main.py mein purane @app.post wale function ke niche ise add karein

#@app.get("/api/bookings", response_model=list[schemas.Booking])
#def read_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
 #   bookings = crud.get_bookings(db, skip=skip, limit=limit)
  #  return bookings

@app.get("/api/bookings")
def get_all_bookings(db: Session = Depends(get_db)):
    # Andar ka code waisa hi rehne dein
    bookings = db.query(models.Booking).all()
    return bookings

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
@app.post("/api/token/")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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

@app.put("/api/bookings/{booking_id}/complete")
def complete_booking(booking_id: int, otp: str, db: Session = Depends(get_db)):
    # 1. Booking dhoondho
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking nahi mili")

    # 2. OTP match karo
    if booking.completion_otp != otp:
        raise HTTPException(status_code=400, detail="Galat OTP! Kaam abhi complete nahi ho sakta.")

    # 3. Agar OTP sahi hai, toh status update kar do
    booking.status = "Completed"
    db.commit()
    return {"message": "Kaam successfully complete ho gaya!"}


# ==========================================
# MANAGER DISPATCH & VERIFICATION ROUTES
# ==========================================

# 1. Ladke ko kaam par bhejne wala route (Assign Technician)
@app.put("/api/bookings/{booking_id}/assign")
def assign_technician(booking_id: int, technician_name: str, db: Session = Depends(get_db)):
    # Pehle database mein booking dhundo
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking nahi mili!")
    
    # Ladke ka naam save karo aur status change karo
    booking.assigned_technician = technician_name
    booking.status = "Assigned"
    db.commit()
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
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
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