from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database se connect hone ka URL (User: sahayak, Pass: sahayak123, DB: sahayak_db)
SQLALCHEMY_DATABASE_URL = "postgresql://sahayak:sahayak123@localhost/sahayak_db"

# Engine database ke sath connection banata hai
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SessionLocal database mein data dalne aur nikalne ka rasta hai
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class jiske upar hum apne saare tables (models) banayenge
Base = declarative_base()