import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ NAYA LOGIC: Cloud DB Environment Variable Check
# What we do: Hum os.getenv ka use karke Render ke DATABASE_URL ko read kar rahe hain.
# Why we do it: Taaki jab ye cloud par chale toh automatically Render ke Postgres database se jud jaye, aur jab aap laptop par chalao toh local sahayak.db se chalta rahe.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sahayak.db")

# ⚠️ CRITICAL FIX: Protocol String Replacement
# What we do: Agar URL 'postgres://' se shuru ho raha hai, toh hum use 'postgresql://' se replace kar rahe hain.
# Why we do it: Render hamesha database URL 'postgres://' se shuru karke deta hai, lekin naya SQLAlchemy standard use invalid maanta hai aur crash ho jata hai. 'postgresql://' karne se crash nahi hoga.
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ✅ SMART ENGINE CONFIGURATION
# What we do: Agar database SQLite hai toh 'check_same_thread' arguments jodenge, nahi toh normal engine banayenge.
# Why we do it: SQLite ek single-thread DB hai jise multi-threading allow karne ke liye ye argument chahiye hota hai, lekin PostgreSQL par ye argument lagane se error aata hai.
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#https://vsetu-backend.onrender.com
#postgresql://vsetu_db_user:F37lIsOyvhMaFbJA1GYxVh0IiP5o5pod@dpg-d8tmlk77f7vs73factf0-a.virginia-postgres.render.com/vsetu_db