import bcrypt

# Yeh function plain password ko hash (encrypt) karega
def get_password_hash(password: str):
    # 1. Password ko normal text se 'bytes' mein badalna zaroori hai
    pwd_bytes = password.encode('utf-8')

    # 2. Salt (random characters) generate karna taaki har password unique tarike se lock ho
    salt = bcrypt.gensalt()

    # 3. Password aur salt ko mix karke hash banana
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)

    # 4. Wapas string mein badal kar return karna taaki database mein save ho sake
    return hashed_password.decode('utf-8')

# Yeh function check karega ki login karte waqt dala gaya password sahi hai ya nahi
def verify_password(plain_password: str, hashed_password: str):
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')

    return bcrypt.checkpw(password_byte_enc, hashed_password_bytes)


import os
from datetime import datetime, timedelta
from jose import jwt

# Yeh aapke JWT tokens ka 'Secret Lock' hai (asli project mein isko chupakar rakhte hain)
SECRET_KEY = "aapka_super_secret_jugaad_key_12345" 

# Konsa algorithm use karna hai token banane ke liye
ALGORITHM = "HS256"

# Entry pass kitni der tak valid rahega (Abhi ke liye 30 mins)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Yeh function ek naya entry pass (JWT Token) banayega
def create_access_token(data: dict):
    to_encode = data.copy()

    # Expiry time set karna: Aaj ka time + 30 mins
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Secret key se data ko lock (encode) karna aur token banana
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt